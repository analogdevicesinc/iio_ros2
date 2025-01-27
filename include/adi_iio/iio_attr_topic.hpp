#ifndef IIO_ATTR_TOPIC_HPP
#define IIO_ATTR_TOPIC_HPP

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <thread>
#include "iio.h"
#include <memory>

class IIONode;
class AttrPubSub;

class UpdateCallback {
    public:
    virtual ~UpdateCallback() {};
    virtual void update(std::string msg) = 0;
};

class IIOAttrTopic : public UpdateCallback {
public:
    typedef enum {
        TYPE_STRING,
        TYPE_INT,
        TYPE_DOUBLE,
        TYPE_BOOL
    } topicType_t;

    IIOAttrTopic(std::shared_ptr<IIONode> nh, std::string topicName, std::string attrPath, topicType_t type, int loopRate);
    virtual ~IIOAttrTopic();

    void publishingLoop();
    void update(std::string msg) override;

private:
    std::mutex m_mutex;
    rclcpp::TimerBase::SharedPtr timer_;

    std::shared_ptr<IIONode> m_nh;
    std::string m_attrPath;
    std::string m_topicName;
    topicType_t m_topicType;
    std::unique_ptr<AttrPubSub> m_pub;

    std::thread m_th;
    std::string last_val;
    bool m_stopThread;
    rclcpp::Rate m_loopRate;

};

#endif
