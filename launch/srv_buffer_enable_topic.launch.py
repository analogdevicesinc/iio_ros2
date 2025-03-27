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
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                            OpaqueFunction)
from launch.substitutions import FindExecutable, LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    """Manipulate runtime values of LaunchConfiguration."""
    device_path_val = LaunchConfiguration("device_path").perform(context)
    topic_name_val = LaunchConfiguration("topic_name").perform(context)
    request_body = f"\"{{device_path : {device_path_val}, topic_name: {topic_name_val} }}\""

    service_call = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            'service call',
            '/adi_iio_node/BufferEnableTopic',
            'adi_iio/srv/BufferEnableTopic',
            request_body
        ],
        shell=True,
    )
    return [
        service_call
    ]


def generate_launch_description():
    device_path_arg = DeclareLaunchArgument(
        name="device_path",
        description="The device path for which a topic for a buffer will be enabled."
    )

    topic_name_arg = DeclareLaunchArgument(
        name="topic_name",
        description="The name of the topic to be enabled."
    )

    return LaunchDescription([
        device_path_arg,
        topic_name_arg,
        OpaqueFunction(function=launch_setup),
    ])
