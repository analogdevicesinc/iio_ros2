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

#include "adi_iio/iio_node.hpp"
#include "adi_iio/iio_path.hpp"
#include "adi_iio/iio_attr_topic.hpp"
#include "adi_iio/iio_buffer.hpp"
#include <memory>

using namespace std::chrono_literals;

#define MAX_ATTR_SIZE 4095
/*
BufferTopic.srv

string buffer_path
int buffer_size
bool enable
---
bool success
string message


parameter
----
"URI"

*/

IIONode::IIONode()
: Node("adi_iio_node")
{
  m_initialized = false;
  this->declare_parameter<std::string>("uri", "local:");
  m_uri = this->get_parameter("uri").as_string();

  m_ctx = iio_create_context_from_uri(m_uri.c_str());

  if (m_ctx != nullptr) {
    RCLCPP_INFO(
      rclcpp::get_logger(
        "rclcpp"), "creating context %p from uri %s", (void *)m_ctx, m_uri.c_str());
    m_initialized = true;
  } else {
    RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "cannot create context from uri %s", m_uri.c_str());
  }
}

void IIONode::initBuffers()
{
  for (unsigned int i = 0; i < iio_context_get_devices_count(m_ctx); i++) {
    iio_device * dev = iio_context_get_device(m_ctx, i);
    std::string dev_name = iio_device_get_name(dev);
    for (unsigned int j = 0; j < iio_device_get_channels_count(dev); j++) {
      iio_channel * ch = iio_device_get_channel(dev, j);
      if (!iio_channel_is_output(ch) && iio_channel_is_scan_element(ch)) {
        m_bufferMap.insert(
          {dev_name, std::make_shared<IIOBuffer>(
              std::dynamic_pointer_cast<IIONode>(shared_from_this()), dev_name)});
        break;
      }
    }
  }
}

IIONode::~IIONode()
{
}

bool IIONode::initialized()
{
  return m_initialized;
}

std::string IIONode::convertAttrPathToTopicName(std::string path)
{
  std::replace(path.begin(), path.end(), '-', '_');
  return path;
}

bool IIONode::rwAttrPath(std::string path, std::string & result, bool write, std::string value)
{
  bool ret = false;
  std::string str = path;
  std::stringstream ss(str);
  std::string segment;
  std::vector<std::string> segments;

  iio_device * dev = nullptr;
  iio_channel * ch = nullptr;

  while (std::getline(ss, segment, '/')) {
    segments.push_back(segment);  // Push each part of the string into the vector
  }

  char * val;
  char attr_val[MAX_ATTR_SIZE];
  int ret1;
  switch (segments.size()) {
    case 1:  // context_attribute
      val = const_cast<char *>(iio_context_get_attr_value(m_ctx, segments[0].c_str()));
      if (val) {
        ret = true;
        result = val;
        RCLCPP_INFO(
          rclcpp::get_logger("rclcpp"), "read context attribute \"%s\" with value \"%s\"",
          segments[0].c_str(), val);
      } else {
        ret = false;
        result = "";
        RCLCPP_WARN(
          rclcpp::get_logger(
            "rclcpp"), "could not find context attribute \"%s\"", segments[0].c_str());
      }

      if (write) {
        ret = false;
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "context attributes cannot be written");
      }
      break;

    case 2:  // device_attribute
      dev = iio_context_find_device(m_ctx, segments[0].c_str());
      if (!dev) {
        RCLCPP_WARN(
          rclcpp::get_logger("rclcpp"), "could not find device \"%s\"",
          segments[0].c_str());
        break;
      }
      if (write) {
        ret1 = iio_device_attr_write(dev, segments[1].c_str(), value.c_str());
        if (ret1 > 0) {
          RCLCPP_INFO(
            rclcpp::get_logger("rclcpp"),
            "wrote device attribute \"%s\" from device \"%s\" with value \"%s\"",
            segments[1].c_str(),
            segments[0].c_str(), value.c_str());
        } else {
          result = strerror(-ret1);
          ret = false;
          RCLCPP_WARN(
            rclcpp::get_logger("rclcpp"),
            "could not write attribute \"%s\" in device \"%s\" with value \"%s\" - errno %d - %s",
            segments[1].c_str(), segments[0].c_str(), value.c_str(), ret1, result.c_str());
          break;
        }
      }

      ret1 = iio_device_attr_read(dev, segments[1].c_str(), attr_val, MAX_ATTR_SIZE);
      if (ret1 > 0) {
        result = attr_val;
        ret = true;
        RCLCPP_INFO(
          rclcpp::get_logger(
            "rclcpp"), "read device attribute \"%s\" from device \"%s\" with value \"%s\"",
          segments[1].c_str(), segments[0].c_str(), attr_val);
      } else {
        result = strerror(-ret1);
        ret = false;
        RCLCPP_WARN(
          rclcpp::get_logger(
            "rclcpp"), "could not read attribute \"%s\" in device \"%s\" - errno %d - %s",
          segments[1].c_str(), segments[0].c_str(), ret1, result.c_str());
      }
      break;

    case 3:  // channel_attribute
      dev = iio_context_find_device(m_ctx, segments[0].c_str());
      if (!dev) {
        RCLCPP_WARN(
          rclcpp::get_logger("rclcpp"), "could not find device \"%s\"",
          segments[0].c_str());
        break;
      }

      if (segments[1].find("input_") == 0) {
        ch = iio_device_find_channel(dev, segments[1].substr(strlen("input_")).c_str(), false);
      } else if (segments[1].find("output_") == 0) {
        ch = iio_device_find_channel(dev, segments[1].substr(strlen("output_")).c_str(), true);
      } else {
        ch = iio_device_find_channel(dev, segments[1].c_str(), false);
        if (!ch) {
          ch = iio_device_find_channel(dev, segments[1].c_str(), true);
        }
      }

      if (!ch) {
        RCLCPP_WARN(
          rclcpp::get_logger("rclcpp"), "could not find channel \"%s\"",
          segments[1].c_str());
        break;
      }

      if (write) {
        ret1 = iio_channel_attr_write(ch, segments[2].c_str(), value.c_str());
        if (ret1 > 0) {
          RCLCPP_INFO(
            rclcpp::get_logger("rclcpp"),
            "wrote channel attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"",
            segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), value.c_str());
        } else {
          result = strerror(-ret1);
          ret = false;
          RCLCPP_WARN(
            rclcpp::get_logger(
              "rclcpp"),
            "could not write attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"- errno %d "
            "- %s",
            segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), value.c_str(), ret1,
            result.c_str());
          break;
        }
      }

      ret1 = iio_channel_attr_read(ch, segments[2].c_str(), attr_val, MAX_ATTR_SIZE);
      if (ret1 > 0) {
        result = attr_val;
        ret = true;
        RCLCPP_INFO(
          rclcpp::get_logger("rclcpp"),
          "read channel attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"",
          segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), attr_val);
      } else {
        result = strerror(-ret1);
        ret = false;
        RCLCPP_WARN(
          rclcpp::get_logger("rclcpp"),
          "could not read attribute \"%s\" from channel \"%s\" device \"%s\" - errno %d - %s",
          segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), ret1, result.c_str());
      }

      break;
    default:
      result = "Service requires attr_path";
      ret = false;
      break;
  }

  return ret;
}

void IIONode::attrReadSrv(
  const std::shared_ptr<adi_iio::srv::AttrReadString::Request> request,                          // CHANGE
  std::shared_ptr<adi_iio::srv::AttrReadString::Response> response)
{
  RCLCPP_INFO(
    rclcpp::get_logger(
      "rclcpp"), "Service request read attr: %s", request->attr_path.c_str());
  std::string result;
  response->success = rwAttrPath(request->attr_path, result);
  response->message = result;
}

void IIONode::attrWriteSrv(
  const std::shared_ptr<adi_iio::srv::AttrWriteString::Request> request,                           // CHANGE
  std::shared_ptr<adi_iio::srv::AttrWriteString::Response> response)
{
  RCLCPP_INFO(
    rclcpp::get_logger("rclcpp"), "Service request write attr %s value %s",
    request->attr_path.c_str(),
    request->value.c_str());
  std::string result;
  response->success = rwAttrPath(request->attr_path, result, true, request->value);
  response->message = result;
}

/*AttrTopicEnable.srv
 string topic_name
 string attr_path
 int loop_rate
 int type
 ---------------
 bool success
 string message*/

void IIONode::attrEnableTopicSrv(
  const std::shared_ptr<adi_iio::srv::AttrEnableTopic::Request> request,
  std::shared_ptr<adi_iio::srv::AttrEnableTopic::Response> response)
{
  RCLCPP_INFO(
    rclcpp::get_logger(
      "rclcpp"), "Service request enable topic %s with type %s with loop_rate %d Hz",
    request->attr_path.c_str(), request->attr_path.c_str(), request->loop_rate);

  std::string result;
  response->success = rwAttrPath(request->attr_path, result);
  response->message = result;

  std::string local_topic_name = request->topic_name;
  if (local_topic_name == "") {
    local_topic_name = convertAttrPathToTopicName(request->attr_path);
  }

  if (response->success) {
    if (m_attrTopicMap.find(local_topic_name) != m_attrTopicMap.end()) {
      m_attrTopicMap.erase(local_topic_name);
    }

    m_attrTopicMap.insert(
      {local_topic_name,
        std::make_shared<IIOAttrTopic>(
          std::dynamic_pointer_cast<IIONode>(shared_from_this()), local_topic_name,
          request->attr_path, static_cast<IIOAttrTopic::topicType_t>(request->type),
          request->loop_rate)});

    response->success = true;
    response->message = "Success";
  }
}

/*
AttrTopicDisable.srv
string topic_name
---
bool success
string message
*/

void IIONode::attrDisableTopicSrv(
  const std::shared_ptr<adi_iio::srv::AttrDisableTopic::Request> request,
  std::shared_ptr<adi_iio::srv::AttrDisableTopic::Response> response)
{
  RCLCPP_INFO(
    rclcpp::get_logger(
      "rclcpp"), "Service request disable topic %s ", request->topic_name.c_str());

  std::string local_topic_name = request->topic_name;
  local_topic_name = convertAttrPathToTopicName(request->topic_name);  // for compatibility with enable

  if (m_attrTopicMap.find(local_topic_name) != m_attrTopicMap.end()) {
    m_attrTopicMap.erase(local_topic_name);
    response->success = true;
    response->message = "Success";
  } else {
    response->success = false;
    response->message = "Topic not found";
  }
}

void IIONode::buffRefillSrv(
  const std::shared_ptr<adi_iio::srv::BufferRefill::Request> request,
  std::shared_ptr<adi_iio::srv::BufferRefill::Response> response)
{
  if (m_bufferMap.find(request->device_path) == m_bufferMap.end()) {
    response->success = false;
    response->message = "Buffer not found";
  } else {
    std::string message;
    if (m_bufferMap[request->device_path]->topic_enabled()) {
    } else {
      response->success = m_bufferMap[request->device_path]->refill(message);
      response->message = message;
    }
    response->buffer = m_bufferMap[request->device_path]->data();
  }
}

void IIONode::buffReadSrv(
  const std::shared_ptr<adi_iio::srv::BufferRead::Request> request,
  std::shared_ptr<adi_iio::srv::BufferRead::Response> response)
{
  std::string channels;
  for (auto & channel : request->channels) {
    channels += channel + " ";
  }

  RCLCPP_INFO(
    rclcpp::get_logger("rclcpp"), "Service request buffer read %s - %s - %d samples",
    request->device_path.c_str(), channels.c_str(), request->samples_count);

  std::string message;

  std::shared_ptr<IIOBuffer> buffer;
  if (m_bufferMap.find(request->device_path) == m_bufferMap.end()) {
    response->success = false;
    response->message = "Device or buffer not found";
    return;
  }

  buffer = m_bufferMap[request->device_path];
  buffer->destroyIIOBuffer();
  buffer->set_samples_count(request->samples_count);
  buffer->set_channels(request->channels);

  response->success = buffer->createIIOBuffer(message);
  if (!response->success) {
    response->message = message;
    return;
  }

  response->success = buffer->refill(message);
  response->buffer = buffer->data();
  response->message = message;
}


void IIONode::buffWriteSrv(
  const std::shared_ptr<adi_iio::srv::BufferWrite::Request> request,
  std::shared_ptr<adi_iio::srv::BufferWrite::Response> response)
{
  std::string channels;
  for (auto & channel : request->channels) {
    channels += channel + " ";
  }

  RCLCPP_INFO(
    rclcpp::get_logger("rclcpp"), "Service request buffer read %s - %s - %d samples",
    request->device_path.c_str(), channels.c_str(), request->buffer.layout.dim[0].size);

  std::string message;

  std::shared_ptr<IIOBuffer> buffer;
  if (m_bufferMap.find(request->device_path) == m_bufferMap.end()) {
    response->success = false;
    response->message = "Device or buffer not found";
    return;
  }

  buffer = m_bufferMap[request->device_path];
  buffer->destroyIIOBuffer();
  buffer->set_samples_count(request->buffer.layout.dim[0].size);
  buffer->set_channels(request->channels);

  response->success = buffer->createIIOBuffer(message);
  if (!response->success) {
    response->message = message;
    return;
  }

  response->success = buffer->push(message, request->buffer);
}

void IIONode::buffCreateSrv(
  const std::shared_ptr<adi_iio::srv::BufferCreate::Request> request,
  std::shared_ptr<adi_iio::srv::BufferCreate::Response> response)
{
  std::string channels;
  for (auto & channel : request->channels) {
    channels += channel + " ";
  }

  RCLCPP_INFO(
    rclcpp::get_logger("rclcpp"), "Service request buffer create %s - %s - %d samples",
    request->device_path.c_str(), channels.c_str(), request->samples_count);

  std::string message;

  std::shared_ptr<IIOBuffer> buffer;
  if (m_bufferMap.find(request->device_path) == m_bufferMap.end()) {
    response->success = false;
    response->message = "Buffer not found";
  }

  buffer = m_bufferMap[request->device_path];
  buffer->destroyIIOBuffer();
  buffer->set_samples_count(request->samples_count);
  buffer->set_channels(request->channels);

  response->success = buffer->createIIOBuffer(message);
  response->message = message;
}

void IIONode::buffDestroySrv(
  const std::shared_ptr<adi_iio::srv::BufferDestroy::Request> request,
  std::shared_ptr<adi_iio::srv::BufferDestroy::Response> response)
{
  RCLCPP_INFO(
    rclcpp::get_logger(
      "rclcpp"), "Service request buffer destroy %s", request->device_path.c_str());

  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    if (m_bufferMap[request->device_path]->buffer()) {
      m_bufferMap[request->device_path]->destroyIIOBuffer();
      response->success = true;
      response->message = "Success";
      return;
    }
  }

  response->success = false;
  response->message = "Buffer not found";
}

void IIONode::buffEnableTopicSrv(
  const std::shared_ptr<adi_iio::srv::BufferEnableTopic::Request> request,
  std::shared_ptr<adi_iio::srv::BufferEnableTopic::Response> response)
{
  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    m_bufferMap[request->device_path]->enableTopic(request->topic_name);
    response->success = true;
    response->message = "Success";
  } else {
    response->success = false;
    response->message = "Buffer not found";
  }
}

void IIONode::buffDisableTopicSrv(
  const std::shared_ptr<adi_iio::srv::BufferDisableTopic::Request> request,
  std::shared_ptr<adi_iio::srv::BufferDisableTopic::Response> response)
{
  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    m_bufferMap[request->device_path]->disableTopic();
    response->success = true;
    response->message = "Success";
  } else {
    response->success = false;
    response->message = "Buffer not found";
  }
}

void IIONode::listDevicesSrv(
  const std::shared_ptr<adi_iio::srv::ListDevices::Request> request,
  std::shared_ptr<adi_iio::srv::ListDevices::Response> response)
{
  RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Service request: /ListDevices");
  std::string msg;

  IIOPath path("");
  std::vector<std::string> data;

  auto devices_ptr = getDevices(ctx());
  for (iio_device * dev : devices_ptr) {
    auto dev_name = std::string(iio_device_get_name(dev));
    auto dev_path = path.append(dev_name);
    data.push_back(dev_path);
  }

  msg = "Found " + std::to_string(data.size()) + " devices";
  setSuccessResponse(response, msg);
  response->data = {data};
}

void IIONode::listChannelsSrv(
  const std::shared_ptr<adi_iio::srv::ListChannels::Request> request,
  std::shared_ptr<adi_iio::srv::ListChannels::Response> response)
{
  RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Service request: /ListChannels");
  std::string msg;

  IIOPath path(request->iio_path);
  if (!path.isValid(IIOPathType::DEVICE)) {
    msg = "Invalid path: " + request->iio_path;
    setWarningResponse(response, msg);
    return;
  }

  auto dev_name = path.getDeviceSegment();
  iio_device * dev = iio_context_find_device(ctx(), dev_name.c_str());
  if (dev == nullptr) {
    msg = "Could not find device: " + dev_name;
    setWarningResponse(response, msg);
    return;
  }

  std::vector<std::string> data;

  auto channels_ptr = getChannels(dev);
  for (iio_channel * chn : channels_ptr) {
    auto chn_name = std::string(iio_channel_get_id(chn));
    auto is_output = iio_channel_is_output(chn);
    auto chn_path = IIOPath::toExtendedChannelSegment(is_output, chn_name);
    data.push_back(path.append(chn_path));
  }

  msg = "Found " + std::to_string(data.size()) + " channels in device: " + dev_name;
  setSuccessResponse(response, msg);
  response->data = {data};
}

void IIONode::listAttributesSrv(
  const std::shared_ptr<adi_iio::srv::ListAttributes::Request> request,
  std::shared_ptr<adi_iio::srv::ListAttributes::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request: /ListAttributes");
  std::string msg;
  std::vector<std::string> data;

  IIOPath path(request->iio_path);
  if (path.isValid(IIOPathType::CONTEXT)) {
    int ret{};
    std::string err_str;

    unsigned int nb_ctx_attrs = iio_context_get_attrs_count(ctx());
    for (unsigned int i = 0; i < nb_ctx_attrs; i++) {
      const char * key, * value;

      ret = iio_context_get_attr(ctx(), i, &key, &value);
      if (ret == 0) {
        data.push_back(path.append(std::string(key)));
      } else {
        err_str = strerror(-ret);
        RCLCPP_WARN(
          rclcpp::get_logger(
            "rclcpp"), "Unable to read IIO context attribute: %s", err_str.c_str());
      }
    }
    msg = "Found " + std::to_string(data.size()) + " attributes";
  } else if (path.isValid(IIOPathType::DEVICE)) {
    auto dev_name = path.getDeviceSegment();
    iio_device * dev = iio_context_find_device(ctx(), dev_name.c_str());
    if (dev == nullptr) {
      msg = "Could not find device: " + dev_name;
      setWarningResponse(response, msg);
      return;
    }

    unsigned int nb_attrs = iio_device_get_attrs_count(dev);
    for (unsigned int i = 0; i < nb_attrs; i++) {
      std::string attr_key = iio_device_get_attr(dev, i);
      data.push_back(path.append(attr_key));
    }
    msg = "Found " + std::to_string(data.size()) + " attributes in device: " + dev_name;
  } else if (path.isValid(IIOPathType::CHANNEL)) {
    auto dev_name = path.getDeviceSegment();
    iio_device * dev = iio_context_find_device(ctx(), dev_name.c_str());
    if (dev == nullptr) {
      msg = "Could not find device: " + dev_name;
      setWarningResponse(response, msg);
      return;
    }

    auto [is_output, chn_name] = path.getExtendedChannelSegment();
    iio_channel * chn = iio_device_find_channel(dev, chn_name.c_str(), is_output);
    if (chn == nullptr) {
      msg = "Could not find channel: " + chn_name;
      setWarningResponse(response, msg);
      return;
    }
    unsigned int nb_attrs = iio_channel_get_attrs_count(chn);
    for (unsigned int i = 0; i < nb_attrs; i++) {
      std::string attr_key = iio_channel_get_attr(chn, i);
      data.push_back(path.append(attr_key));
    }
    msg = "Found " + std::to_string(data.size()) + " attributes in channel: " + chn_name;
  } else {
    msg = "Invalid path: " + request->iio_path;
    setErrorResponse(response, msg);
    return;
  }

  setSuccessResponse(response, msg);
  response->data = {data};
}

void IIONode::scanContextSrv(
  const std::shared_ptr<adi_iio::srv::ScanContext::Request> request,
  std::shared_ptr<adi_iio::srv::ScanContext::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request: /ScanContext");
  std::string msg{"Found: "};
  std::vector<std::string> devices;
  std::vector<std::string> channels;
  std::vector<std::string> context_attrs;
  std::vector<std::string> device_attrs;
  std::vector<std::string> channel_attrs;

  // Handle context attributes
  IIOPath ctx_path("");
  int ret{};
  std::string err_str;
  unsigned int nb_ctx_attrs = iio_context_get_attrs_count(ctx());
  for (unsigned int i = 0; i < nb_ctx_attrs; i++) {
    const char * key, * value;
    ret = iio_context_get_attr(ctx(), i, &key, &value);
    if (ret == 0) {
      context_attrs.push_back(ctx_path.append(std::string(key)));
    } else {
      err_str = strerror(-ret);
      RCLCPP_WARN(
        rclcpp::get_logger(
          "rclcpp"),
        "Unable to read IIO context attribute: %s", err_str.c_str());
    }
  }

  // Handle devices
  auto devices_ptr = getDevices(ctx());
  for (iio_device * dev : devices_ptr) {
    auto dev_name = std::string(iio_device_get_name(dev));
    auto dev_path = IIOPath(ctx_path.append(dev_name));

    devices.push_back(dev_path.basePath());

    // Handle device attributes
    unsigned int nb_attrs = iio_device_get_attrs_count(dev);
    for (unsigned int i = 0; i < nb_attrs; i++) {
      std::string attr_key = iio_device_get_attr(dev, i);
      device_attrs.push_back(dev_path.append(attr_key));
    }

    // Handle device channels
    auto channels_ptr = getChannels(dev);
    for (iio_channel * chn : channels_ptr) {
      auto chn_name = std::string(iio_channel_get_id(chn));
      auto is_output = iio_channel_is_output(chn);
      auto chn_segment = IIOPath::toExtendedChannelSegment(is_output, chn_name);
      auto chn_path = IIOPath(dev_path.append(chn_segment));

      channels.push_back(chn_path.basePath());

      // Handle channel attributes
      unsigned int nb_attrs = iio_channel_get_attrs_count(chn);
      for (unsigned int i = 0; i < nb_attrs; i++) {
        std::string attr_key = iio_channel_get_attr(chn, i);
        channel_attrs.push_back(chn_path.append(attr_key));
      }
    }
  }
  msg += "Context attributes: " + std::to_string(context_attrs.size()) + "; ";
  msg += "Devices: " + std::to_string(devices.size()) + "; ";
  msg += "Channels: " + std::to_string(channels.size()) + "; ";
  msg += "Device attributes: " + std::to_string(device_attrs.size()) + "; ";
  msg += "Channel attributes: " + std::to_string(channel_attrs.size()) + "; ";

  setSuccessResponse(response, msg);
  response->devices = {devices};
  response->channels = {channels};
  response->context_attrs = {context_attrs};
  response->device_attrs = {device_attrs};
  response->channel_attrs = {channel_attrs};
}

std::vector<iio_device *> IIONode::getDevices(iio_context * ctx)
{
  std::vector<iio_device *> devices;
  unsigned int devices_count = iio_context_get_devices_count(ctx);
  for (unsigned int i = 0; i < devices_count; i++) {
    iio_device * dev = iio_context_get_device(ctx, i);
    devices.push_back(dev);
  }
  return devices;
}

std::vector<iio_channel *> IIONode::getChannels(iio_device * device)
{
  std::vector<iio_channel *> channels;
  unsigned int channels_count = iio_device_get_channels_count(device);
  for (unsigned int i = 0; i < channels_count; i++) {
    iio_channel * ch = iio_device_get_channel(device, i);
    channels.push_back(ch);
  }
  return channels;
}

std::string IIONode::uri()
{
  return m_uri;
}

iio_context * IIONode::ctx()
{
  return m_ctx;
}
