import time
import sys
import os

# 프로젝트 루트 디렉토리를 path에 추가하여 dxl_gripper를 찾을 수 있게 합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dxl_gripper.uon_3f_gripper import uon_3f_gripper

def create_gripper():
    # 생성된 인스턴스를 반환(return)해야 main 함수에서 사용할 수 있습니다.
    return uon_3f_gripper(
        stroke_length         = 1800,
        stroke_min            = 0,
        stroke_disable_offset = 100,
        grasping_force_limit  = 1188,
    )

def main():
    # 클래스 인스턴스 생성
    gripper = create_gripper()

    try:
        # 하드웨어 연결 시도
        if not gripper.connect():
            print("[Error] Failed to connect to gripper")
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
    except Exception as e:
        print(f"[Error] An unexpected error occurred: {e}")
    finally:
        # 오류 발생 및 종료 시 안전 조치
        if 'gripper' in locals():
            gripper.cleanup()

if __name__ == "__main__":
    main()
