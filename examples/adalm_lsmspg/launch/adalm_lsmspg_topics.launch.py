# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
Launch file to enable IIO attribute topics for servo demo.
Enables DAC output (CH4) and position ADC input (CH5) topics.
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import FindExecutable


def generate_launch_description():
    loop_rate = 20.0

    ch4_dac_topic = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrEnableTopic adi_iio/srv/AttrEnableTopic ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage4/raw', \
                loop_rate: {loop_rate} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch5_adc_topic = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrEnableTopic adi_iio/srv/AttrEnableTopic ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage5/raw', \
                loop_rate: {loop_rate} \
            }}\" ;"],
        ],
        shell=True,
    )

    return LaunchDescription([
        ch4_dac_topic,
        ch5_adc_topic,
    ])
