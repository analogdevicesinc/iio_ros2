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

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import FindExecutable


def generate_launch_description():
    scale = 0.6103515629
    raw = 0

    # CH0 configuration
    ch0_output_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage0/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage0/raw', \
                value: {raw} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch1_input_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage1/scale', \
                value: {scale} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch2_input_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage2/scale', \
                value: {scale} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch2_output_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage2/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage2/raw', \
                value: {raw} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch3_input_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage3/scale', \
                value: {scale} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch3_output_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage3/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/output_voltage3/raw', \
                value: {raw} \
            }}\" ;"],
        ],
        shell=True,
    )

    ch4_input_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad5592r/input_voltage4/scale', \
                value: {scale} \
            }}\" ;"],
        ],
        shell=True,
    )
    return LaunchDescription([
        ch0_output_cfg,
        ch1_input_cfg,
        ch2_input_cfg,
        ch2_output_cfg,
        ch3_input_cfg,
        ch3_output_cfg,
        ch4_input_cfg
    ])
