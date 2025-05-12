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
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    ad7128_8_pkg = get_package_share_directory('ad7124_8')
    ad7124_8_launch = os.path.join(ad7128_8_pkg, 'launch')

    ad7124_8_config = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            ad7124_8_launch,
            'ad7124_8_config.launch.py',
        )]),
    )

    ad7124_8_topics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            ad7124_8_launch,
            'ad7124_8_topics.launch.py',
        )]),
    )

    # ad7124_8_transforms = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([os.path.join(
    #         ad7124_8_launch,
    #         'ad7124_8_transforms.launch.py',
    #     )]),
    # )

    return LaunchDescription([
        ad7124_8_config,
        ad7124_8_topics,
        # ad7124_8_transforms,
    ])
