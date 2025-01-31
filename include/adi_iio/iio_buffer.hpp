#ifndef IIO_BUFFER_HPP
#define IIO_BUFFER_HPP

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32_multi_array.hpp>
#include "adi_iio/iio_node.hpp"
#include "iio.h"

class IIOBuffer {
public:
    IIOBuffer(std::shared_ptr<IIONode> nh, std::string device_path, std::vector<std::string> channels, int32_t samples_count);
    ~IIOBuffer();

    bool setupIIOBuffer(std::string &message);
    bool refill(std::string &message, std_msgs::msg::Int32MultiArray &buffer);

private:
    std::shared_ptr<IIONode> m_nh;
    std::string m_device_path;
    std::vector<std::string> m_channels;
    int32_t m_samples_count;
    iio_buffer *m_buffer;


};

#endif
