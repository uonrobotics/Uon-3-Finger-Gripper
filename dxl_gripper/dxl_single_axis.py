# ===========================================================================
# 5. [dxl_gripper/dxl_single_axis.py]
# Dedicated module for single motor control.
# Handles individual read/write operations and delegates hardware error 
# recovery to the Centralized State Manager.
# ===========================================================================

import time
from dynamixel_sdk import COMM_SUCCESS

class SingleAxisCore:
    """Core Controller for Single Motor Reading and Writing"""
    def __init__(self, comm_manager, state_manager):
        self.comm = comm_manager
        # Dependency Injection: Delegates recovery and context caching
        self.state = state_manager

    def _get_addr_size(self, dxl_id, data_name):
        """Gets address and size from the motor mapper."""
        mapper = self.comm.motor_mappers.get(dxl_id)
        if not mapper: 
            return None, None
        return mapper.get_addr_size(data_name)

    def write_data(self, dxl_id, data_name, value, mode="safe"):
        """General-purpose single write (Safe/Fast)"""
        addr, size = self._get_addr_size(dxl_id, data_name)
        if addr is None: 
            print(f"[SingleAxis] Error: Cannot find address for '{data_name}'")
            return -1, 0
        
        if mode == "safe":
            comm_result, dxl_error = self.comm.write_safe(dxl_id, addr, size, value)
            if comm_result == COMM_SUCCESS and dxl_error == 0:
                # Report successful configuration to the State Manager
                self.state.update_cache(dxl_id, data_name, value)
            return comm_result, dxl_error
            
        elif mode == "fast":
            self.comm.write_fast(dxl_id, addr, size, value)
            return COMM_SUCCESS, 0

    def write_safe_loop(self, dxl_id, data_name, value, max_retries=3):
        """Write with retry loop and delegated restoration logic"""
        retries = max_retries
        while True:
            comm_result, dxl_error = self.write_data(dxl_id, data_name, value, mode="safe")
            if comm_result == COMM_SUCCESS and dxl_error == 0:
                return comm_result, dxl_error
            
            print(f"[SingleAxis] ID {dxl_id} Error (Comm: {comm_result}, HW: {dxl_error}). Retries: {retries}")
            if retries <= 0: 
                print(f"[SingleAxis] Critical: Recovery Failed for ID {dxl_id}.")
                return comm_result, dxl_error
                
            # Delegate recovery procedure to State Manager when a hardware error occurs
            if dxl_error != 0:
                self.state.clear_hardware_error(dxl_id)
                
            retries -= 1
    
    def read_data(self, dxl_id, data_name):
        """General-purpose single read"""
        addr, size = self._get_addr_size(dxl_id, data_name)
        if addr is None: 
            print(f"[SingleAxis] Error: Cannot find address for '{data_name}'")
            return None, -1, 0
        
        data, comm_result, dxl_error = self.comm.read(dxl_id, addr, size)
        
        if dxl_error != 0:
            print(f"[SingleAxis] Hardware Error detected during READ on ID {dxl_id}.")
            self.state.clear_hardware_error(dxl_id)
            
        return data, comm_result, dxl_error


# Test
# =============================================================================
if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dxl_gripper.dxl_comm import dxl_CommManager
    from dxl_gripper.dxl_state_manager import StateManager

    print("--- Testing dxl_single_axis.py ---")
    comm = dxl_CommManager()
    
    if comm.auto_connect():
        # Instantiate dependencies
        state_mgr = StateManager(comm)
        single_core = SingleAxisCore(comm, state_mgr)
        
        # Bring First Motor ID (with explicitly added!)
        test_id = list(comm.motor_mappers.keys())[0]
        print(f"\n[Test] Using Motor ID {test_id} for Single Axis Test.")
        
        # 1. Set Operation Mode & Torque Enable
        single_core.write_safe_loop(test_id, 'operating mode', 3)   # 3: position
        single_core.write_safe_loop(test_id, 'torque enable', 1)
        print(f"[Success] Torque Enabled on ID {test_id}")
        
        # 2. 'goal position' = 2048 (Safe Mode)
        print(f"[Test] Moving ID {test_id} to position 2048 (Safe)...")
        single_core.write_safe_loop(test_id, 'goal position', 2048)
        time.sleep(1)
        
        # 3. Read Data Test
        pos, res, err = single_core.read_data(test_id, 'present position')
        print(f"[Test] Present Position Read: {pos}")
        
        # 4. Teardown
        single_core.write_safe_loop(test_id, 'torque enable', 0)
        print(f"[Success] Torque Disabled. SingleAxisCore verified successfully!")
        
    comm.close_port()

# ./venv/bin/python -m dxl_gripper.dxl_single_axis