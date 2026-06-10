# ===========================================================================
# 6. [dxl_gripper/__init__.py]
# The Grand Facade of the dxl_gripper package.
# Orchestrates single-axis, multi-axis, state management, and indirect 
# mapping modules into a single, cohesive, user-friendly interface.
# ===========================================================================

from .dxl_comm import dxl_CommManager
from .dxl_state_manager import StateManager
from .dxl_single_axis import SingleAxisCore
from .dxl_indirect import IndirectHandler

class DynamixelManager:
    """Integrated Control Environment (Facade)"""
    def __init__(self):
        self.comm = dxl_CommManager()
        self.state = StateManager(self.comm)
        self.single = SingleAxisCore(self.comm, self.state)
        self.indirect = IndirectHandler(self.comm)
        
        self.current_return_level = {}
        self.SAFE_REGISTERS = {
            'torque enable', 'operating mode', 'status return level',
            'return delay time', 'baud rate', 'id', 'homing offset'
        }

    @property
    def connected_motors(self):
        return self.comm.motor_mappers

    def auto_connect(self, baudrate=2000000):
        comm_success = self.comm.auto_connect(baudrate)
        if comm_success:
            print("[System] Resetting communication settings for stability...")
            for dxl_id in self.connected_motors.keys():
                self.single.write_data(dxl_id, 'return delay time', 0, mode="safe")
                self.single.write_data(dxl_id, 'status return level', 2, mode="safe")
                self.current_return_level[dxl_id] = 2
        return comm_success

    def FnF_write_mode_all(self):
        # print("[System] Switching to High-Speed Mode (Level 1)...")
        for dxl_id in self.connected_motors.keys():
            if self.current_return_level.get(dxl_id) == 1: continue
            self.single.write_data(dxl_id, 'status return level', 1, mode="safe")
            self.current_return_level[dxl_id] = 1

    def ACK_write_mode_all(self):
        # print("[System] Switching to ACK Mode (Level 2)...")
        for dxl_id in self.connected_motors.keys():
            if self.current_return_level.get(dxl_id) == 2: continue
            self.single.write_data(dxl_id, 'status return level', 2, mode="fast")
            self.current_return_level[dxl_id] = 2
    
    # -----------------------------------------------------------
    # Single Axis Wrappers
    # -----------------------------------------------------------
    def write(self, dxl_id, data_name, value):
        current_level = self.current_return_level.get(dxl_id, 2)
        if data_name in self.SAFE_REGISTERS:
            if current_level == 1:
                self.single.write_data(dxl_id, 'status return level', 2, mode="fast")
                res, err = self.single.write_safe_loop(dxl_id, data_name, value)
                self.single.write_data(dxl_id, 'status return level', 1, mode="safe")
                return res, err
            else:
                return self.single.write_safe_loop(dxl_id, data_name, value)
        else:
            if current_level == 1:
                self.single.write_data(dxl_id, data_name, value, mode="fast")
                return 0, 0
            else:
                return self.single.write_safe_loop(dxl_id, data_name, value)

    def read(self, dxl_id, data_name):
        return self.single.read_data(dxl_id, data_name)

    def set_operating_mode(self, dxl_id, mode_name):
        mode_map = {'current': 0, 'velocity': 1, 'position': 3, 'extended position': 4, 'current-based position': 5, 'pwm': 16}
        if mode_name not in mode_map: return False
        
        self.write(dxl_id, 'torque enable', 0)
        res, err = self.write(dxl_id, 'operating mode', mode_map[mode_name])
        if res == 0 and err == 0:
            print(f"[System] ID: {dxl_id}, Operation mode: {mode_name.upper()}")
            return True
        return False

    def close(self):
        self.comm.close_port()
        print("[System] Port closed safely.")

# Test
# =============================================================================
if __name__ == "__main__":
    import time
    import math
    import sys

    print("--- [Full-Stack Integration Test] dxl_gripper Facade ---")
    dxl = DynamixelManager()

    if not dxl.auto_connect(baudrate=2000000):
        print("[System] Error: Connection failed.")
        sys.exit()

    motor_ids = list(dxl.connected_motors.keys())

    id_1 = motor_ids[0]
    print(f"[System] Testing with IDs: {motor_ids}")

    try:
        for m_id in motor_ids:
            dxl.set_operating_mode(m_id, 'position')
            dxl.write(m_id, 'torque enable', 1)

        # ---------------------------------------------------------
        # 1. ACK Mode (Safe Single Control)
        # ---------------------------------------------------------
        print(f"\n[Mode 1] ACK Mode (Single Axis) - ID {id_1}")
        dxl.ACK_write_mode_all() # Return Level 2 setting
        dxl.write(id_1, 'goal position', 2048) # Write in ACK mode
        time.sleep(0.5)
        pos, _, _ = dxl.read(id_1, 'present position') # Read
        print(f" -> Result: {pos}")

        # ---------------------------------------------------------
        # 2. FnF Mode (High-Speed Single Control)
        # ---------------------------------------------------------
        print(f"\n[Mode 2] FnF Mode (Single Axis) - ID {id_1}")
        dxl.FnF_write_mode_all() # Return Level 1 setting
        dxl.write(id_1, 'goal position', 2500) # Write in FnF mode
        time.sleep(0.5)
        pos, _, _ = dxl.read(id_1, 'present position')  # Read
        print(f" -> Result: {pos}")
        dxl.ACK_write_mode_all()    # Return Level 2 setting if not use FnF mode

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        print("\n--- [System] Safety Shutdown ---")
        dxl.ACK_write_mode_all()
        for m_id in motor_ids:
            dxl.write(m_id, 'led', 0)
            dxl.write(m_id, 'torque enable', 0)
        dxl.close()

# ./venv/bin/python -m dxl_gripper.__init__