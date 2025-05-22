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


def generate_launch_description():
    loop_rate: float = 1  # Hz

    adi_iio_node = Node(
        package='adi_iio',
        executable='adi_iio_node',
        name='adi_iio_node',
        output='screen',
        emulate_tty=True,
        parameters=[{
            "uri": "local:"
        }],
    )

    dell_precision_5530_node = Node(
        package='hwmon',
        executable='dell_precision_5530',
        name='dell_precision_5530',
        namespace='dell_precision_5530',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'loop_rate': loop_rate,
        }]
    )

    return LaunchDescription([
        adi_iio_node,
        dell_precision_5530_node,
    ])
