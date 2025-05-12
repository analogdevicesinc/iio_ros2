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

    idx0_volts = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            "run",
            "topic_tools transform",
            "ad7124_8/input_voltage0_voltage1/raw/read",    # Input topic
            "ad7124_8/input_voltage0_voltage1/volts",   # Output topic
            "std_msgs/Float64",
            "'std_msgs.msg.Float64(data=(float(m.data) * 0.000001164 / 1000))'",
            "--import std_msgs numpy",
        ],
        shell=True,
    )

    idx1_volts = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            "run",
            "topic_tools transform",
            "ad7124_8/input_voltage2_voltage3/raw/read",    # Input topic
            "ad7124_8/input_voltage2_voltage3/volts",   # Output topic
            "std_msgs/Float64",
            "'std_msgs.msg.Float64(data=(float(m.data) * 0.000001164 / 1000))'",
            "--import std_msgs numpy",
        ],
        shell=True,
    )

    return LaunchDescription([
        idx0_volts,
        idx1_volts,
    ])
