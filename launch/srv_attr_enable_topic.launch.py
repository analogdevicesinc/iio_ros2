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
    attr_path_val = LaunchConfiguration("attr_path").perform(context)
    topic_name_val = LaunchConfiguration("topic_name").perform(context)
    type_val = LaunchConfiguration("type").perform(context)
    loop_rate_val = LaunchConfiguration("loop_rate").perform(context)
    type_val = LaunchConfiguration("type").perform(context)

    request_body = f"\"{{ attr_path: {attr_path_val}, topic_name: {topic_name_val}, type: {type_val}, loop_rate: {loop_rate_val} }}\""

    service_call = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            'service call',
            '/adi_iio_node/AttrEnableTopic',
            'adi_iio/srv/AttrEnableTopic',
            request_body
        ],
        shell=True,
    )
    return [
        service_call
    ]


def generate_launch_description():
    attr_path_args = DeclareLaunchArgument(
        name="attr_path",
        description="The attribute path to write to."
    )

    topic_name_arg = DeclareLaunchArgument(
        name="topic_name",
        default_value="",
        description="The topic name to be enabled."
    )

    loop_rate_arg = DeclareLaunchArgument(
        name="loop_rate",
        default_value="1",
        description="The loop rate in Hz."
    )

    type_arg = DeclareLaunchArgument(
        name="type",
        default_value="0",
        description="The type of the attribute to be enabled.",
        choices=["0", "1", "2", "3"]
    )

    return LaunchDescription([
        attr_path_args,
        topic_name_arg,
        loop_rate_arg,
        type_arg,
        OpaqueFunction(function=launch_setup),
    ])
