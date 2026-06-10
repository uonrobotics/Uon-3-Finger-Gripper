# =============================================================================
# 2. [dxl_gripper/dxl_mapping.py]
# The dxl_Mapper class acts as a comprehensive data container for a Dynamixel
# motor.
# 
# Especially, it maps NOT ONLY the motor's basic identification info
# --> (ID, model name, model number, firmware version)
# 
# BUT ALSO generates a full memory table for its specific memory addresses
# and data sizes of data name.
# --> ex) data name: 'goal position' -> address: 116, size: 4.
# 
# Key features include:
# 1) self.memory_table: Generates a mapped dictionary of the motor's memory 
#    addresses and data sizes.
# 
# 2) to_dict_info(): Returns a dictionary containing the motor's basic info 
#    (model name, model number, firmware version).
# 
# 3) get_addr_size(data_name): Returns the specific memory address and size 
#    when provided with a memory data name (string).
# =============================================================================

import os
import json
from .dxl_paths import CONFIG_DIR

MODEL_MAP = {
    1020: "XM430-W350-T",
    1030: "XM430-W210-T",
    1060: "XL430-W250-T",
    1070: "XC430-W150-T",
    1120: "XM540-W270-T",
    1130: "XM540-W150-T",
    1140: "XH540-V270-R",
}

class dxl_Mapper:
    def __init__(self, dxl_id, model_name, model_num, firmware_ver):
        self.id = dxl_id
        self.model_name = model_name
        self.model_number = model_num
        self.version = firmware_ver
        
        # dictionary of memory addresses and data sizes
        self.memory_table = self.to_dict_memory()
    
    def to_dict_memory(self):
        """return dxl memory table. self.memory_table will have the return automatically"""
        model_json_path = os.path.join(CONFIG_DIR, f'{self.model_name}.json')
        try:
            with open(model_json_path, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
                return {
                    'address': {**memory_data['eeprom'], **memory_data['ram']},
                    'size': memory_data['data size']
                }
        except FileNotFoundError:
            print(f"[Motor] Error: '{self.model_name}.json' not found.")
            return {'address': {}, 'size': {}}
        
    def to_dict_info(self):
        """return dictionary of motor info"""
        return {
            "model_name": self.model_name,
            "model_number": self.model_number,
            "firmware_version": self.version
        }

    def get_addr_size(self, data_name):
        """return address & size of data_name which is get from self.memory_table"""
        addr = self.memory_table['address'].get(data_name)
        size = self.memory_table['size'].get(f"{data_name} size")
        return addr, size

    def __str__(self):
        return f"[ID: {self.id:03d}] Model: {self.model_name} (FW: {self.version})"


# Test
# =============================================================================
if __name__ == "__main__":
    from pprint import pprint

    print("--- Testing dxl_motor.py ---")

    motor1 = dxl_Mapper(
        dxl_id=1, 
        model_name=MODEL_MAP[1130], 
        model_num=1130, 
        firmware_ver=49, 
    )

    print("\n[[Motor Object]]")
    print(motor1)

    print("\n[[Make info dict for robot_config.json]]")
    print(" ->", motor1.to_dict_info())

    print("\n[[Motor Object memory table]]")
    pprint(motor1.memory_table)

    print("\n[[dxl memory table Check]]")
    addr, size = motor1.get_addr_size('goal position')
    if addr is not None:
        print(f" -> 'goal position' address: {addr}, size: {size}")
        print(" -> [Success] Control Table JSON Loaded Successfully!")
    else:
        print(f" -> [Warning] Failed to load JSON. Check directory.")

# ./venv/bin/python -m dxl_gripper.dxl_mapping