#ifndef ATTR_PUBLISHER_HPP
#define ATTR_PUBLISHER_HPP

#include <string>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_msgs/msg/int32.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/float32.hpp>

#include "adi_iio/iio_node.hpp"

#define QOS_QUEUE_SIZE 10

#define READ_SUFFIX "/read"
#define WRITE_SUFFIX "/write"

class AttrPubSub {
    public:
    virtual ~AttrPubSub() {}
    virtual void publish(std::string msg) = 0;
};


// these could be templates ?

class StringPubSub : public AttrPubSub {
public:
    StringPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic);
    virtual ~StringPubSub();
    void publish(std::string msg) override;
    void update(const std_msgs::msg::String & msg);

private:
    std::shared_ptr<IIONode> m_nh;
    UpdateCallback* m_updateCallback;
    std::string m_topic;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr m_pub;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr m_sub;
};

class Int32PubSub : public AttrPubSub {
public:
    Int32PubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic);
    virtual ~Int32PubSub();
    void publish(std::string msg) override;
    void update(const std_msgs::msg::Int32 & msg);

private:
    std::shared_ptr<IIONode> m_nh;
    UpdateCallback* m_updateCallback;
    std::string m_topic;
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr m_pub;
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr m_sub;
};

class BoolPubSub : public AttrPubSub {
public:
    BoolPubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic);
    virtual ~BoolPubSub();
    void publish(std::string msg) override;
    void update(const std_msgs::msg::Bool & msg);

private:
    std::shared_ptr<IIONode> m_nh;
    UpdateCallback* m_updateCallback;
    std::string m_topic;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr m_pub;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr m_sub;
};


class Float32PubSub : public AttrPubSub {
public:
    Float32PubSub(std::shared_ptr<IIONode> nh, UpdateCallback *up, std::string topic);
    virtual ~Float32PubSub();
    void publish(std::string msg) override;
    void update(const std_msgs::msg::Float32 & msg);

private:
    std::shared_ptr<IIONode> m_nh;
    UpdateCallback* m_updateCallback;
    std::string m_topic;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr m_pub;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr m_sub;
};


#endif