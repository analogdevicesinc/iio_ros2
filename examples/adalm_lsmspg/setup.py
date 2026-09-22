# Copyright 2026 Analog Devices, Inc.
#
# SPDX-License-Identifier: ADIBSD

import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'adalm_lsmspg'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob(os.path.join('launch', '*.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Evelyn Plesca',
    maintainer_email='evelyn-iulia.plesca@analog.com',
    description='ROS2 Hello World demo with ADALM-LSMSPG and adi_iio',
    license='ADIBSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'servo_commander = adalm_lsmspg.servo_commander:main',
            'servo_feedback = adalm_lsmspg.servo_feedback:main',
            'sweep_generator = adalm_lsmspg.sweep_generator:main',
            'pid_controller = adalm_lsmspg.pid_controller:main',
            'step_generator = adalm_lsmspg.step_generator:main',
        ],
    },
)
