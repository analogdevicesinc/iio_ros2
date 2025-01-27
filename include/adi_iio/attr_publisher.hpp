#ifndef ATTR_PUBLISHER_HPP
#define ATTR_PUBLISHER_HPP

#include <string>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

#include "adi_iio/iio_node.hpp"

#define QOS_QUEUE_SIZE 10

#define READ_SUFFIX "/read"
#define WRITE_SUFFIX "/write"

class AttrPubSub {
    public:
    virtual ~AttrPubSub() {}
    virtual void publish(std::string msg) = 0;
    virtual void update(const std_msgs::msg::String & msg) = 0;
};

class StringPubSub : public AttrPubSub {
public:
    StringPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic);
    virtual ~StringPubSub();
    void publish(std::string msg) override;
    void update(const std_msgs::msg::String & msg) override;

private:
    std::shared_ptr<IIONode> m_nh;
    UpdateCallback* m_updateCallback;
    std::string m_topic;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr m_pub;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr m_sub;
};

#endif