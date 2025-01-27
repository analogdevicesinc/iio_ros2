#include "adi_iio/iio_attr_topic.hpp"
#include "adi_iio/attr_publisher.hpp"

using std::placeholders::_1;

StringPubSub::StringPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created string publisher ");
  m_topic = topic;
  m_nh = nh;
  m_updateCallback = up;
  m_pub = m_nh->create_publisher<std_msgs::msg::String>(topic + "/read", QOS_QUEUE_SIZE);
  m_sub = m_nh->create_subscription<std_msgs::msg::String>(
       topic + "/write", QOS_QUEUE_SIZE, std::bind(&StringPubSub::update, this, _1));
}

StringPubSub::~StringPubSub()
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted string publisher ");
  // shared ptr lifetime should delete this publisher automatically
}

void StringPubSub::publish(std::string msg)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Publishing msg %s on topic %s", msg.c_str(), m_topic.c_str());  
  auto message = std_msgs::msg::String();
  message.data = msg;
  m_pub->publish(message);
}

void StringPubSub::update(const std_msgs::msg::String & msg)
{
  m_updateCallback->update(msg.data);
}