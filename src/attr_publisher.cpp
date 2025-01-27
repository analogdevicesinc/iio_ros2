#include "adi_iio/iio_attr_topic.hpp"
#include "adi_iio/attr_publisher.hpp"

using std::placeholders::_1;

StringPubSub::StringPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created String publisher ");
  m_topic = topic;
  m_nh = nh;
  m_updateCallback = up;
  m_pub = m_nh->create_publisher<std_msgs::msg::String>(topic + READ_SUFFIX, QOS_QUEUE_SIZE);
  m_sub = m_nh->create_subscription<std_msgs::msg::String>(
       topic + WRITE_SUFFIX, QOS_QUEUE_SIZE, std::bind(&StringPubSub::update, this, _1));
}

StringPubSub::~StringPubSub()
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted String publisher ");
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

Int32PubSub::Int32PubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created Int32 publisher ");
  m_topic = topic;
  m_nh = nh;
  m_updateCallback = up;
  m_pub = m_nh->create_publisher<std_msgs::msg::Int32>(topic + READ_SUFFIX, QOS_QUEUE_SIZE);
  m_sub = m_nh->create_subscription<std_msgs::msg::Int32>(
       topic + WRITE_SUFFIX, QOS_QUEUE_SIZE, std::bind(&Int32PubSub::update, this, _1));
}

Int32PubSub::~Int32PubSub()
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted Int32 publisher ");
  // shared ptr lifetime should delete this publisher automatically
}

void Int32PubSub::publish(std::string msg)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Publishing msg %s on topic %s", msg.c_str(), m_topic.c_str());  
  auto message = std_msgs::msg::Int32();
  int32_t data = stoi(msg);
  message.data = data;

  m_pub->publish(message);
}

void Int32PubSub::update(const std_msgs::msg::Int32 & msg)
{
  std::string strData = std::to_string(msg.data);
  m_updateCallback->update(strData);
}


BoolPubSub::BoolPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created Bool publisher ");
  m_topic = topic;
  m_nh = nh;
  m_updateCallback = up;
  m_pub = m_nh->create_publisher<std_msgs::msg::Bool>(topic + READ_SUFFIX, QOS_QUEUE_SIZE);
  m_sub = m_nh->create_subscription<std_msgs::msg::Bool>(
       topic + WRITE_SUFFIX, QOS_QUEUE_SIZE, std::bind(&BoolPubSub::update, this, _1));
}

BoolPubSub::~BoolPubSub()
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted Bool publisher ");
  // shared ptr lifetime should delete this publisher automatically
}

void BoolPubSub::publish(std::string msg)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Publishing msg %s on topic %s", msg.c_str(), m_topic.c_str());  
  auto message = std_msgs::msg::Bool();
  bool data = stoi(msg);
  message.data = data;

  m_pub->publish(message);
}

void BoolPubSub::update(const std_msgs::msg::Bool & msg)
{
  std::string strData = std::to_string(msg.data);
  m_updateCallback->update(strData);
}


Float32PubSub::Float32PubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Created Float32 publisher ");
  m_topic = topic;
  m_nh = nh;
  m_updateCallback = up;
  m_pub = m_nh->create_publisher<std_msgs::msg::Float32>(topic + READ_SUFFIX, QOS_QUEUE_SIZE);
  m_sub = m_nh->create_subscription<std_msgs::msg::Float32>(
       topic + WRITE_SUFFIX, QOS_QUEUE_SIZE, std::bind(&Float32PubSub::update, this, _1));
}

Float32PubSub::~Float32PubSub()
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Deleted Float32 publisher ");
  // shared ptr lifetime should delete this publisher automatically
}

void Float32PubSub::publish(std::string msg)
{
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Publishing msg %s on topic %s", msg.c_str(), m_topic.c_str());  
  auto message = std_msgs::msg::Float32();
  bool data = stoi(msg);
  message.data = data;

  m_pub->publish(message);
}

void Float32PubSub::update(const std_msgs::msg::Float32 & msg)
{
  std::string strData = std::to_string(msg.data);
  m_updateCallback->update(strData);
}