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

import time

import rclpy
from adi_iio.srv import AttrEnableTopic
from adi_iio.srv._attr_disable_topic import AttrDisableTopic
from rclpy.callback_groups import (MutuallyExclusiveCallbackGroup,
                                   ReentrantCallbackGroup)
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import Float64, Int32, String


class HWMon(Node):
    def __init__(self):
        super().__init__("hwmon")
        self.get_logger().info("Initializing HWMon...")

        self.declare_parameter('loop_rate', 1.0)
        self.loop_rate = float(self.get_parameter('loop_rate').value)

        self.srv_provider = "/adi_iio_node"

        self.enable_topic_client = None
        self.disable_topic_client = None
        self.sub_bat0_current = None
        self.pub_bat0_uA = None
        self.sub_bat0_voltage = None
        self.pub_bat0_V = None
        self.pub_coretemp_core0 = None
        self.sub_coretemp_core0 = None
        self.pub_coretemp_core1 = None
        self.sub_coretemp_core1 = None
        self.pub_coretemp_core2 = None
        self.sub_coretemp_core2 = None
        self.pub_coretemp_core3 = None
        self.sub_coretemp_core3 = None
        self.pub_cpu_fan = None
        self.sub_cpu_fan = None
        self.pub_gpu_fan = None
        self.sub_gpu_fan = None

        self.cb_group_bat0_current = None
        self.cb_group_bat0_voltage = None
        self.cb_group_coretemp = None
        self.cb_group_fans = None

        self.qos_profile = QoSProfile(depth=10)

        self.one_shot_setup_timer = self.create_timer(
            0.1,
            self.setup_timer_callback,
            callback_group=MutuallyExclusiveCallbackGroup()
        )
        self.timer = None

        self.data = {
            "BAT0": {
                "current": 0.0,
                "voltage": 0.0,
            },
            "coretemp": {
                "Core 0": 0.0,
                "Core 1": 0.0,
                "Core 2": 0.0,
                "Core 3": 0.0,
            },
            "dell_sm": {
                "CPU Fan": 0,
                "GPU Fan": 0
            }
        }

    def compose_attr_enable_topic_request(
        self,
        attr_path: str,
        topic_name: str = "",
        loop_rate: float = 1,
        type: int = 0
    ) -> AttrEnableTopic.Request:

        self.get_logger().debug(
            f"Creating request for {attr_path} with topic name {topic_name} and loop rate {loop_rate}")
        req = AttrEnableTopic.Request()
        req.attr_path = attr_path
        req.topic_name = topic_name
        req.loop_rate = loop_rate
        req.type = type
        return req

    def compose_attr_disable_topic_request(
        self,
        topic_name: str,
        type: int
    ) -> AttrDisableTopic.Request:
        request = AttrDisableTopic.Request()
        request.topic_name = topic_name
        request.type = type
        return request

    def attr_enable_topic(self, request: AttrEnableTopic.Request):
        future = self.enable_topic_client.call_async(request)

        # Poll for results
        while rclpy.ok() and future and not future.done():
            self.get_logger().debug("Waiting for service response...")
            time.sleep(0.1)

        if future and future.done():
            try:
                self.get_logger().debug("Getting service response...")
                response: AttrEnableTopic.Response = future.result()
            except Exception as e:
                self.get_logger().error(f"Service call failed: {e}")
                return False
        else:
            self.get_logger().warn("RCLPY shutdown before service call completed.")

        return response if response.success else False

    def setup_timer_callback(self):
        self.get_logger().info("Setting up /hwmon node...")

        self.setup_service_client()
        while not self.enable_topic_client.wait_for_service(timeout_sec=1.0) and \
                not self.disable_topic_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Waiting for services to be available ...")
            time.sleep(1.0)

        self.setup_bat0_current()
        self.setup_bat0_voltage()
        self.setup_core_temp()
        self.setup_fans()

        # Cancel the one-shot setup timer
        self.one_shot_setup_timer.cancel()
        self.get_logger().info("Setup complete ... entering main loop ...")

        # Prepare the main loop timer
        self.timer = self.create_timer(
            1.0 / self.loop_rate,
            self.timer_callback,
            callback_group=ReentrantCallbackGroup()
        )
        self.get_logger().info(
            f" node main loop started with loop rate: {self.loop_rate} Hz")

    def setup_service_client(self):
        self.enable_topic_client = self.create_client(
            AttrEnableTopic,
            f"{self.srv_provider}/AttrEnableTopic",
            callback_group=ReentrantCallbackGroup()
        )
        self.disable_topic_client = self.create_client(
            AttrDisableTopic,
            f"{self.srv_provider}/AttrDisableTopic",
            callback_group=ReentrantCallbackGroup()
        )

    def setup_bat0_current(self):
        self.cb_group_bat0_current = MutuallyExclusiveCallbackGroup()
        self.get_logger().info("Setting up /BAT0/uA topic ... ")
        request = self.compose_attr_enable_topic_request(
            attr_path="BAT0/curr1/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        response = self.attr_enable_topic(request)
        if response:
            self.get_logger().info(response.message)

        self.get_logger().info("Creating subscription ...")
        self.sub_bat0_current = self.create_subscription(
            String,
            "/BAT0/curr1/input/read",
            self.update_bat0_current,
            10,
            callback_group=self.cb_group_bat0_current
        )
        self.get_logger().info("Creating publisher ...")
        self.pub_bat0_uA = self.create_publisher(
            Float64,
            "/BAT0/uA",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_bat0_current
        )

    def setup_bat0_voltage(self):
        self.cb_group_bat0_voltage = MutuallyExclusiveCallbackGroup()
        self.get_logger().info("Setting up /BAT0/V topic ... ")
        request = self.compose_attr_enable_topic_request(
            attr_path="BAT0/in0/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        response = self.attr_enable_topic(request)
        if response:
            self.get_logger().info(response.message)

        self.get_logger().info("Creating subscription ...")
        self.sub_bat0_voltage = self.create_subscription(
            String,
            "/BAT0/in0/input/read",
            self.update_bat0_voltage,
            10,
            callback_group=self.cb_group_bat0_voltage
        )
        self.get_logger().info("Creating publisher ...")
        self.pub_bat0_V = self.create_publisher(
            Float64,
            "/BAT0/V",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_bat0_voltage
        )

    def setup_core_temp(self):
        self.cb_group_coretemp = MutuallyExclusiveCallbackGroup()
        self.get_logger().info("Setting up /coretemp topic ... ")

        request = self.compose_attr_enable_topic_request(
            attr_path="coretemp/temp2/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        self.attr_enable_topic(request)

        request = self.compose_attr_enable_topic_request(
            attr_path="coretemp/temp3/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        self.attr_enable_topic(request)

        request = self.compose_attr_enable_topic_request(
            attr_path="coretemp/temp4/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        self.attr_enable_topic(request)

        request = self.compose_attr_enable_topic_request(
            attr_path="coretemp/temp5/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        self.attr_enable_topic(request)

        # temp2 -> Core 0
        self.get_logger().info("Creating subscription ...")
        self.sub_coretemp_core0 = self.create_subscription(
            String,
            "/coretemp/temp2/input/read",
            self.update_coretemp_core0,
            10,
            callback_group=self.cb_group_coretemp
        )
        self.get_logger().info("Creating publisher ...")
        self.pub_coretemp_core0 = self.create_publisher(
            Float64,
            "/coretemp/core0",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_coretemp
        )

        # temp3 -> Core 1
        self.sub_coretemp_core1 = self.create_subscription(
            String,
            "/coretemp/temp3/input/read",
            self.update_coretemp_core1,
            10,
            callback_group=self.cb_group_coretemp
        )
        self.pub_coretemp_core1 = self.create_publisher(
            Float64,
            "/coretemp/core1",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_coretemp
        )

        # temp4 -> Core 2
        self.sub_coretemp_core2 = self.create_subscription(
            String,
            "/coretemp/temp4/input/read",
            self.update_coretemp_core2,
            10,
            callback_group=self.cb_group_coretemp
        )
        self.pub_coretemp_core2 = self.create_publisher(
            Float64,
            "/coretemp/core2",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_coretemp
        )

        # temp5 -> Core 3
        self.sub_coretemp_core3 = self.create_subscription(
            String,
            "/coretemp/temp5/input/read",
            self.update_coretemp_core3,
            10,
            callback_group=self.cb_group_coretemp
        )
        self.pub_coretemp_core3 = self.create_publisher(
            Float64,
            "/coretemp/core3",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_coretemp
        )

    def setup_fans(self):
        self.cb_group_fans = MutuallyExclusiveCallbackGroup()
        self.get_logger().info("Setting up /fan topic ... ")

        # CPU Fan
        request = self.compose_attr_enable_topic_request(
            attr_path="dell_smm/fan1/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        response = self.attr_enable_topic(request)
        if response:
            self.get_logger().info(response.message)

        self.get_logger().info("Creating subscription ...")
        self.sub_cpu_fan = self.create_subscription(
            String,
            "/dell_smm/fan1/input/read",
            self.update_cpu_fan,
            10,
            callback_group=self.cb_group_fans
        )
        self.get_logger().info("Creating publisher ...")
        self.pub_cpu_fan = self.create_publisher(
            Int32,
            "/fan/cpu",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_fans
        )

        # GPU Fan
        request = self.compose_attr_enable_topic_request(
            attr_path="dell_smm/fan2/input",
            loop_rate=self.loop_rate,
            type=0  # STRING
        )
        self.attr_enable_topic(request)
        self.get_logger().info("Creating subscription ...")
        self.sub_gpu_fan = self.create_subscription(
            String,
            "/dell_smm/fan2/input/read",
            self.update_gpu_fan,
            10,
            callback_group=self.cb_group_fans
        )
        self.get_logger().info("Creating publisher ...")
        self.pub_gpu_fan = self.create_publisher(
            Int32,
            "/fan/gpu",
            qos_profile=self.qos_profile,
            callback_group=self.cb_group_fans
        )

    def timer_callback(self):
        self.get_logger().info("Sending data ...")

        self.pub_bat0_uA.publish(
            msg=Float64(data=self.data["BAT0"]["current"])
        )
        self.pub_bat0_V.publish(
            msg=Float64(data=self.data["BAT0"]["voltage"])
        )

        self.pub_coretemp_core0.publish(
            msg=Float64(data=self.data["coretemp"]["Core 0"])
        )
        self.pub_coretemp_core1.publish(
            msg=Float64(data=self.data["coretemp"]["Core 1"])
        )
        self.pub_coretemp_core2.publish(
            msg=Float64(data=self.data["coretemp"]["Core 2"])
        )
        self.pub_coretemp_core3.publish(
            msg=Float64(data=self.data["coretemp"]["Core 3"])
        )

        self.pub_cpu_fan.publish(
            msg=Int32(data=self.data["dell_sm"]["CPU Fan"])
        )
        self.pub_gpu_fan.publish(
            msg=Int32(data=self.data["dell_sm"]["GPU Fan"])
        )

    def update_bat0_current(self, msg: String):
        data_mA = float(msg.data)
        data_uA = data_mA * 1000.0
        self.data["BAT0"]["current"] = float(data_uA)

    def update_bat0_voltage(self, msg: String):
        data_mV = float(msg.data)
        data_V = data_mV / 1000.0
        self.data["BAT0"]["voltage"] = float(data_V)

    def update_coretemp_core0(self, msg: String):
        data_mV = float(msg.data)
        data_V = data_mV / 1000.0
        self.data["coretemp"]["Core 0"] = float(data_V)

    def update_coretemp_core1(self, msg: String):
        data_mV = float(msg.data)
        data_V = data_mV / 1000.0
        self.data["coretemp"]["Core 1"] = float(data_V)

    def update_coretemp_core2(self, msg: String):
        data_mV = float(msg.data)
        data_V = data_mV / 1000.0
        self.data["coretemp"]["Core 2"] = float(data_V)

    def update_coretemp_core3(self, msg: String):
        data_mV = float(msg.data)
        data_V = data_mV / 1000.0
        self.data["coretemp"]["Core 3"] = float(data_V)

    def update_cpu_fan(self, msg: String):
        data_rpm = int(msg.data)
        self.data["dell_sm"]["CPU Fan"] = int(data_rpm)

    def update_gpu_fan(self, msg: String):
        data_rpm = int(msg.data)
        self.data["dell_sm"]["GPU Fan"] = int(data_rpm)

    def destroy_node(self):
        self.get_logger().info("Destroying node ...")
        request = self.compose_attr_disable_topic_request(
            topic_name="BAT0/curr1/input",
            type=0
        )
        self.disable_topic_client.call_async(request)

        request = self.compose_attr_disable_topic_request(
            topic_name="BAT0/in0/input",
            type=0
        )
        self.disable_topic_client.call_async(request)

        request = self.compose_attr_disable_topic_request(
            topic_name="coretemp/temp2/input",
            type=0
        )
        self.disable_topic_client.call_async(request)
        request = self.compose_attr_disable_topic_request(
            topic_name="coretemp/temp3/input",
            type=0
        )
        self.disable_topic_client.call_async(request)
        request = self.compose_attr_disable_topic_request(
            topic_name="coretemp/temp4/input",
            type=0
        )
        self.disable_topic_client.call_async(request)
        request = self.compose_attr_disable_topic_request(
            topic_name="coretemp/temp5/input",
            type=0
        )
        self.disable_topic_client.call_async(request)

        request = self.compose_attr_disable_topic_request(
            topic_name="dell_smm/fan1/input",
            type=0
        )
        self.disable_topic_client.call_async(request)
        request = self.compose_attr_disable_topic_request(
            topic_name="dell_smm/fan2/input",
            type=0
        )
        self.disable_topic_client.call_async(request)

        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HWMon()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt received ... shutting down")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
