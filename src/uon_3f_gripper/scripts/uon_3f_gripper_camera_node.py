#!/usr/bin/env python3
import sys
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

# ROS 2 메시지 및 OpenCV 변환 라이브러리
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# Intel RealSense Python API
import pyrealsense2 as rs
import numpy as np


class CameraRunNode(Node):
    def __init__(self):
        super().__init__('camera_run')

        # 콜백 그룹 설정 (타이머가 독립적으로 돌 수 있도록 함)
        self.callback_group = MutuallyExclusiveCallbackGroup()

        # 기본 파라미터 선언 (yaml 파일에서 덮어씌워짐)
        self.declare_parameter('width', 848)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('color_topic_name', 'uon/camera/color/image_raw')
        self.declare_parameter('depth_topic_name', 'uon/camera/depth/image_raw')

        # 파라미터 값 가져오기
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fps = self.get_parameter('fps').value
        color_topic = self.get_parameter('color_topic_name').value
        depth_topic = self.get_parameter('depth_topic_name').value

        self.get_logger().info(f"[System] Color Topic: '{color_topic}'")
        self.get_logger().info(f"[System] Depth Topic: '{depth_topic}'")

        # ROS Image와 OpenCV 배열 변환을 위한 브릿지
        self.bridge = CvBridge()

        # 카메라 데이터 Publisher 생성
        self.color_publisher = self.create_publisher(Image, color_topic, 10)
        self.depth_publisher = self.create_publisher(Image, depth_topic, 10)

        # RealSense 카메라 초기화 및 연결
        self.pipeline = rs.pipeline()
        self.rs_config = rs.config()

        # 스트림 설정 (D405 해상도 및 포맷)
        self.rs_config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        self.rs_config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)

        # 하드웨어 파이프라인 시작
        try:
            self.pipeline.start(self.rs_config)
            self.get_logger().info("[System] RealSense D405 Pipeline started successfully.")
        except Exception as e:
            self.get_logger().error(f"[System] Failed to start RealSense pipeline: {e}")
            sys.exit(1)

        # 설정된 FPS에 맞춰 주기적으로 프레임을 퍼블리시하는 타이머
        timer_period = 1.0 / float(self.fps)
        self.timer = self.create_timer(
            timer_period,
            self.publish_frames_callback,
            callback_group=self.callback_group
        )

    def shutdown_camera(self):
        """노드 종료 시 카메라 파이프라인 안전 종료"""
        self.get_logger().info("[System] Stopping RealSense pipeline and cleaning up...")
        self.pipeline.stop()

    def publish_frames_callback(self):
        """주기적으로 카메라 프레임을 읽어와 ROS 토픽으로 퍼블리시"""
        try:
            # 새로운 프레임 세트를 대기 후 가져오기
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                return

            # 프레임 데이터를 Numpy 배열로 변환
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            # Numpy 배열을 ROS 2 Image 메시지로 변환
            # color: 8비트 BGR, depth: 16비트 단일 채널
            color_msg = self.bridge.cv2_to_imgmsg(color_image, encoding="bgr8")
            depth_msg = self.bridge.cv2_to_imgmsg(depth_image, encoding="16UC1")

            # 시간 동기화(Timestamp) 및 프레임 ID 부여
            now = self.get_clock().now().to_msg()
            color_msg.header.stamp = now
            color_msg.header.frame_id = "camera_color_optical_frame"

            depth_msg.header.stamp = now
            depth_msg.header.frame_id = "camera_depth_optical_frame"

            # 토픽 퍼블리시
            self.color_publisher.publish(color_msg)
            self.depth_publisher.publish(depth_msg)

        except Exception as e:
            self.get_logger().warn(f"Error fetching frames: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = CameraRunNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("\n[System] Program terminated by user.")
    finally:
        node.shutdown_camera()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()