#!/usr/bin/env python3
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

from control_msgs.msg import GripperCommand
from control_msgs.action import GripperCommand as GripperCommandAction

from dxl_gripper.uon_3f_gripper import uon_3f_gripper


class GripperRunNode(Node):
    def __init__(self):
        super().__init__('gripper_run')

        # 멀티스레드 처리를 위한 콜백 그룹 설정 (액션과 타이머가 동시에 돌 수 있도록 함)
        self.callback_group = MutuallyExclusiveCallbackGroup()


        # 기본 파라미터 선언
        self.declare_parameter('stroke_length'        , uon_3f_gripper.DEFAULT_STROKE_LENGTH)
        self.declare_parameter('stroke_min'           , uon_3f_gripper.DEFAULT_STROKE_MIN)
        self.declare_parameter('stroke_disable_offset', uon_3f_gripper.DEFAULT_STROKE_DISABLE_OFFSET)
        self.declare_parameter('grasping_force_limit' , uon_3f_gripper.DEFAULT_GRASPING_FORCE_LIMIT)
        self.declare_parameter('topc_name'            , 'uon/gripper_3f/command') # 제어 명령 토픽
        self.declare_parameter('state_topic_name'     , 'uon/gripper_3f/state')   # 상태 이름
        self.declare_parameter('action_name'          , 'uon/gripper_3f/action')  # 액션 이름

        # 그리퍼 인스턴스 생성
        self.gripper = self.create_gripper()

        # 하드웨어 연결 및 활성화
        if not self.gripper.connect():
            self.get_logger().error("[System] Failed to connect to gripper hardware.")
            sys.exit(1)

        topic_name = self.get_parameter('topc_name').value
        state_topic_name = self.get_parameter('state_topic_name').value
        action_name = self.get_parameter('action_name').value

        self.gripper.enable()
        self.get_logger().info(f"[System] Gripper enabled.")
        self.get_logger().info(f"[System] Topic Command: '{topic_name}' | Action Server: '{action_name}'")

        # 토픽 Subscriber 생성
        self.subscription = self.create_subscription(
            GripperCommand,
            topic_name,
            self.command_callback,
            1,
            callback_group=self.callback_group
        )

        #  상태 토픽 Publisher 생성
        self.state_publisher = self.create_publisher(
            GripperCommand,
            state_topic_name,
            10
        )

        #  주기적 상태 퍼블리시 타이머 (10Hz)
        self.timer_period = 1.0/ 30.0
        self.timer = self.create_timer(
            self.timer_period,
            self.publish_status_callback,
            callback_group=self.callback_group
        )

    def create_gripper(self):
        """그리퍼 생성"""
        return uon_3f_gripper(
            stroke_length         = self.get_parameter('stroke_length').value,
            stroke_min            = self.get_parameter('stroke_min').value,
            stroke_disable_offset = self.get_parameter('stroke_disable_offset').value,
            grasping_force_limit  = self.get_parameter('grasping_force_limit').value,
        )

    def shutdown_gripper(self):
        """노드 종료"""
        self.get_logger().info("[System] Disabling and cleaning up gripper...")
        self.gripper.disable()
        self.gripper.cleanup()

    def command_callback(self, msg):
        """토픽 메시지를 받을 때마다 호출되는 콜백 함수"""
        target_stroke = int(msg.position)
        target_force = int(msg.max_effort)
        print(f"target_stroke: {target_stroke}, target_force: {target_force}", flush=True)
        self.gripper.stroke(target_stroke, target_force)

    def publish_status_callback(self):
        """주기적으로 모터의 실제 현재 위치를 읽어서 토픽으로 퍼블리시하는 함수"""
        pass
        current_pos   = self.gripper.get_position()
        current_force = self.gripper.get_current()
        if current_pos is not None:
            state_msg = GripperCommand()
            state_msg.position = float(current_pos)
            state_msg.max_effort = float(current_force)
            self.state_publisher.publish(state_msg)



def main(args=None):
    rclpy.init(args=args)
    node = GripperRunNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("\n[System] Program terminated by user.")
    finally:
        node.shutdown_gripper()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()