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

import os

from ament_index_python import get_package_share_directory
from launch_ros.actions import Node

import launch
from launch import LaunchDescription


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('adi_iio'),
        'config',
        'adi_iio.yaml'
    )

    adi_iio_node = Node(
        package='adi_iio',
        executable='adi_iio_node',
        name='adi_iio_node',
        output='screen',
        emulate_tty=True,
        parameters=[config],
        arguments=['--ros-args', '--log-level', 'debug'],
        on_exit=launch.actions.Shutdown(),
    )

    return LaunchDescription([
        adi_iio_node,
    ])
