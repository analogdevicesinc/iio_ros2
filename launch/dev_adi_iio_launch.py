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

from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():

    enable_service = ExecuteProcess(
        cmd=[[
            'ros2 service call ',
            '/sensor/AttrEnableTopic ',
            'adi_iio_interfaces/srv/AttrEnableTopic ',
            '"{attr_path: \'ad5625/voltage1/powerdown_mode\'}"'
        ]],
        shell=True
    )

    adi_iio_node = Node(
        package='adi_iio',
        executable='adi_iio_node',
        name='sensor',
        output='screen',
        emulate_tty=True,
        parameters=[
                {'uri': 'ip:192.168.2.1'}],
        arguments=['--ros-args', '--log-level', 'debug']

    )

    return LaunchDescription([
        adi_iio_node,
        enable_service
    ])
