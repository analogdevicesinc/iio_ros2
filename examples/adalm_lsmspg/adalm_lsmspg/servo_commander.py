# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 Servo Commander Node - ADALM-LSMSPG Demo

This node subscribes to position commands (in degrees) and writes corresponding
DAC values to the AD5592r via the adi_iio service/topic interface. It simulates
commanding a servo motor position in a robotic arm application.

The DAC channel (CH4) outputs a drive level: 0-180 degrees mapped to 0-2.5V,
with the midpoint (90 degrees, 1.25 V) meaning motor stopped.
"""

import rclpy
from adi_iio.srv import AttrDisableTopic, AttrEnableTopic, AttrReadString, AttrWriteString
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Float64, String


class ServoCommander(Node):
    """Writes servo position commands to DAC via adi_iio topics."""

    def __init__(self):
        super().__init__('servo_commander')

        self.declare_parameter('loop_rate', 20.0)
        self.declare_parameter('srv_provider', '/adi_iio_node')
        self.declare_parameter('qos', 10)

        self.declare_parameter(
            'dac_raw',
            'ad5592r/output_voltage4/raw',
            descriptor=ParameterDescriptor(
                description='Path to raw attribute of AD5592R DAC channel for servo control.'
            )
        )
        self.declare_parameter(
            'dac_scale',
            'ad5592r/output_voltage4/scale',
            descriptor=ParameterDescriptor(
                description='Path to scale attribute of AD5592R DAC channel.'
            )
        )
        self.declare_parameter(
            'position_topic',
            'servo/position_cmd',
            descriptor=ParameterDescriptor(
                description='Topic to receive position commands (degrees).'
            )
        )
        self.declare_parameter(
            'min_angle',
            0.0,
            descriptor=ParameterDescriptor(
                description='Minimum servo angle in degrees.'
            )
        )
        self.declare_parameter(
            'max_angle',
            180.0,
            descriptor=ParameterDescriptor(
                description='Maximum servo angle in degrees.'
            )
        )
        self.declare_parameter(
            'max_voltage_mv',
            2500.0,
            descriptor=ParameterDescriptor(
                description='Maximum output voltage in millivolts.'
            )
        )

        self.loop_rate = float(self.get_parameter('loop_rate').value)
        self.srv_provider = self.get_parameter('srv_provider').value
        self.qos = int(self.get_parameter('qos').value)
        self.min_angle = float(self.get_parameter('min_angle').value)
        self.max_angle = float(self.get_parameter('max_angle').value)
        self.max_voltage_mv = float(self.get_parameter('max_voltage_mv').value)

        self.scale = None

        self.setup_service_clients()

        self.position_sub = self.create_subscription(
            Float64,
            self.get_parameter('position_topic').value,
            self.position_callback,
            self.qos,
        )

        self.dac_write_pub = self.create_publisher(
            String,
            f"{self.get_parameter('dac_raw').value}/write",
            self.qos,
        )

        self.read_scale()
        self.get_logger().info(
            f'Servo Commander started - accepting commands on '
            f'{self.get_parameter("position_topic").value}'
        )

    def setup_service_clients(self):
        self.attr_read_string_client = self.create_client(
            AttrReadString,
            f'{self.srv_provider}/AttrReadString',
        )

        self.attr_enable_topic_client = self.create_client(
            AttrEnableTopic,
            f'{self.srv_provider}/AttrEnableTopic',
        )

        self.attr_disable_topic_client = self.create_client(
            AttrDisableTopic,
            f'{self.srv_provider}/AttrDisableTopic',
        )

        self.attr_write_string_client = self.create_client(
            AttrWriteString,
            f'{self.srv_provider}/AttrWriteString',
        )

        clients = (
            self.attr_read_string_client,
            self.attr_enable_topic_client,
            self.attr_disable_topic_client,
            self.attr_write_string_client,
        )
        while not all(c.wait_for_service(timeout_sec=1.0) for c in clients):
            self.get_logger().info('Waiting for adi_iio services...')
        self.get_logger().info('adi_iio services available.')

        msg = AttrEnableTopic.Request()
        msg.attr_path = self.get_parameter('dac_raw').value
        msg.loop_rate = self.loop_rate
        self.attr_enable_topic_client.call_async(msg)

    def read_scale(self):
        request = AttrReadString.Request()
        request.attr_path = self.get_parameter('dac_scale').value
        future = self.attr_read_string_client.call_async(request)
        future.add_done_callback(self.scale_response_callback)

    def scale_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.scale = float(response.message)
                self.get_logger().info(f'DAC scale: {self.scale} mV/LSB')
            else:
                self.get_logger().error(f'Failed to read scale: {response.message}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

    def angle_to_voltage_mv(self, angle_deg: float) -> float:
        """Convert angle (degrees) to voltage (mV)."""
        normalized = (angle_deg - self.min_angle) / (self.max_angle - self.min_angle)
        normalized = max(0.0, min(1.0, normalized))
        return normalized * self.max_voltage_mv

    def position_callback(self, msg: Float64):
        """Convert position command to DAC raw value and write."""
        if self.scale is None:
            self.get_logger().warn('Scale not yet available, skipping command.')
            return

        angle = msg.data
        voltage_mv = self.angle_to_voltage_mv(angle)
        raw_value = min(4095, max(0, int(voltage_mv / self.scale)))

        write_msg = String()
        write_msg.data = str(raw_value)
        self.dac_write_pub.publish(write_msg)

        self.get_logger().debug(
            f'Position: {angle:.1f} deg -> {voltage_mv:.0f} mV -> raw: {raw_value}'
        )

    def stop_motor(self):
        """Write the midpoint (motor stopped) and release the topic, waiting for both.

        Uses services (not the /write topic) so we know the write completed
        before the process exits.
        """
        if self.scale is not None:
            stop_raw = int(self.angle_to_voltage_mv(
                (self.min_angle + self.max_angle) / 2.0) / self.scale)
            write = AttrWriteString.Request()
            write.attr_path = self.get_parameter('dac_raw').value
            write.value = str(stop_raw)
            self.get_logger().info('Shutting down, setting DAC to midpoint (motor stopped)...')
            future = self.attr_write_string_client.call_async(write)
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            if not future.done():
                self.get_logger().error('Timed out writing stop value to the DAC!')

        disable = AttrDisableTopic.Request()
        disable.topic_name = self.get_parameter('dac_raw').value
        future = self.attr_disable_topic_client.call_async(disable)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)


def main(args=None):
    # Keep the context alive on SIGINT so stop_motor() can still call services.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = ServoCommander()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Servo Commander stopped by user')
    finally:
        node.stop_motor()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
