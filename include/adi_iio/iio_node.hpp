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
#include "adi_iio_interfaces/srv/buffer_create.hpp"
#include "adi_iio_interfaces/srv/buffer_destroy.hpp"
#include "adi_iio_interfaces/srv/buffer_refill.hpp"
#include "adi_iio_interfaces/srv/buffer_read.hpp"
#include "iio.h"

class IIOAttrTopic;
class IIOBuffer;

class IIONode : public rclcpp::Node
{
public:

  IIONode();
  virtual ~IIONode();

  bool rwAttrPath(std::string path, std::string &result, bool write = false, std::string value = "");
  std::string convertAttrPathToTopicName(std::string path);

  // service handlers
  void attrReadSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Request> request,
            std::shared_ptr<adi_iio_interfaces::srv::AttrReadString::Response>  response);

  void attrWriteSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Request> request,
          std::shared_ptr<adi_iio_interfaces::srv::AttrWriteString::Response>  response);
  
  void attrEnableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Request> request,
          std::shared_ptr<adi_iio_interfaces::srv::AttrEnableTopic::Response>  response);
  
  void attrDisableTopicSrv(const std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::AttrDisableTopic::Response>  response);

  void buffRefillSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferRefill::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::BufferRefill::Response>  response);

  void buffReadSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferRead::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::BufferRead::Response>  response);

  void buffCreateSrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferCreate::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::BufferCreate::Response>  response);

  void buffDestroySrv(const std::shared_ptr<adi_iio_interfaces::srv::BufferDestroy::Request> request, 
          std::shared_ptr<adi_iio_interfaces::srv::BufferDestroy::Response>  response);

  // getters
  std::string uri();
  bool initialized();
  iio_context* ctx();

private:
  bool m_initialized;
  std::string m_uri;
  iio_context *m_ctx;

  std::map<std::string, std::shared_ptr<IIOAttrTopic>> m_attrTopicMap;
  std::map<std::string, std::shared_ptr<IIOBuffer>> m_bufferMap;
  
};

#endif