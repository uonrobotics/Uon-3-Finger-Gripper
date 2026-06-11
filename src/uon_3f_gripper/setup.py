from glob import glob

from setuptools import find_packages, setup

package_name = 'uon_3f_gripper'

setup(
    name=package_name,
    version='0.0.0',
    packages=(
        find_packages(
            where='..',
            include=[
                'uon_3f_gripper',
                'uon_3f_gripper.scripts',
                'dynamixel_sdk',
                'serial',
                'serial.*',
            ],
        )
        + find_packages(
            where='.',
            include=[
                'dxl_gripper',
                'config',
            ],
        )
    ),
    package_dir={
        '': '..',
        'dxl_gripper': 'dxl_gripper',
        'config': 'config',
    },
    package_data={
        'config': ['*.json'],
    },
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jusik Min',
    maintainer_email='jusik.min@uonrobotics.com',
    description='Python ROS 2 package for a Dynamixel-based three-finger gripper.',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'dynamixel_ping = uon_3f_gripper.scripts.uon_3f_gripper_ping:main',
            'gripper_demo   = uon_3f_gripper.scripts.uon_3f_gripper_demo:main',
            'gripper_node   = uon_3f_gripper.scripts.uon_3f_gripper_node:main',
            'gripper_ui     = uon_3f_gripper.scripts.uon_3f_gripper_ui:main',
            'camera_node    = uon_3f_gripper.scripts.uon_3f_gripper_camera_node:main',
        ],
    },
)
