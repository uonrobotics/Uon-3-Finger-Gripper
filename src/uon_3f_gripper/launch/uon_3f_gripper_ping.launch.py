from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    device_name = LaunchConfiguration('device_name')
    baudrate = LaunchConfiguration('baudrate')
    dxl_id = LaunchConfiguration('dxl_id')
    protocol_version = LaunchConfiguration('protocol_version')

    return LaunchDescription([
        DeclareLaunchArgument('device_name', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('baudrate', default_value='2000000'),
        DeclareLaunchArgument('dxl_id', default_value='0'),
        DeclareLaunchArgument('protocol_version', default_value='2.0'),
        Node(
            package='uon_3f_gripper',
            executable='dynamixel_ping',
            name='dynamixel_ping',
            output='screen',
            parameters=[{
                'device_name': device_name,
                'baudrate': baudrate,
                'dxl_id': dxl_id,
                'protocol_version': protocol_version,
            }],
        ),
    ])
