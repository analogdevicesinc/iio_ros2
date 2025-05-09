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
    sampling_frequency = 19200
    scale = 0.000149011

    # voltage0-voltage1 configuration
    idx0_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage0-voltage1/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage0-voltage1/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage2-voltage3 configuration
    idx1_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage2-voltage3/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage2-voltage3/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage4-voltage5 configuration
    idx2_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage4-voltage5/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage4-voltage5/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # # voltage6-voltage7 configuration
    idx3_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage6-voltage7/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage6-voltage7/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage8-voltage9 configuration
    idx4_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage8-voltage9/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage8-voltage9/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage10-voltage11 configuration
    idx5_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage10-voltage11/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage10-voltage11/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage12-voltage13 configuration
    idx6_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage12-voltage13/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage12-voltage13/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    # voltage14-voltage15 configuration
    idx7_cfg = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage14-voltage15/scale', \
                value: {scale} \
            }}\" ;"],
            [FindExecutable(name='ros2'),
             ' service call ',
             ' /adi_iio_node/AttrWriteString adi_iio/srv/AttrWriteString  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage14-voltage15/sampling_frequency', \
                value: {sampling_frequency} \
            }}\" ;"],
        ],
        shell=True,
    )

    return LaunchDescription([
        idx0_cfg,
        idx1_cfg,
        idx2_cfg,
        idx3_cfg,
        idx4_cfg,
        idx5_cfg,
        idx6_cfg,
        idx7_cfg,
    ])
