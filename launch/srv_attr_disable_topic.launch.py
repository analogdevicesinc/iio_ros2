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
    topic_name_val = LaunchConfiguration("topic_name").perform(context)
    type_val = LaunchConfiguration("type").perform(context)
    request_body = f"\"{{ topic_name: {topic_name_val}, type: {type_val} }}\""

    service_call = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            'service call',
            '/adi_iio_node/AttrDisableTopic',
            'adi_iio/srv/AttrDisableTopic',
            request_body
        ],
        shell=True,
    )
    return [
        service_call
    ]


def generate_launch_description():
    topic_name_arg = DeclareLaunchArgument(
        name="topic_name",
        description="The topic name to be disabled."
    )

    type_arg = DeclareLaunchArgument(
        name="type",
        default_value="0",
        description="The type of the topic to be disabled.",
        choices=["0", "1", "2", "3"]
    )

    return LaunchDescription([
        topic_name_arg,
        type_arg,
        OpaqueFunction(function=launch_setup),
    ])
