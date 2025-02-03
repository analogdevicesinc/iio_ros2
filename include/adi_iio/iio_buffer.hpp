#ifndef IIO_BUFFER_HPP
#define IIO_BUFFER_HPP

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32_multi_array.hpp>
#include "adi_iio/iio_node.hpp"
#include "iio.h"

#define BUFFER_QOS_QUEUE_SIZE 10

#define BUFFER_READ_SUFFIX ""
#define BUFFER_WRITE_SUFFIX ""

class IIOBuffer {
public:
    IIOBuffer(std::shared_ptr<IIONode> nh, std::string device_path);
    ~IIOBuffer();

    bool createIIOBuffer(std::string &message);
    void destroyIIOBuffer();
    bool refill(std::string &message);

    void enableTopic(std::string topic_name);
    void disableTopic();
    void publishingLoop();

    int32_t samples_count() { return m_samples_count; }
    std::string device_path() { return m_device_path; }
    std::vector<std::string> channels() { return m_channels; }
    iio_buffer* buffer() { return m_buffer; }
    bool topic_enabled() { return m_topic_enabled; }
    std_msgs::msg::Int32MultiArray &data() { 
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_data; }

    void set_samples_count(int32_t samples_count) { m_samples_count = samples_count; }
    void set_device_path(std::string device_path) { m_device_path = device_path; }
    void set_channels(std::vector<std::string> channels) { m_channels = channels; }
    

private:
    std::shared_ptr<IIONode> m_nh;
    std::string m_device_path;
    std::vector<std::string> m_channels;
    int32_t m_samples_count;
    iio_buffer *m_buffer;

    std_msgs::msg::Int32MultiArray m_data;
    
    bool m_topic_enabled;
    std::string m_topic_name;
    rclcpp::Publisher<std_msgs::msg::Int32MultiArray>::SharedPtr m_pub;
    std::thread m_th;
    bool m_stopThread;
    std::mutex m_mutex;
};

#endif
