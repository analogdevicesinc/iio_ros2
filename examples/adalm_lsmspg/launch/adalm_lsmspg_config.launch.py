# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

"""
Launch file to configure AD5592R channels for servo demo.
Sets up DAC output (drive) on channel 4 and ADC input (position) on channel 5.
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import FindExecutable


def generate_launch_description():
    scale = 0.6103515629
    raw = 2048  # 1.25 V = motor stopped

    ch4_dac_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage4/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage4/raw', \
                value: {raw} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch5_adc_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage5/scale', \
                value: {scale} \
            }}\" ;"],
        ],
        shell=True,
    )

    return LaunchDescription([
        ch4_dac_cfg,
        ch5_adc_cfg,
    ])
