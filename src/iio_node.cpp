#include "adi_iio/iio_node.hpp"
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

IIONode::IIONode() : Node("adi_iio_node")
{
  m_initialized = false;
  this->declare_parameter<std::string>("uri", "local:");
  m_uri = this->get_parameter("uri").as_string();

  m_ctx = iio_create_context_from_uri(m_uri.c_str());

  if (m_ctx != nullptr)
  {
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "creating context %p from uri %s", (void*)m_ctx, m_uri.c_str());
    m_initialized = true;
  }
  else
  {
    RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "cannot create context from uri %s", m_uri.c_str());
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

bool IIONode::rwAttrPath(std::string path, std::string& result, bool write, std::string value)
{
  bool ret = false;
  std::string str = path;
  std::stringstream ss(str);
  std::string segment;
  std::vector<std::string> segments;

  iio_device* dev = nullptr;
  iio_channel* ch = nullptr;

  while (std::getline(ss, segment, '/'))
  {
    segments.push_back(segment);  // Push each part of the string into the vector
  }

  char* val;
  char attr_val[MAX_ATTR_SIZE];
  int ret1;
  switch (segments.size())
  {
    case 1:  // context_attribute
      val = (char*)iio_context_get_attr_value(m_ctx, segments[0].c_str());
      if (val)
      {
        ret = true;
        result = val;
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "read context attribute \"%s\" with value \"%s\"",
                    segments[0].c_str(), val);
      }
      else
      {
        ret = false;
        result = "";
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find context attribute \"%s\"", segments[0].c_str());
      }

      if (write)
      {
        ret = false;
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "context attributes cannot be written");
      }
      break;

    case 2:  // device_attribute
      dev = iio_context_find_device(m_ctx, segments[0].c_str());
      if (!dev)
      {
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find device \"%s\"", segments[0].c_str());
        break;
      }
      if (write)
      {
        ret1 = iio_device_attr_write(dev, segments[1].c_str(), value.c_str());
        if (ret1 > 0)
        {
          RCLCPP_INFO(rclcpp::get_logger("rclcpp"),
                      "wrote device attribute \"%s\" from device \"%s\" with value \"%s\"", segments[1].c_str(),
                      segments[0].c_str(), value.c_str());
        }
        else
        {
          result = strerror(-ret1);
          ret = false;
          RCLCPP_WARN(rclcpp::get_logger("rclcpp"),
                      "could not write attribute \"%s\" in device \"%s\" with value \"%s\" - errno %d - %s",
                      segments[1].c_str(), segments[0].c_str(), value.c_str(), ret1, result.c_str());
          break;
        }
      }

      ret1 = iio_device_attr_read(dev, segments[1].c_str(), attr_val, MAX_ATTR_SIZE);
      if (ret1 > 0)
      {
        result = attr_val;
        ret = true;
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "read device attribute \"%s\" from device \"%s\" with value \"%s\"",
                    segments[1].c_str(), segments[0].c_str(), attr_val);
      }
      else
      {
        result = strerror(-ret1);
        ret = false;
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not read attribute \"%s\" in device \"%s\" - errno %d - %s",
                    segments[1].c_str(), segments[0].c_str(), ret1, result.c_str());
      }
      break;

    case 3:  // channel_attribute
      dev = iio_context_find_device(m_ctx, segments[0].c_str());
      if (!dev)
      {
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find device \"%s\"", segments[0].c_str());
        break;
      }

      if (segments[1].find("input_") == 0)
      {
        ch = iio_device_find_channel(dev, segments[1].substr(strlen("input_")).c_str(), false);
      }
      else if (segments[1].find("output_") == 0)
      {
        ch = iio_device_find_channel(dev, segments[1].substr(strlen("output_")).c_str(), true);
      }
      else
      {
        ch = iio_device_find_channel(dev, segments[1].c_str(), false);
        if (!ch)
        {
          ch = iio_device_find_channel(dev, segments[1].c_str(), true);
        }
      }

      if (!ch)
      {
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find channel \"%s\"", segments[1].c_str());
        break;
      }

      if (write)
      {
        ret1 = iio_channel_attr_write(ch, segments[2].c_str(), value.c_str());
        if (ret1 > 0)
        {
          RCLCPP_INFO(rclcpp::get_logger("rclcpp"),
                      "wrote channel attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"",
                      segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), value.c_str());
        }
        else
        {
          result = strerror(-ret1);
          ret = false;
          RCLCPP_WARN(rclcpp::get_logger("rclcpp"),
                      "could not write attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"- errno %d "
                      "- %s",
                      segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), value.c_str(), ret1,
                      result.c_str());
          break;
        }
      }

      ret1 = iio_channel_attr_read(ch, segments[2].c_str(), attr_val, MAX_ATTR_SIZE);
      if (ret1 > 0)
      {
        result = attr_val;
        ret = true;
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"),
                    "read channel attribute \"%s\" from channel \"%s\" device \"%s\" with value \"%s\"",
                    segments[2].c_str(), segments[1].c_str(), segments[0].c_str(), attr_val);
      }
      else
      {
        result = strerror(-ret1);
        ret = false;
        RCLCPP_WARN(rclcpp::get_logger("rclcpp"),
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

void IIONode::attrReadSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Request> request,  // CHANGE
                          std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request read attr: %s", request->attr_path.c_str());
  std::string result;
  response->success = rwAttrPath(request->attr_path, result);
  response->message = result;
}

void IIONode::attrWriteSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Request> request,  // CHANGE
                           std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request write attr %s value %s", request->attr_path.c_str(),
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

void IIONode::attrEnableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Request> request,
                                 std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request enable topic %s with type %s with loop_rate %d Hz",
              request->attr_path.c_str(), request->attr_path.c_str(), request->loop_rate);

  std::string result;
  response->success = rwAttrPath(request->attr_path, result);
  response->message = result;

  std::string local_topic_name = request->topic_name;
  if (local_topic_name == "")
  {
    local_topic_name = convertAttrPathToTopicName(request->attr_path);
  }

  if (response->success)
  {
    if (m_attrTopicMap.find(local_topic_name) != m_attrTopicMap.end())
    {
      m_attrTopicMap.erase(local_topic_name);
    }

    m_attrTopicMap.insert(
        { local_topic_name,
          std::make_shared<IIOAttrTopic>(std::dynamic_pointer_cast<IIONode>(shared_from_this()), local_topic_name,
                                         request->attr_path, static_cast<IIOAttrTopic::topicType_t>(request->type),
                                         request->loop_rate) });

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

void IIONode::attrDisableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Request> request,
                                  std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request disable topic %s ", request->topic_name.c_str());

  std::string local_topic_name = request->topic_name;
  local_topic_name = convertAttrPathToTopicName(request->topic_name);  // for compatibility with enable

  if (m_attrTopicMap.find(local_topic_name) != m_attrTopicMap.end())
  {
    m_attrTopicMap.erase(local_topic_name);
    response->success = true;
    response->message = "Success";
  }
  else
  {
    response->success = false;
    response->message = "Topic not found";
  }
}

void IIONode::buffRefillSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferRefill::Request> request,
                         std::shared_ptr<adi_iio_interfaces::srv::BufferRefill::Response> response)
{
if (m_bufferMap.find(request->device_path) == m_bufferMap.end()) {
    response->success = false;
    response->message = "Buffer not found";
  } else {
    std::string message;
    response->success = m_bufferMap[request->device_path]->refill(message, response->buffer);
    response->message = message;
  }
}

void IIONode::buffReadSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferRead::Request> request,
                          std::shared_ptr<adi_iio_interfaces::srv::BufferRead::Response> response)
{
  std::string channels;
  for (auto& channel : request->channels)
  {
    channels += channel + " ";
  }

  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request buffer create %s - %s - %d samples",
              request->device_path.c_str(), channels.c_str(), request->samples_count);

  std::string message;
  
  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    m_bufferMap.erase(request->device_path);
  }

  std::shared_ptr<IIOBuffer> buffer = std::make_shared<IIOBuffer>(std::dynamic_pointer_cast<IIONode>(shared_from_this()), request->device_path, request->channels, request->samples_count);
  m_bufferMap.insert({request->device_path, buffer});

  response->success = buffer->setupIIOBuffer(message);
  if(!response->success) {
    m_bufferMap.erase(request->device_path);
    response->message = message;
    return;
  }
  
  response->success = m_bufferMap[request->device_path]->refill(message, response->buffer);
  response->message = message;

}

void IIONode::buffCreateSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferCreate::Request> request,
                            std::shared_ptr<adi_iio_interfaces::srv::BufferCreate::Response> response)
{
 std::string channels;
  for (auto& channel : request->channels)
  {
    channels += channel + " ";
  }

  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request buffer create %s - %s - %d samples",
              request->device_path.c_str(), channels.c_str(), request->samples_count);

  std::string message;
  
  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    m_bufferMap.erase(request->device_path);
  }

  std::shared_ptr<IIOBuffer> buffer = std::make_shared<IIOBuffer>(std::dynamic_pointer_cast<IIONode>(shared_from_this()), request->device_path, request->channels, request->samples_count);
  m_bufferMap.insert({request->device_path, buffer});

  response->success = buffer->setupIIOBuffer(message);
  if(!response->success) {
    m_bufferMap.erase(request->device_path);
    response->message = message;
    return;
  }
}

void IIONode::buffDestroySrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferDestroy::Request> request,
                             std::shared_ptr<adi_iio_interfaces::srv::BufferDestroy::Response> response)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service request buffer destroy %s",
              request->device_path.c_str());

  if (m_bufferMap.find(request->device_path) != m_bufferMap.end()) {
    m_bufferMap.erase(request->device_path);
    response->success = true;
    response->message = "Success";
  } else {
    response->success = false;
    response->message = "Buffer not found";
  }
}

std::string IIONode::uri()
{
  return m_uri;
}

iio_context* IIONode::ctx()
{
  return m_ctx;
}