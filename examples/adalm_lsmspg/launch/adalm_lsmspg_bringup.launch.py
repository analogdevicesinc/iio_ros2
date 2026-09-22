# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
Main bringup launch file for ADALM-LSMSPG servo demo.
Launches configuration and demo nodes.
"""

import os

from ament_index_python import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('adalm_lsmspg')
    launch_dir = os.path.join(pkg_dir, 'launch')

    config_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'adalm_lsmspg_config.launch.py')
        ),
    )

    topics_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'adalm_lsmspg_topics.launch.py')
        ),
    )

    servo_commander_node = Node(
        package='adalm_lsmspg',
        executable='servo_commander',
        name='servo_commander',
        output='screen',
        parameters=[{
            'loop_rate': 20.0,
            'dac_raw': 'ad5592r/output_voltage4/raw',
            'dac_scale': 'ad5592r/output_voltage4/scale',
            'position_topic': 'servo/position_cmd',
            'min_angle': 0.0,
            'max_angle': 180.0,
            'max_voltage_mv': 2500.0,
        }],
    )

    servo_feedback_node = Node(
        package='adalm_lsmspg',
        executable='servo_feedback',
        name='servo_feedback',
        output='screen',
        parameters=[{
            'timer_period': 0.05,
            'position_adc_raw': 'ad5592r/input_voltage5/raw',
            'position_adc_scale': 'ad5592r/input_voltage5/scale',
            'current_adc_raw': '',
            'current_adc_scale': '',
            'max_voltage_mv': 2500.0,
            'max_angle': 180.0,
            'current_sense_resistor': 47.0,
        }],
    )

    pid_controller_node = Node(
        package='adalm_lsmspg',
        executable='pid_controller',
        name='pid_controller',
        output='screen',
        parameters=[{
            'kp': 1.0,
            'ki': 0.1,
            'kd': 0.05,
            'midpoint': 90.0,
            'sign': 1.0,
            'output_min': 0.0,
            'output_max': 180.0,
            'integral_max': 50.0,
            'update_rate_hz': 20.0,
            'setpoint_topic': 'servo/setpoint',
            'feedback_topic': 'servo/joint_state',
            'command_topic': 'servo/position_cmd',
        }],
    )

    step_generator_node = Node(
        package='adalm_lsmspg',
        executable='step_generator',
        name='step_generator',
        output='screen',
        parameters=[{
            # 625..1825 mV in 200 mV steps (same sweep as silly_servo.py),
            # converted to degrees: 0-2500 mV <-> 0-180 deg
            'setpoints': [mv * 180.0 / 2500.0 for mv in range(625, 1875, 200)],
            'dwell_time': 1.0,
            'setpoint_topic': 'servo/setpoint',
            'update_rate_hz': 10.0,
        }],
    )

    delayed_nodes = TimerAction(
        period=2.0,
        actions=[
            servo_commander_node,
            servo_feedback_node,
            pid_controller_node,
            step_generator_node,
        ],
    )

    return LaunchDescription([
        config_launch,
        topics_launch,
        delayed_nodes,
    ])
