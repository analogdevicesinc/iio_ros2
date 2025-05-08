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

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    ad5592r_pkg = get_package_share_directory('ad5592r')
    ad5592r_launch = os.path.join(ad5592r_pkg, 'launch')

    loop_rate_arg = DeclareLaunchArgument(
        name="loop_rate",
        default_value="1.0",
        description="The loop rate for the topic publishing.",
    )

    ad5592r_config = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            ad5592r_launch,
            'ad5592r_config.launch.py',
        )]),
    )

    ad5592r_topics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            ad5592r_launch,
            'ad5592r_topics.launch.py',
        )]),
        launch_arguments={
            'loop_rate': LaunchConfiguration("loop_rate")}.items(),
    )

    ad5592r_transforms = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            ad5592r_launch,
            'ad5592r_transforms.launch.py',
        )]),
        launch_arguments={
            'loop_rate': LaunchConfiguration("loop_rate")}.items(),
    )

    return LaunchDescription([
        loop_rate_arg,

        ad5592r_config,
        ad5592r_topics,
        ad5592r_transforms,
    ])
