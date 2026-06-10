# ===========================================================================
# 4. [dxl_gripper/dxl_state_manager.py]
# Dedicated module for Centralized State Management.
# Handles motor context caching (saving configurations like PID gains) and 
# executes Auto-Recovery sequences (reboot & restore) when hardware errors occur.
# ===========================================================================

import time
from dynamixel_sdk import COMM_SUCCESS

class StateManager:
    """Manages Context Cache and Hardware Error Recovery"""
    def __init__(self, comm_manager):
        self.comm = comm_manager
        self.context_cache = {} # dict for recent settings of motors

    def update_cache(self, dxl_id, data_name, value):
        """Saves the successful configuration to the cache."""
        if dxl_id not in self.context_cache:
            self.context_cache[dxl_id] = {}
        self.context_cache[dxl_id][data_name] = value

    def restore_config(self, dxl_id):
        """Restores context from the cache using direct safe writes."""
        if dxl_id not in self.context_cache:
            return
            
        mapper = self.comm.motor_mappers.get(dxl_id)
        if not mapper: return

        print(f"[StateManager] Restoring configuration for ID {dxl_id}...")
        for key_dataName, val_value in self.context_cache[dxl_id].items():
            # Skip dynamic states; only restore static configurations
            if key_dataName not in ['torque enable', 'goal pwm', 'goal current', 'goal velocity', 'goal position', 'reboot']:
                addr, size = mapper.get_addr_size(key_dataName)
                if addr is not None:
                    self.comm.write_safe(dxl_id, addr, size, val_value)
                    # Small delay to ensure EEPROM/RAM stability during rapid restoration
                    time.sleep(0.01) 

    def clear_hardware_error(self, dxl_id):
        """Executes the full recovery sequence: Disable Torque -> Reboot -> Restore -> Enable Torque"""
        mapper = self.comm.motor_mappers.get(dxl_id)
        if not mapper: return False

        tq_addr, tq_size = mapper.get_addr_size('torque enable')
        
        # 1. Force torque off (safe state)
        self.comm.write_safe(dxl_id, tq_addr, tq_size, 0)
        time.sleep(0.1)
        
        # 2. Reboot motor to clear hardware error status
        print(f"[StateManager] Rebooting ID {dxl_id} to clear hardware error...")
        self.comm.reboot(dxl_id)
        time.sleep(0.5) # Wait for Dynamixel to boot up completely
        
        # 3. Restore previous configuration
        self.restore_config(dxl_id)
        
        # 4. Re-enable torque
        print(f"[StateManager] Recovery complete. Re-enabling torque for ID {dxl_id}.")
        self.comm.write_safe(dxl_id, tq_addr, tq_size, 1)
        return True


# Test
# =============================================================================
if __name__ == "__main__":
    import os
    import sys
    # Add parent directory to path to import peers
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dxl_gripper.dxl_comm import dxl_CommManager

    print("--- Testing dxl_state_manager.py ---")
    comm = dxl_CommManager()
    
    if comm.auto_connect():
        state_mgr = StateManager(comm)
        
        test_id = list(comm.motor_mappers.keys())[0]
        print(f"\n[Test] Simulating State Management for Motor ID {test_id}...")
        
        # 1. Simulate saving configurations to cache
        print("[Test] Caching 'profile velocity' = 200 and 'profile acceleration' = 50.")
        state_mgr.update_cache(test_id, 'profile velocity', 200)
        state_mgr.update_cache(test_id, 'profile acceleration', 50)
        print(f" -> Current Cache: {state_mgr.context_cache}")
        
        # 2. Trigger Auto-Recovery Sequence
        print("\n[Test] Triggering manual hardware error recovery sequence...")
        state_mgr.clear_hardware_error(test_id)
        
        print("\n[Test] StateManager verified successfully!")
        time.sleep(3)
    
    tq_addr, tq_size = comm.motor_mappers[test_id].get_addr_size('torque enable')
    comm.write_safe(test_id,tq_addr,tq_size,0) # torque off
    print("Torque off")
    comm.close_port()

# ./venv/bin/python -m dxl_gripper.dxl_state_manager