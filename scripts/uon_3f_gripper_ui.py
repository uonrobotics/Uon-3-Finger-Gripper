#!/usr/bin/env python3
import sys
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from dxl_gripper.uon_3f_gripper import uon_3f_gripper
except ImportError:
    try:
        import uon_3f_gripper as ug
        uon_3f_gripper = ug.uon_3f_gripper
    except:
        pass

class GripperTkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UON 3F Gripper Direct Controller")
        self.geometry("450x450")

        # 그리퍼 기본 설정값
        self.max_stroke = 1800
        self.max_force = 1188

        # 실시간 상태 변수
        self.current_pos_val = 0
        self.current_force_val = 0
        self.is_connected = False
        self.stop_feedback = False

        # 그리퍼 인스턴스
        self.gripper = None

        self.init_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_ui(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 0. Connection Control ---
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 15))

        self.conn_status_var = tk.StringVar(value="Status: Disconnected")
        ttk.Label(conn_frame, textvariable=self.conn_status_var).pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.RIGHT, padx=5)

        # --- 1. Position 제어 슬라이더 ---
        self.pos_label_var = tk.StringVar(value=f"Target Position: 0 / {self.max_stroke}")
        ttk.Label(main_frame, textvariable=self.pos_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.pos_slider = ttk.Scale(main_frame, from_=0, to=self.max_stroke, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.pos_slider.pack(fill=tk.X, pady=(0, 15))

        # --- 2. Force 제어 슬라이더 ---
        self.force_label_var = tk.StringVar(value=f"Target Force: 50 / {self.max_force}")
        ttk.Label(main_frame, textvariable=self.force_label_var, font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))

        self.force_slider = ttk.Scale(main_frame, from_=0, to=self.max_force, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.force_slider.set(50)
        self.force_slider.pack(fill=tk.X, pady=(0, 20))

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # --- 3. Live Feedback 상태창 ---
        ttk.Label(main_frame, text="[Live Gripper State]", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.state_pos_var = tk.StringVar(value="Current Position: 0")
        ttk.Label(main_frame, textvariable=self.state_pos_var).pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate', maximum=self.max_stroke)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))

        self.state_force_var = tk.StringVar(value="Current Force: 0.0")
        ttk.Label(main_frame, textvariable=self.state_force_var).pack(anchor=tk.W)

        self.check_ui_updates()

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_gripper()
        else:
            self.disconnect_gripper()

    def connect_gripper(self):
        try:
            self.gripper = uon_3f_gripper(
                stroke_length         = self.max_stroke,
                stroke_min            = 0,
                stroke_disable_offset = 100,
                grasping_force_limit  = self.max_force,
            )

            if self.gripper.connect():
                self.gripper.enable()
                self.is_connected = True
                self.conn_status_var.set("Status: Connected")
                self.btn_connect.config(text="Disconnect")
                print("[System] Gripper connected and enabled.")

                self.stop_feedback = False
                self.feedback_thread = threading.Thread(target=self.update_gripper_state_loop, daemon=True)
                self.feedback_thread.start()
            else:
                messagebox.showerror("Connection Error", "Failed to connect to Dynamixel. Check port and IDs.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def disconnect_gripper(self):
        self.stop_feedback = True
        if self.gripper:
            try:
                self.gripper.disable()
                self.gripper.cleanup()
            except:
                pass
        self.is_connected = False
        self.conn_status_var.set("Status: Disconnected")
        self.btn_connect.config(text="Connect")
        print("[System] Gripper disconnected.")

    def update_gripper_state_loop(self):
        """하드웨어로부터 실시간 데이터를 읽어오는 백그라운드 루ㅠㅡ"""
        while not self.stop_feedback and self.is_connected:
            try:
                if self.gripper:
                    #  위치 읽기
                    try:
                        pos = self.gripper.get_position()
                        if pos is not None:
                            self.current_pos_val = pos
                    except (IndexError, TypeError):
                        # 통신 패킷이 불완전할 때 발생하는 에러 무시
                        pass

                    # 전류(힘) 읽기
                    try:
                        force = self.gripper.get_current()
                        if force is not None:
                            self.current_force_val = force
                    except (IndexError, TypeError):
                        pass

            except Exception as e:
                # print(f"[Debug] Feedback Loop Error: {e}")
                pass

            time.sleep(0.1)

    def update_labels(self):
        pos = int(self.pos_slider.get())
        force = int(self.force_slider.get())
        self.pos_label_var.set(f"Target Position: {pos} / {self.max_stroke}")
        self.force_label_var.set(f"Target Force: {force} / {self.max_force}")

    def on_slider_changed(self, event=None):
        self.update_labels()
        if self.is_connected and self.gripper:
            pos = int(self.pos_slider.get())
            force = int(self.force_slider.get())
            try:
                self.gripper.stroke(pos, force=force)
            except:
                pass

    def check_ui_updates(self):
        pos = int(self.current_pos_val)
        force = self.current_force_val

        self.state_pos_var.set(f"Current Position: {pos} / {self.max_stroke}")
        self.progress_bar['value'] = pos
        self.state_force_var.set(f"Current Force: {force} / {self.max_force}")

        self.after(50, self.check_ui_updates)

    def on_closing(self):
        if self.is_connected:
            self.disconnect_gripper()
        self.destroy()

def main():
    app = GripperTkApp()
    app.mainloop()

if __name__ == '__main__':
    main()
