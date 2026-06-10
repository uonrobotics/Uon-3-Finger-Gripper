# =====================================================================================
# 1. [dxl_gripper/dxl_paths.py]
# This module pre-maps the absolute path of the `/dxl_gripper` library directory, 
# the internal `config` folder, and the robot configuration file (`robot_config.json`). 
# It provides these predefined paths to be referenced globally across the project.
# =====================================================================================
import os

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(PKG_DIR, '..', 'config')
ROBOT_CONFIG_PATH = os.path.join(CONFIG_DIR, 'robot_config.json')