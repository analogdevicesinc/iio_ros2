#include "adi_iio/iio_attr_topic.hpp"
#include "adi_iio/iio_node.hpp"
#include "adi_iio/attr_publisher.hpp"
#include <memory>

IIOAttrTopic::IIOAttrTopic(std::shared_ptr<IIONode> nh, std::string topicName, std::string attrPath, topicType_t type, int loopRate)
  : m_loopRate(loopRate)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created IIOAttrTopic");  
  m_nh = nh;
  m_attrPath = attrPath;
  m_topicName = topicName;
  m_topicType = type;
  m_stopThread = false;

  // Start the thread for the publishing loop
  switch(type) {
    case TYPE_STRING:
      m_pub = std::make_unique<StringPubSub>(m_nh, this, m_topicName);
      break;
    case TYPE_INT:
      m_pub = std::make_unique<Int32PubSub>(m_nh, this, m_topicName);
      break;
    default:
      m_pub = std::make_unique<StringPubSub>(m_nh, this, m_topicName);
      break;
  }
  
  m_th = std::thread(&IIOAttrTopic::publishingLoop, this);  
}

IIOAttrTopic::~IIOAttrTopic()
{
  // Stop the thread gracefully

  m_stopThread = true;
  if (m_th.joinable())
  {
    m_th.join();
  }
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted IIOAttrTopic");  
}

void IIOAttrTopic::publishingLoop()
{
  while (rclcpp::ok() && !m_stopThread)
  {
    m_mutex.lock();
    
    std::string msg;
    m_nh->rwAttrPath(m_attrPath, msg);
    last_val = msg;
    m_pub->publish(msg);
    m_mutex.unlock();
    // Sleep to maintain the loop rate
    m_loopRate.sleep();
  }
}

void IIOAttrTopic::update(std::string msg) {
  m_mutex.lock();
  std::string result;
  m_nh->rwAttrPath(m_attrPath, result, true, msg);
  m_mutex.unlock();
}
