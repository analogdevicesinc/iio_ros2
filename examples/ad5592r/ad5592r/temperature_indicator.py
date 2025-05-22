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
from adi_iio.srv import AttrEnableTopic, AttrReadString
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import String


class TemperatureIndicator(Node):
    def __init__(self):
        super().__init__("temperature_indicator")

        self.declare_parameter('timer_period', 1.0)
        self.declare_parameter("srv_provider", "/adi_iio_node")
        self.declare_parameter("qos", 10)

        self.timer_period = float(self.get_parameter('timer_period').value)
        self.srv_provider = self.get_parameter('srv_provider').value
        self.qos = int(self.get_parameter('qos').value)

        self.offset: int = None
        self.raw: int = None
        self.scale: float = 1.0

        self.temperature_statistics = VarianceWelford()

        self.enable_topic_client = self.create_client(
            AttrEnableTopic,
            f"{self.srv_provider}/AttrEnableTopic"
        )
        self.attr_read_string_srv_client = self.create_client(
            AttrReadString,
            f"{self.srv_provider}/AttrReadString"
        )
        self.wait_for_services()

        # One time reading
        self.read_scale()
        # Periodic reading
        self.enable_attr_topic("raw")
        self.raw_subscriber = self.create_subscription(
            String,
            "ad5592r/temp/raw/read",
            self.raw_attr_callback,
            self.qos
        )
        self.enable_attr_topic("offset")
        self.offset_subscriber = self.create_subscription(
            String,
            "ad5592r/temp/offset/read",
            self.offset_attr_callback,
            self.qos
        )

        self.temperature_publisher = self.create_publisher(
            Temperature,
            "/temperature",
            self.qos
        )

        self.timer = self.create_timer(
            self.timer_period,
            self.timer_callback
        )

    def wait_for_services(self):
        while not self.enable_topic_client.wait_for_service(timeout_sec=1.0) and \
                not self.attr_read_string_srv_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for services to be available...")
        self.get_logger().info("Services are available.")

    def enable_attr_topic(self, attr: str):
        request = AttrEnableTopic.Request()
        request.attr_path = "ad5592r/temp/" + attr
        request.topic_name = "ad5592r/temp/" + attr
        request.loop_rate = 1 / float(self.timer_period)
        request.type = 0  # STRING

        future = self.enable_topic_client.call_async(request)
        future.add_done_callback(self.enable_topic_response_callback)

    def enable_topic_response_callback(self, future):
        try:
            response: AttrEnableTopic.Response = future.result()
            if response.success:
                self.get_logger().info("Successfully enabled topic.")
            else:
                self.get_logger().error(
                    f"Failed to enable topic: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")

    def read_scale(self):
        future = self.read_attr("ad5592r/temp/scale")
        future.add_done_callback(self.read_scale_response_callback)

    def read_attr(self, attr_path: str):
        request = AttrReadString.Request()
        request.attr_path = attr_path
        future = self.attr_read_string_srv_client.call_async(request)
        return future

    def read_scale_response_callback(self, future):
        try:
            response: AttrReadString.Response = future.result()
            if response.success:
                self.get_logger().info(
                    f"Successfully read scale: {response.message}")
                self.scale = float(response.message)
            else:
                self.get_logger().error(
                    f"Failed to read scale: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")

    def raw_attr_callback(self, msg: String):
        self.get_logger().info(f"Raw value: {msg.data}")
        self.raw = int(msg.data)

    def offset_attr_callback(self, msg: String):
        self.get_logger().info(f"Offset value: {msg.data}")
        self.offset = float(msg.data)

    def timer_callback(self):
        if self.offset is None or self.raw is None:
            self.get_logger().warn("Offset or raw values are still missing.")
            return

        temperature = self.compute_temperature(
            self.raw, self.offset, self.scale)
        self.temperature_statistics.update(temperature)

        temperature_msg = Temperature()
        temperature_msg.temperature = self.temperature_statistics.mean()
        temperature_msg.variance = self.temperature_statistics.variance()
        temperature_msg.header.stamp = self.get_clock().now().to_msg()

        self.temperature_publisher.publish(temperature_msg)

    def compute_temperature(self, raw: int, offset: int, scale: float = 1.0) -> float:
        temp_mDegC = (raw + offset) * scale
        temp_degC = temp_mDegC / 1000
        return temp_degC


class VarianceWelford:
    def __init__(self):
        self._n = 0  # number of measurements
        self._mean = 0.0  # running mean
        self.M2 = 0.0  # sum of squares of differences from the current mean

    def update(self, x: float):
        """Incorporate a new measurement into the running variance computation."""
        self._n += 1
        delta1 = x - self._mean
        self._mean += delta1 / self._n
        delta2 = x - self._mean
        self.M2 += delta1 * delta2

    def variance(self) -> float:
        """Return the biased sample variance."""
        if self._n < 2:
            return float('nan')
        return self.M2 / (self._n - 1)

    def mean(self) -> float:
        """Return the current running mean."""
        return self._mean


def main(args=None):
    rclpy.init(args=args)
    node = TemperatureIndicator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info("Shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
