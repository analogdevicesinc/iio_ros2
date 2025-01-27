#ifndef IIO_NODE_HPP
#define IIO_NODE_HPP

#include <chrono>
#include <functional>
#include <string>
#include <map>
#include <memory>

#include <rclcpp/rclcpp.hpp>
#include "adi_iio_interfaces/srv/attr_read_string.hpp"
#include "adi_iio_interfaces/srv/attr_write_string.hpp"
#include "adi_iio_interfaces/srv/attr_enable_topic.hpp"
#include "adi_iio_interfaces/srv/attr_disable_topic.hpp"
#include "iio.h"

class IIOAttrTopic;

class IIONode : public rclcpp::Node
{
public:

  IIONode();
  virtual ~IIONode();

  // service handlers
  bool rwAttrPath(std::string path, std::string &result, bool write = false, std::string value = "");
  void attrReadSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Request> request,
            std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Response>  response);

  void attrWriteSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Request> request,
          std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Response>  response);
  
  void attrEnableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Request> request,
          std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Response>  response);
  
  void attrDisableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Response>  response);


  // getters
  std::string uri();
  bool initialized();

private:
  bool m_initialized;
  std::string m_uri;
  iio_context *m_ctx;

  std::map<std::string, std::shared_ptr<IIOAttrTopic>> m_attrTopicMap;
  
};

#endif