from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # camera_config.yaml 파일의 경로를 가져옵니다.
    config_path = Path(
        get_package_share_directory('uon_3f_gripper')
    ) / 'config' / 'camera_config.yaml'

    return LaunchDescription([
        Node(
            package    = 'uon_3f_gripper',
            executable = 'camera_node',
            name       = 'camera_node',
            output     = 'screen',
            parameters = [str(config_path)],
        ),
    ])