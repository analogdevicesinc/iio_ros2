# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 Servo Feedback Node - ADALM-LSMSPG Demo

Reads the position potentiometer on AD5592R ADC channel 5 via the adi_iio
topic interface and publishes it as a sensor_msgs/JointState (radians).
In a real robotic arm this would be an encoder.
"""

import math

import rclpy
from adi_iio.srv import AttrEnableTopic, AttrReadString
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from sensor_msgs.msg import JointState
from std_msgs.msg import String


class ServoFeedback(Node):
    """Reads the position ADC and publishes it as a JointState."""

    def __init__(self):
        super().__init__('servo_feedback')

        self.declare_parameter('timer_period', 0.05)
        self.declare_parameter('srv_provider', '/adi_iio_node')
        self.declare_parameter('qos', 10)

        self.declare_parameter(
            'position_adc_raw',
            'ad5592r/input_voltage5/raw',
            descriptor=ParameterDescriptor(
                description='Path to raw attribute of ADC channel for position feedback.'
            )
        )
        self.declare_parameter(
            'position_adc_scale',
            'ad5592r/input_voltage5/scale',
            descriptor=ParameterDescriptor(
                description='Path to scale attribute of position ADC channel.'
            )
        )
        self.declare_parameter(
            'joint_state_topic',
            'servo/joint_state',
            descriptor=ParameterDescriptor(
                description='Topic on which the measured position is published.'
            )
        )
        self.declare_parameter(
            'max_voltage_mv',
            2500.0,
            descriptor=ParameterDescriptor(
                description='Maximum ADC voltage in millivolts (maps to max angle).'
            )
        )
        self.declare_parameter(
            'max_angle',
            180.0,
            descriptor=ParameterDescriptor(
                description='Maximum angle in degrees.'
            )
        )

        self.timer_period = float(self.get_parameter('timer_period').value)
        self.srv_provider = self.get_parameter('srv_provider').value
        self.qos = int(self.get_parameter('qos').value)
        self.max_voltage_mv = float(self.get_parameter('max_voltage_mv').value)
        self.max_angle = float(self.get_parameter('max_angle').value)

        self.position_scale = None
        self.position_raw = None

        self.setup_service_clients()

        self.position_raw_sub = self.create_subscription(
            String,
            f"{self.get_parameter('position_adc_raw').value}/read",
            self.position_raw_callback,
            self.qos,
        )

        self.joint_pub = self.create_publisher(
            JointState, self.get_parameter('joint_state_topic').value, self.qos)

        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        self.get_logger().info(
            f'Servo Feedback started at {1.0 / self.timer_period:.1f} Hz'
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

        clients = (self.attr_read_string_client, self.attr_enable_topic_client)
        while not all(c.wait_for_service(timeout_sec=1.0) for c in clients):
            self.get_logger().info('Waiting for adi_iio services...')
        self.get_logger().info('adi_iio services available.')

        # Read the ADC scale (mV/LSB) once.
        request = AttrReadString.Request()
        request.attr_path = self.get_parameter('position_adc_scale').value
        future = self.attr_read_string_client.call_async(request)
        future.add_done_callback(self.scale_response_callback)

        # Ask adi_iio_node to publish the raw ADC value at our rate.
        enable = AttrEnableTopic.Request()
        enable.attr_path = self.get_parameter('position_adc_raw').value
        enable.loop_rate = 1.0 / self.timer_period
        self.attr_enable_topic_client.call_async(enable)

    def scale_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.position_scale = float(response.message)
                self.get_logger().info(f'Position ADC scale: {self.position_scale} mV/LSB')
            else:
                self.get_logger().error(f'Failed to read scale: {response.message}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

    def position_raw_callback(self, msg: String):
        try:
            self.position_raw = int(msg.data)
        except ValueError:
            self.get_logger().warn(f'Invalid position raw value: {msg.data}')

    def voltage_to_angle(self, voltage_mv: float) -> float:
        """Convert voltage (mV) back to angle (degrees)."""
        return (voltage_mv / self.max_voltage_mv) * self.max_angle

    def timer_callback(self):
        if self.position_scale is None:
            self.get_logger().warn('Scale not yet available.', throttle_duration_sec=2.0)
            return
        if self.position_raw is None:
            self.get_logger().debug('Waiting for ADC readings...')
            return

        measured_angle = self.voltage_to_angle(self.position_raw * self.position_scale)

        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['servo_joint']
        joint_msg.position = [math.radians(measured_angle)]
        self.joint_pub.publish(joint_msg)

        self.get_logger().debug(f'Position: {measured_angle:.1f} deg')


def main(args=None):
    rclpy.init(args=args)
    node = ServoFeedback()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Servo Feedback stopped')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
