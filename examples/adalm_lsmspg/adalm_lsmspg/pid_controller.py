# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
ROS2 PID Controller Node - ADALM-LSMSPG Demo

Closes the servo control loop (DAC level = motor drive, midpoint = stopped)
by subscribing to a position setpoint and
joint-state feedback, computing a PID output, and publishing the corrected
position command to the ServoCommander.

Topic graph:
  /servo/setpoint  -->  PIDController  -->  /servo/position_cmd
                            ^
                            |
                   /servo/joint_state
"""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node, ParameterDescriptor
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64, Float64MultiArray


class PIDController(Node):
    """PID position controller for the ADALM-LSMSPG servo."""

    def __init__(self):
        super().__init__('pid_controller')

        self.declare_parameter(
            'kp', 1.0,
            descriptor=ParameterDescriptor(description='Proportional gain.')
        )
        self.declare_parameter(
            'ki', 0.1,
            descriptor=ParameterDescriptor(description='Integral gain.')
        )
        self.declare_parameter(
            'kd', 0.05,
            descriptor=ParameterDescriptor(description='Derivative gain.')
        )
        self.declare_parameter(
            'output_min', 0.0,
            descriptor=ParameterDescriptor(
                description='Minimum controller output (degrees).'
            )
        )
        self.declare_parameter(
            'output_max', 180.0,
            descriptor=ParameterDescriptor(
                description='Maximum controller output (degrees).'
            )
        )
        self.declare_parameter(
            'midpoint', 90.0,
            descriptor=ParameterDescriptor(
                description='Output that corresponds to "motor stopped" (degrees, 1.25 V).'
            )
        )
        self.declare_parameter(
            'sign', 1.0,
            descriptor=ParameterDescriptor(
                description='Set to -1.0 if more drive moves the feedback the wrong way.'
            )
        )
        self.declare_parameter(
            'integral_max', 50.0,
            descriptor=ParameterDescriptor(
                description='Anti-windup clamp on integral term (degrees).'
            )
        )
        self.declare_parameter(
            'update_rate_hz', 20.0,
            descriptor=ParameterDescriptor(
                description='Control loop frequency in Hz.'
            )
        )
        self.declare_parameter(
            'setpoint_topic', 'servo/setpoint',
            descriptor=ParameterDescriptor(
                description='Topic to receive setpoint commands (degrees).'
            )
        )
        self.declare_parameter(
            'feedback_topic', 'servo/joint_state',
            descriptor=ParameterDescriptor(
                description='Topic to receive joint-state feedback.'
            )
        )
        self.declare_parameter(
            'command_topic', 'servo/position_cmd',
            descriptor=ParameterDescriptor(
                description='Topic to publish corrected position commands (degrees).'
            )
        )
        self.declare_parameter('qos', 10)

        qos = int(self.get_parameter('qos').value)
        update_rate = float(self.get_parameter('update_rate_hz').value)

        self.setpoint = None
        self.measured_deg = None
        self.error_integral = 0.0
        self.prev_error = 0.0
        self.prev_setpoint = None

        self.create_subscription(
            Float64,
            self.get_parameter('setpoint_topic').value,
            self.setpoint_callback,
            qos,
        )
        self.create_subscription(
            JointState,
            self.get_parameter('feedback_topic').value,
            self.feedback_callback,
            qos,
        )

        self.cmd_pub = self.create_publisher(
            Float64,
            self.get_parameter('command_topic').value,
            qos,
        )
        self.pid_state_pub = self.create_publisher(
            Float64MultiArray,
            'servo/pid_state',
            qos,
        )

        self.dt = 1.0 / update_rate
        self.timer = self.create_timer(self.dt, self.control_loop)

        self.get_logger().info(
            f'PID Controller started at {update_rate:.0f} Hz '
            f'(kp={self.get_parameter("kp").value}, '
            f'ki={self.get_parameter("ki").value}, '
            f'kd={self.get_parameter("kd").value})'
        )

    def setpoint_callback(self, msg: Float64):
        if self.prev_setpoint is not None and msg.data != self.prev_setpoint:
            self.error_integral = 0.0
        self.prev_setpoint = msg.data
        self.setpoint = msg.data

    def feedback_callback(self, msg: JointState):
        if msg.position:
            self.measured_deg = msg.position[0] * 180.0 / math.pi

    def control_loop(self):
        if self.setpoint is None or self.measured_deg is None:
            return

        kp = float(self.get_parameter('kp').value)
        ki = float(self.get_parameter('ki').value)
        kd = float(self.get_parameter('kd').value)
        output_min = float(self.get_parameter('output_min').value)
        output_max = float(self.get_parameter('output_max').value)
        integral_max = float(self.get_parameter('integral_max').value)
        midpoint = float(self.get_parameter('midpoint').value)
        sign = float(self.get_parameter('sign').value)

        error = self.setpoint - self.measured_deg

        self.error_integral += error * self.dt
        self.error_integral = max(-integral_max, min(integral_max, self.error_integral))

        error_derivative = (error - self.prev_error) / self.dt
        self.prev_error = error

        p_term = kp * error
        i_term = ki * self.error_integral
        d_term = kd * error_derivative
        output = midpoint + sign * (p_term + i_term + d_term)
        output_clamped = max(output_min, min(output_max, output))

        cmd_msg = Float64()
        cmd_msg.data = output_clamped
        self.cmd_pub.publish(cmd_msg)

        state_msg = Float64MultiArray()
        state_msg.data = [error, p_term, i_term, d_term, output_clamped]
        self.pid_state_pub.publish(state_msg)

        self.get_logger().info(
            f'SP: {self.setpoint:.1f} | Meas: {self.measured_deg:.1f} | '
            f'Err: {error:.2f} | Out: {output_clamped:.1f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = PIDController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('PID Controller stopped')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
