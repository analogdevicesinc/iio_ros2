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
    loop_rate = 1.0

    idx0_topic = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
                ' service call ',
             ' /adi_iio_node/AttrEnableTopic adi_iio/srv/AttrEnableTopic  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage0-voltage1/raw', \
                loop_rate: {loop_rate} \
            }}\" ;"],
        ],
        shell=True,
    )

    idx1_topic = ExecuteProcess(
        cmd=[
            [FindExecutable(name='ros2'),
                ' service call ',
             ' /adi_iio_node/AttrEnableTopic adi_iio/srv/AttrEnableTopic  ',
             f"\"{{ \
                attr_path: 'ad7124-8/input_voltage2-voltage3/raw', \
                loop_rate: {loop_rate} \
            }}\" ;"],
        ],
        shell=True,
    )

    return LaunchDescription([
        idx0_topic,
        idx1_topic,
    ])
