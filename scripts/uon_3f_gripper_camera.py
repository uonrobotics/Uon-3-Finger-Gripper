#!/usr/bin/env python3
import sys
import pyrealsense2 as rs
import numpy as np
import cv2
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
CAMERA_CONFIG_PATH = project_root / "config" / "camera_config.yaml"

def load_camera_config(config_path=CAMERA_CONFIG_PATH):
    config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            for line in config_file:
                line = line.split("#", 1)[0].strip()
                if not line or ":" not in line:
                    continue

                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip("'\"")

                if value.isdigit():
                    config[key] = int(value)
                else:
                    config[key] = value
    except FileNotFoundError:
        print(f"[Warning] Camera config file not found at {config_path}. Using defaults.")

    return config

def main():
    camera_config = load_camera_config()

    width = camera_config.get("width", 848)
    height = camera_config.get("height", 480)
    fps = camera_config.get("fps", 30)

    print(f"[System] Initializing RealSense camera ({width}x{height} @ {fps}FPS)...")

    # RealSense 파이프라인 및 설정 초기화
    pipeline = rs.pipeline()
    rs_config = rs.config()

    # 스트림 설정
    rs_config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
    rs_config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)

    # 하드웨어 파이프라인 시작
    try:
        pipeline.start(rs_config)
        print("[System] RealSense D405 Pipeline started successfully.")
    except Exception as e:
        print(f"[System] Failed to start RealSense pipeline: {e}")
        sys.exit(1)

    try:
        # 무한 루프를 돌며 프레임 지속 업데이트
        while True:
            # 새로운 프레임 세트를 대기 후 가져오기
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            images_stacked = np.hstack((color_image, depth_colormap))

            cv2.imshow('RealSense Color & Depth Viewer', images_stacked)

            # 키보드 입력 대기 (1ms)
            key = cv2.waitKey(1)
            # 'q' 키 또는 ESC(27) 키를 누르면 루프 탈출
            if key & 0xFF == ord('q') or key == 27:
                print("\n[System] Program terminated by user.")
                break

    except Exception as e:
        print(f"Error occurred during streaming: {e}")

    finally:
        print("[System] Stopping RealSense pipeline and cleaning up...")
        pipeline.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()