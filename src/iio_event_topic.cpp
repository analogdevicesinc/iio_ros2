// Copyright 2026 Analog Devices, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#if defined(LIBIIO_V1)

#include <cstring>
#include <utility>

#include "adi_iio/iio_event_topic.hpp"
#include "adi_iio/iio_path.hpp"

IIOEventTopic::IIOEventTopic(std::shared_ptr<IIONode> nh, std::string device_path)
: m_nh(std::move(nh)), m_device_path(std::move(device_path))
{}

IIOEventTopic::~IIOEventTopic()
{
  disableTopic();
}

bool IIOEventTopic::enableTopic(std::string & message, const std::string & topic_name)
{
  std::lock_guard<std::mutex> lock(m_mutex);

  m_dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  if (m_dev == nullptr) {
    message = "Device not found";
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not find device \"%s\" - errno %d",
      m_device_path.c_str(), errno);
    return false;
  }

  int err = EventStreamHandle::create(m_dev, m_stream);
  if (err) {
    message = strerror(-err);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not create event stream for device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    return false;
  }

  if (topic_name.empty()) {
    m_topic_name = IIOPath::toTopicName(m_device_path);
  } else {
    m_topic_name = IIOPath::toTopicName(topic_name);
  }

  m_pub = m_nh->create_publisher<adi_iio::msg::IIOEvent>(
    m_topic_name, EVENT_QOS_QUEUE_SIZE);

  m_stopThread = false;
  m_topic_enabled = true;
  m_th = std::thread(&IIOEventTopic::readLoop, this);

  RCLCPP_INFO(
    rclcpp::get_logger("adi_iio_node"), "Enabled IIOEventTopic for device \"%s\" on topic \"%s\"",
    m_device_path.c_str(), m_topic_name.c_str());
  message = "Success";
  return true;
}

void IIOEventTopic::readLoop()
{
  while (rclcpp::ok() && !m_stopThread) {
    struct iio_event ev;
    int ret = m_stream.read(ev, false);

    // underlying stream was destroyed
    if (ret == -EINTR) {
      break;
    }

    if (ret < 0) {
      RCLCPP_WARN(
        rclcpp::get_logger(
          "adi_iio_node"), "event stream read failed for device \"%s\" - %s",
        m_device_path.c_str(), strerror(-ret));
      m_topic_enabled = false;
      break;
    }

    m_pub->publish(decode(EventView(ev)));
  }
}

adi_iio::msg::IIOEvent IIOEventTopic::decode(const EventView & ev) const
{
  adi_iio::msg::IIOEvent msg;

  msg.header.stamp = m_nh->now();
  msg.header.frame_id = m_device_path;

  msg.id = ev.id;
  msg.hw_timestamp = ev.timestamp;

  msg.type = static_cast<int8_t>(ev.type());
  msg.type_name = ev.type_name();

  msg.direction = static_cast<int8_t>(ev.direction());
  msg.direction_name = ev.direction_name();

  const iio_channel * chn = ev.channel(m_dev, false);
  msg.channel = chn ? iio_channel_get_id(chn) : "";

  const iio_channel * diff_chn = ev.channel(m_dev, true);
  msg.diff_channel = diff_chn ? iio_channel_get_id(diff_chn) : "";

  return msg;
}

void IIOEventTopic::disableTopic()
{
  std::lock_guard<std::mutex> lock(m_mutex);

  m_stopThread = true;
  m_stream.reset();

  if (m_th.joinable()) {
    m_th.join();
  }

  m_pub.reset();
  m_topic_enabled = false;

  RCLCPP_INFO(
    rclcpp::get_logger("adi_iio_node"), "Disabled IIOEventTopic for device \"%s\"",
    m_device_path.c_str());
}

#endif  // LIBIIO_V1
