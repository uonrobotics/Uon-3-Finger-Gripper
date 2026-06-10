from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_path = Path(
        get_package_share_directory('uon_3f_gripper')
    ) / 'config' / 'gripper_config.yaml'

    return LaunchDescription([
        # 그리퍼 노드
        Node(
            package    = 'uon_3f_gripper',
            executable = 'gripper_node',
            name       = 'gripper_node',
            output     = 'screen',
            parameters = [str(config_path)],
        ),

        # GUI 제어 노드
        Node(
            package    = 'uon_3f_gripper',
            executable = 'gripper_ui',
            name       = 'gripper_ui',
            output     = 'screen',
            parameters = [str(config_path)],
        ),
    ])