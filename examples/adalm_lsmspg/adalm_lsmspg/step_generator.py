# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 Step Generator Node - ADALM-LSMSPG Demo

Generates a step-function setpoint pattern for the PID controller by cycling
through a list of positions (degrees), holding each for a configurable dwell time.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from std_msgs.msg import Float64


class StepGenerator(Node):
    """Cycles through a list of setpoints for PID closed-loop testing."""

    def __init__(self):
        super().__init__('step_generator')

        self.declare_parameter(
            'setpoints', [45.0, 135.0],
            descriptor=ParameterDescriptor(
                description='Angles (degrees) to cycle through, one per dwell_time.'
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

        self.setpoints = [float(v) for v in self.get_parameter('setpoints').value]
        if not self.setpoints:
            raise ValueError('step_generator: "setpoints" must not be empty')
        self.dwell_time = float(self.get_parameter('dwell_time').value)
        update_rate = float(self.get_parameter('update_rate_hz').value)
        qos = int(self.get_parameter('qos').value)

        self.index = 0
        self.setpoint_pub = self.create_publisher(
            Float64,
            self.get_parameter('setpoint_topic').value,
            qos,
        )

        self.last_switch = self.get_clock().now()
        self.timer = self.create_timer(1.0 / update_rate, self.timer_callback)

        self.get_logger().info(
            f'Step Generator started - cycling through {len(self.setpoints)} setpoints '
            f'{[round(v, 1) for v in self.setpoints]} deg every {self.dwell_time:.1f} s'
        )

    def timer_callback(self):
        now = self.get_clock().now()
        if (now - self.last_switch).nanoseconds * 1e-9 >= self.dwell_time:
            self.index = (self.index + 1) % len(self.setpoints)
            self.last_switch = now
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
