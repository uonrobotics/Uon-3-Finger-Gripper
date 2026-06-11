#!/usr/bin/env python3
import sys
import threading
import tkinter as tk
from tkinter import ttk

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

# ROS 2 메시지 타입
from control_msgs.msg import GripperCommand
from sensor_msgs.msg import Image

# 이미지 변환 라이브러리
from cv_bridge import CvBridge
import cv2
import numpy as np
from PIL import Image as PilImage, ImageTk


class GripperTkGuiNode(Node):
    def __init__(self, ui_app):
        super().__init__('gripper_camera_tk_gui_node')
        self.ui_app = ui_app

        # 멀티스레딩을 위한 콜백 그룹 설정
        self.image_cb_group = MutuallyExclusiveCallbackGroup()
        self.bridge = CvBridge()

        # YAML 파일에서 설정된 파라미터 선언 및 가져오기
        self.declare_parameter('stroke_length', 1800)
        self.declare_parameter('grasping_force_limit', 1188)
        self.declare_parameter('topc_name', 'uon/gripper_3f/command')
        self.declare_parameter('state_topic_name', 'uon/gripper_3f/state')

        # 카메라 토픽 파라미터
        self.declare_parameter('color_topic_name', 'uon/camera/color/image_raw')
        self.declare_parameter('depth_topic_name', 'uon/camera/depth/image_raw')

        self.stroke_length = self.get_parameter('stroke_length').value
        self.grasping_force_limit = self.get_parameter('grasping_force_limit').value
        topic_name = self.get_parameter('topc_name').value
        state_topic_name = self.get_parameter('state_topic_name').value

        # 카메라 토픽 이름 가져오기
        color_topic = self.get_parameter('color_topic_name').value
        depth_topic = self.get_parameter('depth_topic_name').value

        # 제어 명령 Publisher 생성
        self.command_pub = self.create_publisher(GripperCommand, topic_name, 10)

        # 상태 수신 Subscriber 생성
        self.state_sub = self.create_subscription(GripperCommand, state_topic_name, self.state_callback, 10)

        # 카메라 이미지 수신 Subscriber 생성
        self.color_sub = self.create_subscription(
            Image, color_topic, self.color_image_callback, 1, callback_group=self.image_cb_group
        )
        self.depth_sub = self.create_subscription(
            Image, depth_topic, self.depth_image_callback, 1, callback_group=self.image_cb_group
        )

        self.get_logger().info(f"[GUI] Subscribing to Color: '{color_topic}', Depth: '{depth_topic}'")

    def send_command(self, position, force):
        """슬라이더 값 변경 시 ROS2 토픽 발행"""
        msg = GripperCommand()
        msg.position = float(position)
        msg.max_effort = float(force)
        self.command_pub.publish(msg)

    def state_callback(self, msg):
        """그리퍼 피드백 수신 시 Tkinter UI 데이터 갱신 요청"""
        self.ui_app.queue_update_state(msg.position, msg.max_effort)

    # 카메라 콜백 함수들
    def color_image_callback(self, msg):
        """컬러 이미지 수신 시 OpenCV 배열로 변환하여 UI로 전달"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.ui_app.queue_update_color_image(cv_image)
        except Exception as e:
            self.get_logger().warn(f"Failed to convert color image: {e}")

    def depth_image_callback(self, msg):
        """깊이 이미지 수신 시 시각화 가능한 배열로 변환하여 UI로 전달"""
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

            depth_normalized = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

            depth_colormap = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)

            self.ui_app.queue_update_depth_image(depth_colormap)
        except Exception as e:
            self.get_logger().warn(f"Failed to convert depth image: {e}")


class GripperTkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UON 3F Gripper & Camera Dashboard")

        self.geometry("1100x550")

        self.ros_node = None
        self.current_pos_val = 0.0
        self.current_force_val = 0.0

        # 카메라 이미지 데이터를 담을 변수
        self.cv_img_color = None
        self.cv_img_depth = None

        # Tkinter에 표시될 이미지 객체 래퍼
        self.tk_img_color = None
        self.tk_img_depth = None

        # 초기 슬라이더 최댓값기존 유지)
        self.max_stroke = 1800
        self.max_force = 1188

        self.init_ui()

    def set_ros_node(self, ros_node):
        """ROS2 노드 생성 시 파라미터 업데이트"""
        self.ros_node = ros_node
        self.max_stroke = self.ros_node.stroke_length
        self.max_force = self.ros_node.grasping_force_limit

        self.pos_slider.config(to=self.max_stroke)
        self.force_slider.config(to=self.max_force)
        self.progress_bar.config(maximum=self.max_stroke)
        self.update_labels()

    def init_ui(self):
        # 전체 화면을 왼쪽(제어)과 오른쪽(카메라)으로 분할
        content_frame = ttk.Frame(self, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # 왼쪽 파트: 그리퍼 제어 및 상태
        # ==========================================
        control_frame = ttk.LabelFrame(content_frame, text=" Gripper Control & State ", padding="15")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Position 제어 슬라이더
        self.pos_label_var = tk.StringVar(value="Target Position: 0")
        ttk.Label(control_frame, textvariable=self.pos_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.pos_slider = ttk.Scale(control_frame, from_=0, to=self.max_stroke, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.pos_slider.pack(fill=tk.X, pady=(0, 15))

        # Force 제어 슬라이더
        self.force_label_var = tk.StringVar(value="Target Force: 0")
        ttk.Label(control_frame, textvariable=self.force_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.force_slider = ttk.Scale(control_frame, from_=0, to=self.max_force, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.force_slider.set(50)  # 초기 힘 설정값
        self.force_slider.pack(fill=tk.X, pady=(0, 20))

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # Live Feedback 상태창
        ttk.Label(control_frame, text="[Live Gripper State]", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.state_pos_var = tk.StringVar(value="Current Position: 0")
        ttk.Label(control_frame, textvariable=self.state_pos_var).pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, mode='determinate', maximum=self.max_stroke)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))

        self.state_force_var = tk.StringVar(value="Current Force: 0.0")
        ttk.Label(control_frame, textvariable=self.state_force_var).pack(anchor=tk.W)

        # ==========================================
        # 오른쪽 파트: 카메라 이미지 시각화
        # ==========================================
        camera_frame = ttk.LabelFrame(content_frame, text=" Live Camera View ", padding="10")
        camera_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 이미지가 표시될 라벨 생성
        self.lbl_color = ttk.Label(camera_frame, text="Waiting for Color Image...", anchor=tk.CENTER, background="black", foreground="white")
        self.lbl_color.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.lbl_depth = ttk.Label(camera_frame, text="Waiting for Depth Image...", anchor=tk.CENTER, background="black", foreground="white")
        self.lbl_depth.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # UI 업데이트 타이머 루프 시작
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
        """그리퍼 상태 데이터 큐잉"""
        self.current_pos_val = position
        self.current_force_val = force

    # 카메라 이미지 데이터 큐잉 함수들
    def queue_update_color_image(self, cv_bgr_image):
        """콜백 스레드에서 수신한 OpenCV 이미지를 저장"""
        self.cv_img_color = cv_bgr_image

    def queue_update_depth_image(self, cv_colormap_image):
        """콜백 스레드에서 수신한 깊이 컬러맵 이미지를 저장"""
        self.cv_img_depth = cv_colormap_image

    def check_ui_updates(self):
        """주기적으로 실제 피드백 UI 및 이미지 요소를 변경 """

        # 1. 그리퍼 상태 업데이트
        pos = int(self.current_pos_val)
        force = self.current_force_val

        self.state_pos_var.set(f"Current Position: {pos} / {self.max_stroke}")
        self.progress_bar['value'] = pos
        self.state_force_var.set(f"Current Force: {force:.1f} / {self.max_force}")

        # 2. 카메라 이미지 UI 업데이트
        # 컬러 이미지 처리
        if self.cv_img_color is not None:
            # OpenCV BGR -> RGB 변환
            rgb_img = cv2.cvtColor(self.cv_img_color, cv2.COLOR_BGR2RGB)
            # PIL Image -> ImageTk 변환
            pil_img = PilImage.fromarray(rgb_img)

            # UI 크기에 맞게 리사이징
            display_img = pil_img.resize((480, 270), PilImage.Resampling.LANCZOS)
            self.tk_img_color = ImageTk.PhotoImage(image=display_img)

            # 라벨 업데이트
            self.lbl_color.configure(image=self.tk_img_color, text="")
            # self.cv_img_color = None # 소모 처리 안 함 (지속 표시)

        # 뎁스 이미지 처리
        if self.cv_img_depth is not None:
            # OpenCV BGR -> RGB 변환
            rgb_depth = cv2.cvtColor(self.cv_img_depth, cv2.COLOR_BGR2RGB)
            # PIL Image -> ImageTk 변환
            pil_depth = PilImage.fromarray(rgb_depth)

            # UI 크기에 맞게 리사이징
            display_depth = pil_depth.resize((480, 270), PilImage.Resampling.LANCZOS)
            self.tk_img_depth = ImageTk.PhotoImage(image=display_depth)

            # 라벨 업데이트
            self.lbl_depth.configure(image=self.tk_img_depth, text="")

        # 50ms 마다 반복
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