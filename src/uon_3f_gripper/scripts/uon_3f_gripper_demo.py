#!/usr/bin/env python3
import time

import rclpy
from dxl_gripper.uon_3f_gripper import uon_3f_gripper
from rclpy.node import Node


class GripperDemoNode(Node):
    def __init__(self):
        super().__init__('gripper_demo')

        # 기본 파라미터
        self.declare_parameter('stroke_length',         uon_3f_gripper.DEFAULT_STROKE_LENGTH)
        self.declare_parameter('stroke_min',            uon_3f_gripper.DEFAULT_STROKE_MIN)
        self.declare_parameter('stroke_disable_offset', uon_3f_gripper.DEFAULT_STROKE_DISABLE_OFFSET,)
        self.declare_parameter('grasping_force_limit',  uon_3f_gripper.DEFAULT_GRASPING_FORCE_LIMIT,)

    def create_gripper(self):
        return uon_3f_gripper(
            stroke_length         = self.get_parameter('stroke_length').value,
            stroke_min            = self.get_parameter('stroke_min').value,
            stroke_disable_offset = self.get_parameter('stroke_disable_offset').value,
            grasping_force_limit  = self.get_parameter('grasping_force_limit').value,
        )



def main(args=None):
    rclpy.init(args=args)
    node = GripperDemoNode()

    # 클래스 인스턴스 생성
    gripper = node.create_gripper()

    try:
        # 하드웨어 연결 시도
        if not gripper.connect():
            return 1

        gripper.enable()
        time.sleep(0.1)

        print("[System] Gripper open", flush=True)
        gripper.open()
        time.sleep(2.0)

        print("[System] Gripper close", flush=True)
        gripper.close()
        time.sleep(2.0)

        print("[System] Gripper stroke: 1500", flush=True)
        gripper.close()
        gripper.stroke(1500)
        time.sleep(2.0)

        print("[System] Gripper stroke: 1000", flush=True)
        gripper.stroke(1000)
        time.sleep(2.0)

        print("[System] Gripper stroke: 500", flush=True)
        gripper.stroke(500)
        time.sleep(2.0)

        print("[System] Gripper stroke: 0", flush=True)
        gripper.stroke(0)
        time.sleep(2.0)

        gripper.disable()

    except KeyboardInterrupt:
        print("\n[System] Program terminated by user.")
    finally:
        # 오류 발생 및 종료 시 안전 조치
        gripper.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
