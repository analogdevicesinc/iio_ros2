# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 Servo Feedback Node - ADALM-LSMSPG Demo

This node reads ADC values from the AD5592r via the adi_iio topic interface
to simulate position and current feedback from a servo motor. In a real
robotic arm application, these would come from encoders and current sensors.

Channels used:
  - ADC channel 5: Position feedback (simulating encoder)
  - Current feedback is optional; leave current_adc_raw empty to disable it
"""

import rclpy
from adi_iio.srv import AttrEnableTopic, AttrReadString
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64, String


class ServoFeedback(Node):
    """Reads ADC feedback and publishes sensor data via adi_iio topics."""

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
            'current_adc_raw',
            '',
            descriptor=ParameterDescriptor(
                description='Path to raw attribute of ADC channel for current feedback '
                            '(empty = no current sensing).'
            )
        )
        self.declare_parameter(
            'current_adc_scale',
            '',
            descriptor=ParameterDescriptor(
                description='Path to scale attribute of current ADC channel.'
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
        self.declare_parameter(
            'current_sense_resistor',
            47.0,
            descriptor=ParameterDescriptor(
                description='Current sense resistor value in ohms.'
            )
        )

        self.timer_period = float(self.get_parameter('timer_period').value)
        self.srv_provider = self.get_parameter('srv_provider').value
        self.qos = int(self.get_parameter('qos').value)
        self.max_voltage_mv = float(self.get_parameter('max_voltage_mv').value)
        self.max_angle = float(self.get_parameter('max_angle').value)
        self.r_sense = float(self.get_parameter('current_sense_resistor').value)

        self.position_scale = None
        self.current_scale = None
        self.position_raw = None
        self.current_raw = None
        self.last_cmd = 0.0
        self.has_current = bool(self.get_parameter('current_adc_raw').value)

        self.setup_service_clients()

        self.position_raw_sub = self.create_subscription(
            String,
            f"{self.get_parameter('position_adc_raw').value}/read",
            self.position_raw_callback,
            self.qos,
        )
        if self.has_current:
            self.current_raw_sub = self.create_subscription(
                String,
                f"{self.get_parameter('current_adc_raw').value}/read",
                self.current_raw_callback,
                self.qos,
            )

        self.cmd_sub = self.create_subscription(
            Float64,
            'servo/position_cmd',
            self.cmd_callback,
            self.qos,
        )

        self.joint_pub = self.create_publisher(JointState, 'servo/joint_state', self.qos)
        self.current_pub = self.create_publisher(Float64, 'servo/current_ma', self.qos)

        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        self.get_logger().info(
            f'Servo Feedback started at {1.0/self.timer_period:.1f} Hz'
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

        while not self.attr_read_string_client.wait_for_service(timeout_sec=1.0) and \
                not self.attr_enable_topic_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for adi_iio services...')
        self.get_logger().info('adi_iio services available.')

        self.read_scales()
        self.enable_adc_topics()

    def read_scales(self):
        request = AttrReadString.Request()
        request.attr_path = self.get_parameter('position_adc_scale').value
        future = self.attr_read_string_client.call_async(request)
        future.scale_type = 'position'
        future.add_done_callback(self.scale_response_callback)

        if self.has_current:
            request = AttrReadString.Request()
            request.attr_path = self.get_parameter('current_adc_scale').value
            future = self.attr_read_string_client.call_async(request)
            future.scale_type = 'current'
            future.add_done_callback(self.scale_response_callback)

    def scale_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                scale = float(response.message)
                if future.scale_type == 'position':
                    self.position_scale = scale
                    self.get_logger().info(f'Position ADC scale: {scale} mV/LSB')
                else:
                    self.current_scale = scale
                    self.get_logger().info(f'Current ADC scale: {scale} mV/LSB')
            else:
                self.get_logger().error(f'Failed to read scale: {response.message}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

    def enable_adc_topics(self):
        loop_rate = 1.0 / self.timer_period

        msg = AttrEnableTopic.Request()
        msg.attr_path = self.get_parameter('position_adc_raw').value
        msg.loop_rate = loop_rate
        self.attr_enable_topic_client.call_async(msg)

        if self.has_current:
            msg = AttrEnableTopic.Request()
            msg.attr_path = self.get_parameter('current_adc_raw').value
            msg.loop_rate = loop_rate
            self.attr_enable_topic_client.call_async(msg)

    def position_raw_callback(self, msg: String):
        try:
            self.position_raw = int(msg.data)
        except ValueError:
            self.get_logger().warn(f'Invalid position raw value: {msg.data}')

    def current_raw_callback(self, msg: String):
        try:
            self.current_raw = int(msg.data)
        except ValueError:
            self.get_logger().warn(f'Invalid current raw value: {msg.data}')

    def cmd_callback(self, msg: Float64):
        self.last_cmd = msg.data

    def voltage_to_angle(self, voltage_mv: float) -> float:
        """Convert voltage (mV) back to angle (degrees)."""
        return (voltage_mv / self.max_voltage_mv) * self.max_angle

    def voltage_to_current(self, voltage_mv: float) -> float:
        """Convert sense voltage to current in mA."""
        return voltage_mv / self.r_sense

    def timer_callback(self):
        if self.position_scale is None or (self.has_current and self.current_scale is None):
            self.get_logger().warn('Scales not yet available.')
            return
        if self.position_raw is None or (self.has_current and self.current_raw is None):
            self.get_logger().debug('Waiting for ADC readings...')
            return

        pos_voltage_mv = self.position_raw * self.position_scale
        measured_angle = self.voltage_to_angle(pos_voltage_mv)

        measured_current = 0.0
        if self.has_current:
            cur_voltage_mv = self.current_raw * self.current_scale
            measured_current = self.voltage_to_current(cur_voltage_mv)

        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ['servo_joint']
        joint_msg.position = [measured_angle * 3.14159 / 180.0]
        joint_msg.effort = [measured_current]
        self.joint_pub.publish(joint_msg)

        current_msg = Float64()
        current_msg.data = measured_current
        self.current_pub.publish(current_msg)

        error = self.last_cmd - measured_angle
        self.get_logger().info(
            f'Pos: {measured_angle:.1f} deg (cmd: {self.last_cmd:.1f}, err: {error:.1f}) | '
            f'Current: {measured_current:.2f} mA'
        )


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
