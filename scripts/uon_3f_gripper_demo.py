import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from dxl_gripper.uon_3f_gripper import uon_3f_gripper

GRIPPER_CONFIG_PATH = PROJECT_ROOT / "config" / "gripper_config.yaml"


def load_gripper_config(config_path=GRIPPER_CONFIG_PATH):
    config = {}
    with open(config_path, "r", encoding="utf-8") as config_file:
        for line_number, line in enumerate(config_file, start=1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError(f"Invalid config line {line_number}: {line}")

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key or not value:
                raise ValueError(f"Invalid config line {line_number}: {line}")

            try:
                config[key] = int(value)
            except ValueError as exc:
                raise ValueError(
                    f"Config value for '{key}' must be an integer: {value}"
                ) from exc

    return config


def create_gripper(config_path=GRIPPER_CONFIG_PATH):
    config = load_gripper_config(config_path)
    return uon_3f_gripper(**config)

def main():
    # 클래스 인스턴스 생성
    gripper = create_gripper()

    try:
        # 하드웨어 연결
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
        gripper.stroke(1500, 50)
        time.sleep(2.0)

        print("[System] Gripper stroke: 1000", flush=True)
        gripper.stroke(1000, 50)
        time.sleep(2.0)

        print("[System] Gripper stroke: 500", flush=True)
        gripper.stroke(500, 50)
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
