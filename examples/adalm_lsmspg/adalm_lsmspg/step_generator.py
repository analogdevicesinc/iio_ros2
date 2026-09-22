# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 Step Generator Node - ADALM-LSMSPG Demo

Generates a step-function setpoint pattern for the PID controller,
stepping through a list of positions (or alternating between two) with a
configurable dwell time at each.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from std_msgs.msg import Float64


class StepGenerator(Node):
    """Alternates between two setpoints for PID closed-loop testing."""

    def __init__(self):
        super().__init__('step_generator')

        self.declare_parameter(
            'setpoint_a', 45.0,
            descriptor=ParameterDescriptor(
                description='First setpoint angle in degrees.'
            )
        )
        self.declare_parameter(
            'setpoint_b', 135.0,
            descriptor=ParameterDescriptor(
                description='Second setpoint angle in degrees.'
            )
        )
        self.declare_parameter(
            'setpoints', [0.0],
            descriptor=ParameterDescriptor(
                description='Optional list of angles (degrees) to cycle through, '
                            'one per dwell_time. Overrides setpoint_a/setpoint_b if it '
                            'has more than one entry.'
            )
        )
        self.declare_parameter(
            'dwell_time', 10.0,
            descriptor=ParameterDescriptor(
                description='Time in seconds to hold each setpoint.'
            )
        )
        self.declare_parameter(
            'setpoint_topic', 'servo/setpoint',
            descriptor=ParameterDescriptor(
                description='Topic to publish setpoint commands.'
            )
        )
        self.declare_parameter(
            'update_rate_hz', 10.0,
            descriptor=ParameterDescriptor(
                description='Rate at which to publish the setpoint.'
            )
        )
        self.declare_parameter('qos', 10)

        self.setpoint_a = float(self.get_parameter('setpoint_a').value)
        self.setpoint_b = float(self.get_parameter('setpoint_b').value)
        self.setpoints = [float(v) for v in self.get_parameter('setpoints').value]
        if len(self.setpoints) < 2:
            self.setpoints = [self.setpoint_a, self.setpoint_b]
        self.index = 0
        self.dwell_time = float(self.get_parameter('dwell_time').value)
        update_rate = float(self.get_parameter('update_rate_hz').value)
        qos = int(self.get_parameter('qos').value)

        self.setpoint_pub = self.create_publisher(
            Float64,
            self.get_parameter('setpoint_topic').value,
            qos,
        )

        self.time_in_state = 0.0
        self.timer_period = 1.0 / update_rate
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        self.get_logger().info(
            f'Step Generator started - alternating between '
            f'{len(self.setpoints)} setpoints {self.setpoints} deg '
            f'every {self.dwell_time:.1f} s'
        )

    def timer_callback(self):
        self.time_in_state += self.timer_period

        if self.time_in_state >= self.dwell_time:
            self.index = (self.index + 1) % len(self.setpoints)
            self.time_in_state = 0.0
            self.get_logger().info(
                f'Switching setpoint to {self.setpoints[self.index]:.1f} deg'
            )

        msg = Float64()
        msg.data = self.setpoints[self.index]
        self.setpoint_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = StepGenerator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Step Generator stopped')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
