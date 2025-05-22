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

import copy
import threading
import time

import rclpy
from adi_iio.srv import (AttrReadString, AttrWriteString, BufferCreate,
                         BufferDestroy, BufferDisableTopic, BufferEnableTopic)
from rclpy.callback_groups import (MutuallyExclusiveCallbackGroup,
                                   ReentrantCallbackGroup)
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import Int32MultiArray


class Conversion(Node):
    def __init__(self):
        super().__init__("ad7124_8_buffer_scaled")
        self.lock = threading.Lock()
        self.conversion_available = False

        self.qos_profile = QoSProfile(depth=10)
        self.srv_provider = "/adi_iio_node"

        self.declare_parameter('device_path', 'ad7124-8')
        self.declare_parameter(
            'channels', 'input_voltage0-voltage1,input_voltage2-voltage3')
        self.declare_parameter('sampling_frequency', '1000')
        self.declare_parameter('scale', '0.000149011')
        self.declare_parameter('samples_count', 256)
        self.declare_parameter('loop_rate', 1.0)
        self.declare_parameter('topic_name', 'ad7124_8')

        self.device_path = self.get_parameter('device_path').value
        self.topic_name = str(f"/{self.get_parameter('topic_name').value}")

        channels = self.get_parameter('channels').value
        self.channels = [ch.strip() for ch in channels.split(',')]
        self.sampling_frequency = str(
            self.get_parameter('sampling_frequency').value)
        self.scale = str(self.get_parameter('scale').value)
        self.samples_count = int(self.get_parameter('samples_count').value)

        self.loop_rate = float(self.get_parameter('loop_rate').value)

        self.chn_scales = []

        self.buffer_create_client = None
        self.buffer_destroy_client = None
        self.buffer_enable_topic_client = None
        self.buffer_disable_topic_client = None
        self.attr_write_string_client = None
        self.attr_read_string_client = None

        self.reentrant_group = ReentrantCallbackGroup()

        self.one_shot_setup_timer = self.create_timer(
            0.1,
            self.setup_timer_callback,
            callback_group=MutuallyExclusiveCallbackGroup()
        )
        self.pub_timer = None

        self.scaled_data_msg: Int32MultiArray = Int32MultiArray()

    def setup_timer_callback(self):
        self.get_logger().info(f"Setting up: {self.get_name()} ... ")

        self.setup_service_clients()
        while not self.buffer_create_client.wait_for_service(timeout_sec=1.0) \
                or not self.buffer_destroy_client.wait_for_service(timeout_sec=1.0) \
                or not self.buffer_enable_topic_client.wait_for_service(timeout_sec=1.0) \
                or not self.buffer_disable_topic_client.wait_for_service(timeout_sec=1.0) \
                or not self.attr_read_string_client.wait_for_service(timeout_sec=1.0) \
                or not self.attr_write_string_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Waiting for services to be available ...")
            time.sleep(1.0)

        self.get_logger().info("Creating buffer ...")
        request = self.compose_buffer_create_request(
            device_path=self.device_path,
            channels=self.channels,
            samples_count=self.samples_count
        )
        response = self.buffer_create_client.call(request)
        self.get_logger().info(f"Buffer created: {response.message}")

        self.get_logger().info(f"Enabling buffer topic: {self.topic_name} ...")
        request = self.compose_buffer_enable_topic_request(
            device_path=self.device_path,
            topic_name=self.topic_name,
            loop_rate=self.loop_rate,
        )
        response = self.buffer_enable_topic_client.call(request)

        self.get_logger().info("Reading channel scales ...")
        for channel in self.channels:
            chn_path = f"{self.device_path}/{channel}"

            attr_path = f"{chn_path}/sampling_frequency"
            request = self.compose_attr_write_string(
                attr_path, self.sampling_frequency)
            response: AttrWriteString.Response = self.attr_write_string_client.call(
                request)
            self.get_logger().info(
                f"Setting sampling frequency for {channel}: {self.sampling_frequency}")

            attr_path = f"{chn_path}/scale"
            request = self.compose_attr_write_string(attr_path, self.scale)
            response: AttrWriteString.Response = self.attr_write_string_client.call(
                request)
            self.get_logger().info(
                f"Setting scale for {channel}: {self.scale}")

            request = self.compose_attr_read_string(attr_path)
            response: AttrReadString.Response = self.attr_read_string_client.call(
                request)

            try:
                scale_value = float(response.message)
                self.chn_scales.append(scale_value)
                self.get_logger().info(
                    f"Storing scale for {channel}: {scale_value}")
            except ValueError:
                self.get_logger().warn(
                    f"Invalid scale value received for {channel}: {response.message}")

        # Subscribe to buffer topic
        self.get_logger().info("Subscribing to buffer topic ...")
        self.sub_raw_buffer_topic = self.create_subscription(
            Int32MultiArray,
            self.topic_name,
            self.scale_buffer_data_callback,
            10,
            callback_group=self.reentrant_group
        )

        self.get_logger().info(
            f"Setting up scaled topic publish: {self.topic_name}/mV ...")
        self.pub_scaled_buffer_topic = self.create_publisher(
            Int32MultiArray,
            f"{self.topic_name}/mV",
            10,
            callback_group=self.reentrant_group
        )

        self.get_logger().info("Setup complete ... entering main loop ...")
        self.one_shot_setup_timer.cancel()
        self.pub_timer = self.create_timer(
            1.0 / self.loop_rate,
            self.publish_scaled_data,
            callback_group=self.reentrant_group
        )

    def setup_service_clients(self):
        self.buffer_create_client = self.create_client(
            BufferCreate,
            f"{self.srv_provider}/BufferCreate",
        )

        self.buffer_destroy_client = self.create_client(
            BufferDestroy,
            f"{self.srv_provider}/BufferDestroy",
        )

        self.buffer_enable_topic_client = self.create_client(
            BufferEnableTopic,
            f"{self.srv_provider}/BufferEnableTopic",
        )

        self.buffer_disable_topic_client = self.create_client(
            BufferDisableTopic,
            f"{self.srv_provider}/BufferDisableTopic",
        )

        self.attr_read_string_client = self.create_client(
            AttrReadString,
            f"{self.srv_provider}/AttrReadString",
        )

        self.attr_write_string_client = self.create_client(
            AttrWriteString,
            f"{self.srv_provider}/AttrWriteString",
        )

    def scale_buffer_data_callback(self, msg: Int32MultiArray):
        with self.lock:
            self.get_logger().info("Buffer scale conversion callback ...")

            data = msg.data
            scaled_data = map(
                # raw -> mV
                lambda x: int(x * self.chn_scales[x % len(self.chn_scales)]),
                data
            )
            scaled_data = list(scaled_data)

            self.scaled_data_msg.layout = copy.deepcopy(msg.layout)
            self.scaled_data_msg.data = scaled_data

            self.conversion_available = True

    def publish_scaled_data(self):
        with self.lock:
            if not self.conversion_available:
                return

            self.get_logger().info("Publishing scaled data ...")
            self.pub_scaled_buffer_topic.publish(self.scaled_data_msg)
            self.conversion_available = False

    def compose_buffer_create_request(
        self,
        device_path: str,
        channels: str,
        samples_count: int,
    ) -> BufferCreate.Request:
        request = BufferCreate.Request()
        request.device_path = device_path
        request.samples_count = samples_count
        request.channels = channels
        return request

    def compose_buffer_destroy_request(
        self,
        device_path: str
    ) -> BufferDestroy.Request:
        request = BufferDestroy.Request()
        request.device_path = device_path
        return request

    def compose_buffer_enable_topic_request(
        self,
        device_path: str,
        topic_name: str,
        loop_rate: float = 1,
    ) -> BufferEnableTopic.Request:
        request = BufferEnableTopic.Request()
        request.device_path = device_path
        request.topic_name = topic_name
        request.loop_rate = loop_rate
        return request

    def compose_buffer_disable_topic_request(
        self,
        device_path: str,
    ) -> BufferDisableTopic.Request:
        request = BufferDisableTopic.Request()
        request.device_path = device_path
        return request

    def compose_attr_write_string(
        self,
        attr_path: str,
        value: str
    ) -> AttrWriteString.Request:
        request = AttrWriteString.Request()
        request.attr_path = attr_path
        request.value = value
        return request

    def compose_attr_read_string(
        self,
        attr_path: str
    ) -> AttrReadString.Request:
        request = AttrReadString.Request()
        request.attr_path = attr_path
        return request

    def destroy_node(self):
        self.get_logger().info(f"Destroying {self.get_name()} ...")

        request = self.compose_buffer_destroy_request(
            device_path=self.device_path
        )
        self.buffer_destroy_client.call_async(request)

        request = self.compose_buffer_disable_topic_request(
            device_path=self.device_path
        )
        self.buffer_disable_topic_client.call_async(request)

        result = super().destroy_node()
        self.get_logger().info(f"{self.get_name()} destroyed successfully.")
        return result


def main(args=None):
    rclpy.init(args=args)
    node = Conversion()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt received ... shutting down")
    finally:
        node.destroy_node()
        executor.remove_node(node)
        rclpy.shutdown()


if __name__ == "__main__":
    main()
