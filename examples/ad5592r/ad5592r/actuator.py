# Copyright 2025 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from adi_iio.srv import AttrDisableTopic, AttrEnableTopic, AttrReadString
from rclpy.node import Node, ParameterDescriptor
from std_msgs.msg import Float64, String


class Actuator(Node):
    def __init__(self):
        super().__init__('actuator')

        self.declare_parameter('loop_rate', 1.0)
        self.declare_parameter("srv_provider", "/adi_iio_node")
        self.declare_parameter("qos", 10)

        # Device parameters
        self.declare_parameter(
            "anode_raw",
            "ad5592r/output_voltage2/raw",
            descriptor=ParameterDescriptor(
                description="Path to raw attribute of AD5592R channel connected to anode."
            )
        )
        self.declare_parameter(
            "anode_scale",
            "ad5592r/output_voltage2/scale",
            descriptor=ParameterDescriptor(
                description="Path to scale attribute of AD5592R channel connected to anode."
            )
        )
        self.declare_parameter(
            "cathode_raw",
            "ad5592r/output_voltage3/raw",
            descriptor=ParameterDescriptor(
                description="Path to raw attribute of AD5592R channel connected to cathode."
            )
        )
        self.declare_parameter(
            "cathode_scale",
            "ad5592r/output_voltage3/scale",
            descriptor=ParameterDescriptor(
                description="Path to scale attribute of AD5592R channel connected to cathode."
            )
        )

        # Topics
        self.declare_parameter(
            "anode_topic",
            "anode",
            descriptor=ParameterDescriptor(
                description="Specifies the name of the topic that provides voltage data. This data will be converted to raw values and used to control the anode's raw channel on the device."
            )
        )
        self.declare_parameter(
            "cathode_topic",
            "cathode",
            descriptor=ParameterDescriptor(
                description="Specifies the name of the topic that provides voltage data. This data will be converted to raw values and used to control the cathode's raw channel on the device."
            )
        )

        self.loop_rate: float = float(self.get_parameter('loop_rate').value)
        self.srv_provider: str = self.get_parameter('srv_provider').value
        self.qos: int = int(self.get_parameter('qos').value)

        self.scale_anode = None
        self.scale_cathode = None

        self.setup_service_clients()

        self.anode_data_sub = self.create_subscription(
            Float64,
            self.get_parameter("anode_topic").value,
            self.anode_data_callback,
            self.qos,
        )
        self.cathode_data_sub = self.create_subscription(
            Float64,
            self.get_parameter("cathode_topic").value,
            self.cathode_data_callback,
            self.qos,
        )

        self.anode_raw_write_pub = self.create_publisher(
            String,
            f"{self.get_parameter('anode_raw').value}/write",
            self.qos,
        )
        self.cathode_raw_write_pub = self.create_publisher(
            String,
            f"{self.get_parameter('cathode_raw').value}/write",
            self.qos,
        )

        self.read_scale()

    def setup_service_clients(self):
        self.attr_read_string_srv_client = self.create_client(
            AttrReadString,
            f"{self.srv_provider}/AttrReadString",
        )

        self.attr_enable_topic_srv_client = self.create_client(
            AttrEnableTopic,
            f"{self.srv_provider}/AttrEnableTopic",
        )

        self.attr_disable_topic_srv_client = self.create_client(
            AttrDisableTopic,
            f"{self.srv_provider}/AttrDisableTopic",
        )

        # Wait for the services to be available
        while not self.attr_read_string_srv_client.wait_for_service(timeout_sec=1.0) and \
                not self.attr_enable_topic_srv_client.wait_for_service(timeout_sec=1.0) and \
                not self.attr_disable_topic_srv_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for services to be available...")
        self.get_logger().info("Services are available.")

        # Topics controlling AD5592R device
        msg = AttrEnableTopic.Request()
        msg.attr_path = self.get_parameter("anode_raw").value
        msg.loop_rate = self.loop_rate
        self.attr_enable_topic_srv_client.call_async(msg)

        msg = AttrEnableTopic.Request()
        msg.attr_path = self.get_parameter("cathode_raw").value
        msg.loop_rate = self.loop_rate
        self.attr_enable_topic_srv_client.call_async(msg)

    def read_scale(self):
        request = AttrReadString.Request()
        request.attr_path = self.get_parameter("anode_scale").value
        future = self.attr_read_string_srv_client.call_async(request)
        future.state = "anode_scale"
        future.add_done_callback(self.read_scale_response_callback)

        request = AttrReadString.Request()
        request.attr_path = self.get_parameter("anode_scale").value
        future = self.attr_read_string_srv_client.call_async(request)
        future.state = "cathode_scale"
        future.add_done_callback(self.read_scale_response_callback)

    def read_scale_response_callback(self, future):
        print(future.state)
        try:
            response: AttrReadString.Response = future.result()
            if response.success:
                if future.state == "anode_scale":
                    self.scale_anode = float(response.message)
                elif future.state == "cathode_scale":
                    self.scale_cathode = float(response.message)
                else:
                    self.get_logger().error(
                        f"Invalid state: {future.state}. Cannot set scale.")
                    return
                self.get_logger().info(
                    f"Anode scale: {self.scale_anode}, Cathode scale: {self.scale_cathode}")
            else:
                self.get_logger().error(
                    f"Failed to read scale: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")

    def anode_data_callback(self, msg: Float64):
        """Volts to raw conversion."""
        if self.scale_anode is None:
            self.get_logger().error("Scale not set. Cannot convert data.")
            return

        mV = msg.data * 1_000
        raw_value = min(4095, int(mV / self.scale_anode))

        msg = String()
        msg.data = str(raw_value)
        self.get_logger().info(f"Writing to Anode: {msg.data}")
        self.anode_raw_write_pub.publish(msg)

    def cathode_data_callback(self, msg: Float64):
        """Volts to raw conversion."""
        if self.scale_cathode is None:
            self.get_logger().error("Scale not set. Cannot convert data.")
            return

        mV = msg.data * 1_000
        raw_value = min(4095, int(mV / self.scale_cathode))

        msg = String()
        msg.data = str(raw_value)
        self.get_logger().info(f"Writing to Cathode: {msg.data}")
        self.cathode_raw_write_pub.publish(msg)

    def destroy_node(self):
        # Disable the topic before shutting down
        self.get_logger().info("Disabling topic...")

        msg = AttrDisableTopic.Request()
        msg.topic_name = self.get_parameter("anode_raw").value
        self.get_logger().info(f"Topic name: {msg.topic_name}")
        self.attr_disable_topic_srv_client.call_async(msg)

        msg = AttrDisableTopic.Request()
        msg.topic_name = self.get_parameter("cathode_raw").value
        self.get_logger().info(f"Topic name: {msg.topic_name}")
        self.attr_disable_topic_srv_client.call_async(msg)

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Actuator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Channel Controller stopped by user')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
