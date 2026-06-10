#!/usr/bin/env python3
import sys
import threading
import tkinter as tk
from tkinter import ttk

import rclpy
from rclpy.node import Node
from control_msgs.msg import GripperCommand

class GripperTkGuiNode(Node):
    def __init__(self, ui_app):
        super().__init__('gripper_tk_gui_node')
        self.ui_app = ui_app

        # YAML 파일에서 설정된 파라미터 선언 및 가져오기
        self.declare_parameter('stroke_length', 1800)
        self.declare_parameter('grasping_force_limit', 1188)
        self.declare_parameter('topc_name', 'uon/gripper_3f/command')
        self.declare_parameter('state_topic_name', 'uon/gripper_3f/state')

        self.stroke_length = self.get_parameter('stroke_length').value
        self.grasping_force_limit = self.get_parameter('grasping_force_limit').value
        topic_name = self.get_parameter('topc_name').value
        state_topic_name = self.get_parameter('state_topic_name').value

        # 제어 명령 Publisher 생성
        self.command_pub = self.create_publisher(
            GripperCommand,
            topic_name,
            10
        )

        # 상태 수신 Subscriber 생성
        self.state_sub = self.create_subscription(
            GripperCommand,
            state_topic_name,
            self.state_callback,
            10
        )

    def send_command(self, position, force):
        """슬라이더 값 변경 시 ROS2 토픽 발행"""
        msg = GripperCommand()
        msg.position = float(position)
        msg.max_effort = float(force)
        self.command_pub.publish(msg)

    def state_callback(self, msg):
        """그리퍼 피드백 수신 시 Tkinter UI 데이터 갱신 요청"""
        self.ui_app.queue_update_state(msg.position, msg.max_effort)


class GripperTkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UON 3F Gripper Controller (Tkinter)")
        self.geometry("450x350")

        self.ros_node = None
        self.current_pos_val = 0.0
        self.current_force_val = 0.0

        # 초기 슬라이더 최댓값
        self.max_stroke = 1800
        self.max_force = 50

        self.init_ui()

    def set_ros_node(self, ros_node):
        """ROS2 노드가 생성되면 YAML에서 가져온 실제 파라미터로 UI 셋팅 업데이트"""
        self.ros_node = ros_node
        self.max_stroke = self.ros_node.stroke_length
        self.max_force = self.ros_node.grasping_force_limit

        # 슬라이더 가동 범위 및 프로그레스바 최댓값 리셋
        self.pos_slider.config(to=self.max_stroke)
        self.force_slider.config(to=self.max_force)
        self.progress_bar.config(maximum=self.max_stroke)
        self.update_labels()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. Position 제어 슬라이더 ---
        self.pos_label_var = tk.StringVar(value="Target Position: 0")
        ttk.Label(main_frame, textvariable=self.pos_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.pos_slider = ttk.Scale(main_frame, from_=0, to=self.max_stroke, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.pos_slider.pack(fill=tk.X, pady=(0, 15))

        # --- 2. Force 제어 슬라이더 ---
        self.force_label_var = tk.StringVar(value="Target Force: 0")
        ttk.Label(main_frame, textvariable=self.force_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.force_slider = ttk.Scale(main_frame, from_=0, to=self.max_force, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.force_slider.set(300)  # 초기 힘 설정값 (예: 300)
        self.force_slider.pack(fill=tk.X, pady=(0, 20))

        # 구분선
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # --- 3. Live Feedback 상태창 ---
        ttk.Label(main_frame, text="[Live Gripper State]", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.state_pos_var = tk.StringVar(value="Current Position: 0")
        ttk.Label(main_frame, textvariable=self.state_pos_var).pack(anchor=tk.W)

        # 상태 프로그레스 바
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate', maximum=self.max_stroke)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))

        self.state_force_var = tk.StringVar(value="Current Force: 0.0")
        ttk.Label(main_frame, textvariable=self.state_force_var).pack(anchor=tk.W)

        self.check_ui_updates()

    def update_labels(self):
        """슬라이더 조작 시 상단 텍스트 갱신"""
        pos = int(self.pos_slider.get())
        force = int(self.force_slider.get())
        self.pos_label_var.set(f"Target Position: {pos} / {self.max_stroke}")
        self.force_label_var.set(f"Target Force: {force} / {self.max_force}")

    def on_slider_changed(self, event=None):
        """드래그할 때마다 ROS2 토픽으로 명령 전송"""
        if self.ros_node:
            pos = int(self.pos_slider.get())
            force = int(self.force_slider.get())
            self.update_labels()
            self.ros_node.send_command(pos, force)

    def queue_update_state(self, position, force):
        self.current_pos_val = position
        self.current_force_val = force

    def check_ui_updates(self):
        """주기적으로 실제 피드백 UI 요소를 변경"""
        pos = int(self.current_pos_val)
        force = self.current_force_val

        self.state_pos_var.set(f"Current Position: {pos} / {self.max_stroke}")
        self.progress_bar['value'] = pos
        self.state_force_var.set(f"Current Force: {force:.1f} / {self.max_force}")

        self.after(50, self.check_ui_updates)


def ros_spin_thread(node):
    """ROS2 통신 전용 백그라운드 스레드"""
    rclpy.spin(node)


def main():
    rclpy.init()

    app = GripperTkApp()

    gripper_tk_node = GripperTkGuiNode(app)
    app.set_ros_node(gripper_tk_node)

    ros_thread = threading.Thread(target=ros_spin_thread, args=(gripper_tk_node,), daemon=True)
    ros_thread.start()

    try:
        app.mainloop()
    finally:
        gripper_tk_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()