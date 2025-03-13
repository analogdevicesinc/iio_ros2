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
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import FindExecutable, LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    """Manipulate runtime values of LaunchConfiguration."""
    attr_path = LaunchConfiguration("attr_path").perform(context)
    value = LaunchConfiguration("value").perform(context)
    request_body = f"\"{{ attr_path: {attr_path}, value: {value} }}\""

    service_call = ExecuteProcess(
        cmd=[
            FindExecutable(name='ros2'),
            'service call',
            '/adi_iio_node/AttrWriteString',
            'adi_iio/srv/AttrWriteString',
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

    value_arg = DeclareLaunchArgument(
        name="value",
        description="The value to write to the attribute."
    )

    return LaunchDescription([
        attr_path_args,
        value_arg,
        OpaqueFunction(function=launch_setup),
    ])
