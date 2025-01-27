from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='adi_iio',
            executable='adi_iio',
            name='sensor',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'uri': 'ip:192.168.2.1'}
            ]
        )
    ])
