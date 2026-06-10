# ===========================================================================
# [dxl_gripper/dxl_indirect.py]
# Handles Indirect Address mapping to combine disjointed memory addresses
# (e.g., position, velocity, current) into a single contiguous block.
# Acts as an independent mapping expert used by both Single and Multi-axis modules.
# ===========================================================================

class IndirectHandler:
    """Mapping Expert for Indirect Address and Data Packing/Parsing"""
    def __init__(self, comm_manager):
        self.comm = comm_manager
        # Default base addresses for X-Series Protocol 2.0
        self.ind_addr_base = 168  # Indirect Address 1
        self.ind_data_base = 224  # Indirect Data 1
        
        # Stores the layout of mapped data to parse the byte array later
        self.layouts = {} # {group_name: {'start_addr': int, 'total_size': int, 'items': [(name, size)...]}}

    def setup_mapping(self, motor_ids, data_names, group_name="default_group"):
        """Maps a list of data names into the Indirect Address space."""
        total_size = 0
        items = []

        # 1. Analyze layout based on the first motor (Safely using!)
        ref_id = motor_ids[0]
        mapper = self.comm.motor_mappers.get(ref_id)
        if not mapper:
            raise ValueError(f"[Indirect] Error: Motor ID {ref_id} is not connected.")

        mapping_plan = [] # [(indirect_addr, target_addr), ...]
        current_ind_addr = self.ind_addr_base

        for name in data_names:
            target_addr, target_size = mapper.get_addr_size(name)
            if target_addr is None:
                raise ValueError(f"[Indirect] Error: Cannot find address for '{name}'")

            items.append((name, target_size))
            
            # Map each byte individually to the Indirect Address registers (2 bytes each)
            for i in range(target_size):
                mapping_plan.append((current_ind_addr, target_addr + i))
                current_ind_addr += 2
                total_size += 1

        self.layouts[group_name] = {
            'start_addr': self.ind_data_base,
            'total_size': total_size,
            'items': items
        }

        # 2. Write the mapping to all target motors
        print(f"[Indirect] Writing mapping for '{group_name}'... (Total: {total_size} bytes)")
        for dxl_id in motor_ids:
            for ind_addr, tgt_addr in mapping_plan:
                # Write to RAM for mapping using write_safe for stability (ACK required)
                self.comm.write_safe(dxl_id, ind_addr, 2, tgt_addr)

        return self.ind_data_base, total_size

    def parse_giant_integer(self, huge_int, group_name="default_group"):
        """Parses the giant integer returned by GroupSyncRead back into individual named values."""
        if group_name not in self.layouts:
            return {}

        layout = self.layouts[group_name]['items']
        parsed_result = {}
        current_shift = 0

        for name, size in layout:
            mask = (1 << (size * 8)) - 1
            value = (huge_int >> (current_shift * 8)) & mask

            if size == 4 and value > 0x7FFFFFFF:
                value -= 0x100000000
            elif size == 2 and value > 0x7FFF:
                value -= 0x10000

            parsed_result[name] = value
            current_shift += size

        return parsed_result
    
    def pack_data_to_bytes(self, data_dict, group_name="default_group"):
        """Packs a dictionary of data into a single byte array based on the mapped layout."""
        if group_name not in self.layouts:
            return []

        layout = self.layouts[group_name]['items']
        byte_array = []

        for name, size in layout:
            value = data_dict.get(name, 0) 
            
            if value < 0:
                value += (1 << (size * 8))

            for i in range(size):
                byte_array.append((value >> (i * 8)) & 0xFF)

        return byte_array


# Test
# =============================================================================
if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dxl_gripper.dxl_comm import dxl_CommManager

    print("--- Testing dxl_indirect.py ---")
    comm = dxl_CommManager()
    
    if comm.auto_connect():
        indirect = IndirectHandler(comm)
        motor_ids = list(comm.motor_mappers.keys())
        
        print(f"\n[Test] Setting up indirect mapping for IDs {motor_ids}...")
        
        # Disable torque before writing to indirect addresses (best practice)
        for m_id in motor_ids:
            tq_addr, tq_size = comm.motor_mappers[m_id].get_addr_size('torque enable')
            comm.write_safe(m_id, tq_addr, tq_size, 0)
        
        target_data = ['present current', 'present velocity', 'present position']
        start_addr, total_size = indirect.setup_mapping(motor_ids, target_data, "sensor_3set")
        
        print(f" -> Mapping Success! Start Address: {start_addr}, Total Size: {total_size} bytes.")
        print(f" -> Layout generated: {indirect.layouts['sensor_3set']['items']}")
        
        print("\n[Test] Simulating Packing & Parsing Data...")
        simulated_data = {'present current': -100, 'present velocity': 150, 'present position': 2048}
        print(f" -> Original Dictionary: {simulated_data}")
        
        # Pack to bytes
        packed_bytes = indirect.pack_data_to_bytes(simulated_data, "sensor_3set")
        print(f" -> Packed Byte Array: {packed_bytes}")
        
        # Simulate receiving a huge integer from SyncRead (combining bytes)
        simulated_huge_int = 0
        for i, b in enumerate(packed_bytes):
            simulated_huge_int |= (b << (i * 8))
        
        # Parse back to dictionary
        parsed_dict = indirect.parse_giant_integer(simulated_huge_int, "sensor_3set")
        print(f" -> Parsed Dictionary: {parsed_dict}")
        
        if simulated_data == parsed_dict:
            print("\n[Success] Packing and Parsing logic perfectly matched! IndirectHandler verified.")
        else:
            print("\n[Fail] Packing and Parsing mismatch!")
            
    comm.close_port()

# ./venv/bin/python -m dxl_gripper.dxl_indirect