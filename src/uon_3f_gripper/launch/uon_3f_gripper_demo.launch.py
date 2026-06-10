from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_path = Path(
        get_package_share_directory('uon_3f_gripper')
    ) / 'config' / 'gripper_config.yaml'

    return LaunchDescription([
        Node(
            package    = 'uon_3f_gripper',
            executable = 'gripper_demo',
            name       = 'gripper_demo',
            output     = 'screen',
            parameters = [str(config_path)],
        ),
    ])
