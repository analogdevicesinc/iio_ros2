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
    # TODO: review source code implementation + required service call format (for buffer request parameter)
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
    device_path_arg = DeclareLaunchArgument(
        name="device_path",
        description="The path of the device to write to."
    )

    channels_arg = DeclareLaunchArgument(
        name="channels",
        description="The channels to write to."
    )

    buffer_arg = DeclareLaunchArgument(
        name="buffer",
        description="The path of the device to write to."
    )

    cyclic_arg = DeclareLaunchArgument(
        name="cyclic",
        description="Indicates if the buffer write should be cyclic."
    )

    return LaunchDescription([
        device_path_arg,
        channels_arg,
        buffer_arg,
        cyclic_arg,
        OpaqueFunction(function=launch_setup),
    ])
