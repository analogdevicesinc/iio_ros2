// Copyright 2025 Analog Devices, Inc.
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

#include "adi_iio/iio_buffer.hpp"
#include "adi_iio/iio_path.hpp"

IIOBuffer::IIOBuffer(std::shared_ptr<IIONode> nh, std::string device_path)
{
  this->m_nh = nh;
  this->m_device_path = device_path;
  m_canceled = false;
  this->m_buffer = nullptr;
#if defined(LIBIIO_V1)
  this->m_mask = nullptr;
  this->m_stream = nullptr;
  this->m_block = nullptr;
  this->m_cyclic = false;
  this->m_started = false;
  this->m_sample_size = 0;
#endif
  this->m_topic_enabled = false;
}

IIOBuffer::~IIOBuffer()
{
  destroyIIOBuffer();

  m_stopThread = true;
  if (m_th.joinable()) {
    m_th.join();
  }
}

bool IIOBuffer::created()
{
#if defined(LIBIIO_V1)
  return m_block != nullptr;
#else
  return m_buffer != nullptr;
#endif
}

void IIOBuffer::destroyIIOBuffer()
{
#if defined(LIBIIO_V1)
  if (m_block) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_canceled = true;
    iio_buffer_stream_cancel(m_stream);
    RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Destroyed buffer %p", (void *)m_buffer);
    iio_block_destroy(m_block);
    m_block = nullptr;
    iio_buffer_close(m_stream);
    m_stream = nullptr;
    iio_channels_mask_destroy(m_mask);
    m_mask = nullptr;
    m_started = false;
    m_buffer = nullptr;
    m_loopRate = nullptr;
  }
#else
  if (m_buffer) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_canceled = true;
    iio_buffer_cancel(m_buffer);
    RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Destroyed buffer %p", (void *)m_buffer);
    iio_buffer_destroy(m_buffer);
    m_buffer = nullptr;
    m_loopRate = nullptr;
  }
#endif
}

bool IIOBuffer::createIIOBuffer(std::string & message, bool output, bool cyclic)
{
  std::lock_guard<std::mutex> lock(m_mutex);
  iio_device * dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  if (dev == nullptr) {
    message = "Device not found";
    RCLCPP_WARN(
      rclcpp::get_logger(
        "rclcpp"), "could not find device \"%s\" - errno %d - %s", m_device_path.c_str(),
      errno, message.c_str());
    return false;
  }

  // verify channel count
  if (m_channels.size() == 0) {
    message = "No channels to read";
    return false;
  }

  if (m_samples_count == 0) {
    message = "No samples to read";
    return false;
  }

  bool direction;
  // validate that all channels exist
  for (auto & channel : m_channels) {
    iio_channel * ch = nullptr;

    if (IIOPath::hasExtendedChannelFormat(channel)) {
      auto [is_output, chn_name] = IIOPath::getExtendedChannelSegment(channel);
      ch = iio_device_find_channel(dev, chn_name.c_str(), is_output);
      direction = is_output;
    } else {
      ch = iio_device_find_channel(dev, channel.c_str(), output);
    }
    if (ch == nullptr) {
      message = strerror(-errno);
      RCLCPP_WARN(
        rclcpp::get_logger(
          "rclcpp"), "could not find channel \"%s\" in device \"%s\" - errno %d - %s",
        channel.c_str(), m_device_path.c_str(), errno, message.c_str());
      return false;
    }
  }

#if defined(LIBIIO_V1)
  m_mask = iio_create_channels_mask(iio_device_get_channels_count(dev));
  if (!m_mask) {
    message = "Could not create channels mask";
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not create channels mask for device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    return false;
  }
#endif

  // disable all channels
  for (unsigned int i = 0; i < iio_device_get_channels_count(dev); i++) {
#if defined(LIBIIO_V1)
    iio_channel_disable(iio_device_get_channel(dev, i), m_mask);
#else
    iio_channel_disable(iio_device_get_channel(dev, i));
#endif
    RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Disabling channel %d", i);
  }

  // enable channels
  for (auto & channel : m_channels) {
    iio_channel * ch = nullptr;

    if (IIOPath::hasExtendedChannelFormat(channel)) {
      auto [is_output, chn_name] = IIOPath::getExtendedChannelSegment(channel);
      ch = iio_device_find_channel(dev, chn_name.c_str(), is_output);
      direction = is_output;
    } else {
      ch = iio_device_find_channel(dev, channel.c_str(), output);
    }
    if (ch == nullptr) {
      message = strerror(-errno);
      RCLCPP_WARN(
        rclcpp::get_logger(
          "rclcpp"), "could not find channel \"%s\" in device \"%s\" - errno %d - %s",
        channel.c_str(), m_device_path.c_str(), errno, message.c_str());
      return false;
    }
#if defined(LIBIIO_V1)
    iio_channel_enable(ch, m_mask);
#else
    iio_channel_enable(ch);
#endif
    RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Enabling channel %s", channel.c_str());
  }

  m_canceled = false;
#if defined(LIBIIO_V1)
  m_cyclic = cyclic;
  m_sample_size = iio_device_get_sample_size(dev, m_mask);
  if (m_sample_size < 0) {
    message = strerror(static_cast<int>(-m_sample_size));
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not get sample size for device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    iio_channels_mask_destroy(m_mask);
    m_mask = nullptr;
    return false;
  }

  m_buffer = iio_device_get_buffer(dev, 0);
  if (!m_buffer) {
    message = strerror(-errno);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not get buffer in device \"%s\" - errno %d - %s",
      m_device_path.c_str(), errno, message.c_str());
    iio_channels_mask_destroy(m_mask);
    m_mask = nullptr;
    return false;
  }

  m_stream = iio_buffer_open(m_buffer, m_mask);
  if (iio_err(m_stream)) {
    message = strerror(-iio_err(m_stream));
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not open buffer stream in device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    m_stream = nullptr;
    m_buffer = nullptr;
    iio_channels_mask_destroy(m_mask);
    m_mask = nullptr;
    return false;
  }

  m_block = iio_buffer_stream_create_block(
    m_stream, static_cast<size_t>(m_sample_size) * m_samples_count);
  if (iio_err(m_block)) {
    message = strerror(-iio_err(m_block));
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not create block in device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    m_block = nullptr;
    iio_buffer_close(m_stream);
    m_stream = nullptr;
    m_buffer = nullptr;
    iio_channels_mask_destroy(m_mask);
    m_mask = nullptr;
    return false;
  }
#else
  m_buffer = iio_device_create_buffer(dev, m_samples_count, cyclic);
  if (m_buffer == nullptr) {
    message = strerror(-errno);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not create buffer in device \"%s\" - errno %d - %s",
      m_device_path.c_str(), errno, message.c_str());
    return false;
  }
#endif

  m_data.layout.dim.clear();
  m_data.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  m_data.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  m_data.layout.dim[0].label = "samples";
  m_data.layout.dim[0].size = m_samples_count;
  m_data.layout.dim[0].stride = m_channels.size() * m_samples_count;
  m_data.layout.dim[1].label = "channels";
  m_data.layout.dim[1].size = m_channels.size();
  m_data.layout.dim[1].stride = m_channels.size();


  RCLCPP_INFO(
    rclcpp::get_logger("adi_iio_node"), "Created buffer %p, direction: %s, cyclic: %s",
    (void *)m_buffer, direction ? "output" : "input", cyclic ? "true" : "false");
  message = "Success";
  return true;
}

bool IIOBuffer::refill(std::string & message)
{
  std::lock_guard<std::mutex> lock(m_mutex);
  iio_device * dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  if (!created() || m_canceled) {
    message = "Buffer not created";
    return false;
  }

#if defined(LIBIIO_V1)
  int ret = iio_block_enqueue(m_block, 0, false);
  if (ret >= 0 && !m_started) {
    ret = iio_buffer_stream_start(m_stream);
    m_started = ret >= 0;
  }
  if (ret >= 0) {
    ret = iio_block_dequeue(m_block, false);
  }
  RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Refilled buffer, ret %d", ret);

  if (ret < 0) {
    message = strerror(-ret);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not refill buffer in device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    return false;
  }
#else
  ssize_t size = iio_buffer_refill(m_buffer);
  RCLCPP_DEBUG(rclcpp::get_logger("adi_iio_node"), "Refilled buffer with %ld bytes from HW", size);

  if (size < 0) {
    message = strerror(-errno);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not refill buffer in device \"%s\" - errno %d - %s",
      m_device_path.c_str(), errno, message.c_str());
    return false;
  }
#endif

  m_data.data.clear();
  for (int i = 0; i < m_samples_count; i++) {
    for (const auto & channel : m_channels) {
      iio_channel * ch = nullptr;
      if (IIOPath::hasExtendedChannelFormat(channel)) {
        auto [is_output, chn_name] = IIOPath::getExtendedChannelSegment(channel);
        ch = iio_device_find_channel(dev, chn_name.c_str(), is_output);
        if (is_output) {
          RCLCPP_ERROR(
            rclcpp::get_logger("adi_iio_node"),
            "Refill only works for input channels");
          return false;
        }
      } else {
        ch = iio_device_find_channel(dev, channel.c_str(), false);
      }

#if defined(LIBIIO_V1)
      uint8_t * base_ptr = reinterpret_cast<uint8_t *>(iio_block_first(m_block, ch));
      size_t step = static_cast<size_t>(m_sample_size);
#else
      uint8_t * base_ptr = reinterpret_cast<uint8_t *>(iio_buffer_first(m_buffer, ch));
      size_t step = iio_buffer_step(m_buffer);  // Should be in bytes
#endif
      uint8_t * sample = base_ptr + (step * i);

      int32_t val = 0;
      iio_channel_convert(ch, &val, sample);
      const iio_data_format * fmt = iio_channel_get_data_format(ch);
      // val = val & ((1<<fmt->bits) - 1);
      if (val & (1 << (fmt->bits))) {  // sign extension
        val = val | (~((1 << fmt->bits) - 1));
      }
      m_data.data.push_back(val);
    }
  }
  message = "Success";
  return true;
}

bool IIOBuffer::push(std::string & message, std_msgs::msg::Int32MultiArray & data)
{
  std::lock_guard<std::mutex> lock(m_mutex);
  iio_device * dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  iio_channel * ch = nullptr;

  if (!created()) {
    message = "Buffer not created";
    return false;
  }

  // get data from multiarray and add it to a memory "arena"
  for (int i = 0; i < m_samples_count; i++) {
    for (size_t j = 0; j < m_channels.size(); j++) {
      auto channel = m_channels[j];

      if (IIOPath::hasExtendedChannelFormat(channel)) {
        auto [is_output, chn_name] = IIOPath::getExtendedChannelSegment(channel);
        ch = iio_device_find_channel(dev, chn_name.c_str(), is_output);
        if (!is_output) {
          RCLCPP_ERROR(
            rclcpp::get_logger("adi_iio_node"),
            "Push only works for input channels");
          return false;
        }
      } else {
        ch = iio_device_find_channel(dev, channel.c_str(), true);
      }

#if defined(LIBIIO_V1)
      uint8_t * base_ptr = reinterpret_cast<uint8_t *>(iio_block_first(m_block, ch));
      size_t step = static_cast<size_t>(m_sample_size) * i;
#else
      uint8_t * base_ptr = reinterpret_cast<uint8_t *>(iio_buffer_first(m_buffer, ch));
      size_t step = iio_buffer_step(m_buffer) * i;
#endif
      uint8_t * sample = base_ptr + step;

      int32_t val = data.data[i * m_channels.size() + j];
      iio_channel_convert_inverse(ch, sample, &val);
    }
  }

#if defined(LIBIIO_V1)
  int ret = iio_block_enqueue(
    m_block, static_cast<size_t>(m_sample_size) * m_samples_count, m_cyclic);
  if (ret >= 0 && !m_started) {
    ret = iio_buffer_stream_start(m_stream);
    m_started = ret >= 0;
  }
  if (ret >= 0) {
    ret = iio_block_dequeue(m_block, false);
  }
  if (ret < 0) {
    message = strerror(-ret);
    RCLCPP_WARN(
      rclcpp::get_logger(
        "adi_iio_node"), "could not push buffer in device \"%s\" - %s",
      m_device_path.c_str(), message.c_str());
    return false;
  }
#else
  iio_buffer_push(m_buffer);
#endif
  message = "Success";
  return true;
}


void IIOBuffer::enableTopic(std::string topic_name, double loopRate)
{
  m_topic_enabled = true;
  m_stopThread = false;
  m_loopRate = std::make_shared<rclcpp::Rate>(loopRate);

  if (topic_name == "") {
    m_topic_name = IIOPath::toTopicName(m_device_path);
  } else {
    m_topic_name = IIOPath::toTopicName(topic_name);
  }


  m_pub = m_nh->create_publisher<std_msgs::msg::Int32MultiArray>(
    m_topic_name + BUFFER_READ_SUFFIX,
    BUFFER_QOS_QUEUE_SIZE);
  m_th = std::thread(&IIOBuffer::publishingLoop, this);
}
// create topic
// create thread that refills
// update publishes to topic
// move Int32MultiArray to class - and unlock mutex to get data in refill service

void IIOBuffer::publishingLoop()
{
  while (rclcpp::ok() && !m_stopThread) {
    std::string msg;
    std_msgs::msg::Int32MultiArray buffer;
    if (refill(msg)) {
      m_pub->publish(m_data);
    }
    // Sleep to maintain the loop rate
    RCLCPP_DEBUG(
      rclcpp::get_logger("adi_iio_node"), "Publishing loop %s", m_topic_name.c_str());
    m_loopRate->sleep();
  }
}

void IIOBuffer::disableTopic()
{
  m_topic_enabled = false;
  m_stopThread = true;

  if (m_th.joinable()) {
    m_th.join();  // stop thread
  }
  m_pub.reset();  // destroy topic
  RCLCPP_INFO(rclcpp::get_logger("adi_iio_node"), "Disabled IIOBuffer topic");
}
