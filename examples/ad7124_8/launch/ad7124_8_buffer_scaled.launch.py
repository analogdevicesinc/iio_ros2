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

    adi_iio_node = Node(
        package='adi_iio',
        executable='adi_iio_node',
        name='adi_iio_node',
        output='screen',
        emulate_tty=True,
        parameters=[{
            "uri": "ip:10.76.84.244"
        }],
    )

    buffer_scale_node = Node(
        package='ad7124_8',
        executable='ad7124_8_buffer_scaled',
        name='ad7124_8_buffer_scaled',
        namespace='ad7124_8_buffer_scaled',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'device_path': 'ad7124-8',
            'channels':  'input_voltage0-voltage1,input_voltage2-voltage3',
            'sampling_frequency': '1000',
            'scale': '0.000149011',
            'samples_count': 400,
            'loop_rate': 1.0,
            'topic_name': 'ad7124_8',
        }]
    )

    return LaunchDescription([
        adi_iio_node,
        buffer_scale_node,
    ])
