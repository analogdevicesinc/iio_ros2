from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():

    enable_service = ExecuteProcess(
        cmd=[[
            'ros2 service call ',
            '/sensor/AttrEnableTopic ',
            'adi_iio_interfaces/srv/AttrEnableTopic ',
            '"{attr_path: \'ad5625/voltage1/powerdown_mode\'}"'
        ]],
        shell=True
    )

    adi_iio_node = Node(
            package='adi_iio',
            executable='adi_iio',
            name='sensor',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'uri': 'ip:192.168.2.1'}],
            arguments=['--ros-args', '--log-level', 'debug']
            
        )

    return LaunchDescription([
        adi_iio_node,
        enable_service
    ])
