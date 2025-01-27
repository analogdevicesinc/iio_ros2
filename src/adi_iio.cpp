#include <rclcpp/rclcpp.hpp>
#include "adi_iio_interfaces/srv/attr_read_string.hpp"
#include "adi_iio_interfaces/srv/attr_write_string.hpp"
#include "adi_iio/iio_node.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  std::shared_ptr<IIONode> node = std::make_shared<IIONode>();

  if (!node->initialized()) {
        RCLCPP_FATAL(rclcpp::get_logger("rclcpp"), "Node initialization failed.");
        return EXIT_FAILURE; // Fail if the node isn't properly initialized
    }


  rclcpp::Service<adi_iio_interfaces::srv::AttrReadString>::SharedPtr attrReadSrv =
    node->create_service<adi_iio_interfaces::srv::AttrReadString>(
      std::string(node->get_name())+"/AttrReadString", 
      std::bind(&IIONode::attrReadSrv, node, std::placeholders::_1, std::placeholders::_2));

  rclcpp::Service<adi_iio_interfaces::srv::AttrWriteString>::SharedPtr attrWriteSrv =
    node->create_service<adi_iio_interfaces::srv::AttrWriteString>(
      std::string(node->get_name())+"/AttrWriteString", 
      std::bind(&IIONode::attrWriteSrv, node, std::placeholders::_1, std::placeholders::_2));

  rclcpp::Service<adi_iio_interfaces::srv::AttrEnableTopic>::SharedPtr attrEnableTopicSrv =
    node->create_service<adi_iio_interfaces::srv::AttrEnableTopic>(
    std::string(node->get_name())+"/AttrEnableTopic", 
    std::bind(&IIONode::attrEnableTopicSrv, node, std::placeholders::_1, std::placeholders::_2));

  rclcpp::Service<adi_iio_interfaces::srv::AttrDisableTopic>::SharedPtr attrDisableTopicSrv =
    node->create_service<adi_iio_interfaces::srv::AttrDisableTopic>(
    std::string(node->get_name())+"/AttrDisableTopic", 
    std::bind(&IIONode::attrDisableTopicSrv, node, std::placeholders::_1, std::placeholders::_2));


  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "IIO Node");

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
