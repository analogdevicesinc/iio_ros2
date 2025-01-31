#include "adi_iio/iio_buffer.hpp"

IIOBuffer::IIOBuffer(std::shared_ptr<IIONode> nh, std::string device_path, std::vector<std::string> channels,
                     int32_t samples_count)
{
  this->m_nh = nh;
  this->m_device_path = device_path;
  this->m_channels = channels;
  this->m_samples_count = samples_count;
  this->m_buffer = nullptr;
}

IIOBuffer::~IIOBuffer()
{
  if (m_buffer)
  {
    iio_buffer_destroy(m_buffer);
    RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Destroyed buffer %p", (void*)m_buffer);
  }
}

bool IIOBuffer::setupIIOBuffer(std::string &message)
{
  iio_device* dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  if (dev == nullptr)
  {
    message = "Device not found";
    RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find device \"%s\" - errno %d - %s", m_device_path.c_str(),
                errno, message.c_str());
    return false;
  }

  // verify channel count
  if (m_channels.size() == 0)
  {
    message = "No channels to read";
    return false;
  }

  if(m_samples_count == 0) {
    message = "No samples to read";
    return false;
  }

  // validate that all channels exist
  for (auto& channel : m_channels)
  {
    iio_channel* ch = iio_device_find_channel(dev, channel.c_str(), false);
    if (ch == nullptr)
    {
      message = strerror(-errno);
      RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find channel \"%s\" in device \"%s\" - errno %d - %s",
                  channel.c_str(), m_device_path.c_str(), errno, message.c_str());
      return false;
    }
  }

  // disable all channels
  for (unsigned int i = 0; i < iio_device_get_channels_count(dev); i++)
  {
    iio_channel_disable(iio_device_get_channel(dev, i));
    RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Disabling channel %d", i);
  }

  // enable channels
  for (auto& channel : m_channels)
  {
    iio_channel* ch = iio_device_find_channel(dev, channel.c_str(), false);
    if (ch == nullptr)
    {
      message = strerror(-errno);
      RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not find channel \"%s\" in device \"%s\" - errno %d - %s",
                  channel.c_str(), m_device_path.c_str(), errno, message.c_str());
      return false;
    }
    iio_channel_enable(ch);
    RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Enabling channel %s", channel.c_str());
  }

  m_buffer = iio_device_create_buffer(dev, m_samples_count, false);
  if (m_buffer == nullptr)
  {
    message = strerror(-errno);
    RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not create buffer in device \"%s\" - errno %d - %s",
                m_device_path.c_str(), errno, message.c_str());
    return false;
  }
  RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Created buffer %p", (void*)m_buffer);
  message = "Success";
  return true;
}

bool IIOBuffer::refill(std::string &message, std_msgs::msg::Int32MultiArray &buffer)
{
  iio_device* dev = iio_context_find_device(m_nh->ctx(), m_device_path.c_str());
  ssize_t size = iio_buffer_refill(m_buffer);
  RCLCPP_DEBUG(rclcpp::get_logger("rclcpp"), "Refilled buffer with %ld bytes from HW", size);

  if (size < 0)
  {
    message = strerror(-errno);
    RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "could not refill buffer in device \"%s\" - errno %d - %s",
                m_device_path.c_str(), errno, message.c_str());
    iio_buffer_destroy(m_buffer);
    return false;
  }

  buffer.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  buffer.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
  buffer.layout.dim[0].label = "samples";
  buffer.layout.dim[0].size = m_samples_count;
  buffer.layout.dim[0].stride = m_channels.size() * m_samples_count;
  buffer.layout.dim[1].label = "channels";
  buffer.layout.dim[1].size = m_channels.size();
  buffer.layout.dim[1].stride = m_channels.size();

  for (int i = 0; i < m_samples_count; i++)
  {
    for (auto& channel : m_channels)
    {
      iio_channel* ch = iio_device_find_channel(dev, channel.c_str(), false);
      void* sample = ((int32_t*)iio_buffer_first(m_buffer, ch) + iio_buffer_step(m_buffer) * i);
      int32_t val = 0;
      iio_channel_convert(ch, &val, sample);
      const iio_data_format* fmt = iio_channel_get_data_format(ch);
      // val = val & ((1<<fmt->bits) - 1);
      if (val & (1 << (fmt->bits)))
      {  // sign extension
        val = val | (~((1 << fmt->bits) - 1));
      }
      buffer.data.push_back(val);
    }
  }
  message = "Success";
  return true;
}
