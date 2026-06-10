# =============================================================================
# 3. [dxl_gripper/dxl_comm.py]
# The dxl_CommManager class acts as the low-level communication manager, 
# dedicated to port connection and packet transmission with Dynamixel motors.
# 
# Key features include:
# 1) Motor Connection & Mapping: Executes auto_connect() to scan for devices and 
#    populate dictionary self.motor_mappers ({ID, dxl_Mapper class}).
#    This dictionary is essential for accessing specific motor IDs and
#    retrieving their memory addresses.
#
# 2) Core I/O Primitives: Provides write_safe() and write_fast() functions, 
#    which serve as the foundational write operations for the upper-level dxl_Core.
#    Also read() and reboot() functions are provided.
#
#  3) Port & Packet Handling: Directly interfaces with the SDK's PortHandler and 
#    PacketHandler to manage low-level hardware communication.
# =============================================================================

import os
import json
import serial.tools.list_ports
from dynamixel_sdk import *

from .dxl_mapping import dxl_Mapper, MODEL_MAP
from .dxl_paths import CONFIG_DIR, ROBOT_CONFIG_PATH

class dxl_CommManager:
    """Port & Packet Handling, Motor Connection Management"""
    def __init__(self, protocol_version=2.0):
        self.packetHandler = PacketHandler(protocol_version)
        self.portHandler = None
        self.is_connected = False

        # motor_mappers: dictionary of motor ID (key) and dxl_Mapper object (value).
        # Populated when auto_connect() is executed.
        # Accesses the dxl_Mapper for a specific motor ID.
        # ex) mapper = self.comm.motor_mappers.get(dxl_id)
        self.motor_mappers: dict[int, dxl_Mapper] = {}

    def open_port(self, port_name, baudrate):
        """open port and set baudrate"""
        selected_port = PortHandler(port_name)
        try:
            if selected_port.openPort():
                if selected_port.setBaudRate(baudrate):
                    self.portHandler = selected_port
                    self.is_connected = True
                    return True
                else:
                    print(f"[Warning] Failed to set baudrate {baudrate} on {port_name}")
                    selected_port.closePort()
        except Exception:
            try: selected_port.closePort()
            except: pass
        return False
    
    def close_port(self):
        """close port"""
        if self.portHandler and self.is_connected:
            self.portHandler.closePort()
            self.is_connected = False
            self.motor_mappers.clear()
    
    def ping(self, dxl_id):
        """send ping to verify motor connection with certain ID"""
        _, comm_result, _ = self.packetHandler.ping(self.portHandler, dxl_id)
        return comm_result == COMM_SUCCESS
    
    def broadcast_ping(self):
        """send broadcast ping to verify connected motors"""
        return self.packetHandler.broadcastPing(self.portHandler)

    def _load_robot_config(self):
        """return saved motor info & motor ids from robot_config.json"""
        if not os.path.exists(ROBOT_CONFIG_PATH):
            return {}, []
        try:
            with open(ROBOT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                saved_info = json.load(f)
                saved_motor_ids = [int(id_str) for id_str in saved_info.keys()]
                return saved_info, saved_motor_ids
        except Exception:
            return {}, []

    def _save_robot_config(self):
        """make robot_config.json from self.motor_mappers"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        id_info_dict = {str(id): mapper_obj.to_dict_info() for id, mapper_obj in self.motor_mappers.items()}
        with open(ROBOT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(id_info_dict, f, indent=4)
        print("[dxl_CommManager] Robot configuration saved successfully.")

    def auto_connect(self, baudrate=2000000):
        """Automatically connects motors & make self.motor_mappers"""
        print("[dxl_CommManager] Searching for Dynamixel...")
        
        saved_info, saved_motor_ids = self._load_robot_config()
        ports = [port.device for port in serial.tools.list_ports.comports()]

        for port_name in ports:
            if 'ttyS' in port_name: 
                continue 
            
            if self.open_port(port_name, baudrate):
                
                # 1. JSON based verification
                if saved_motor_ids:
                    all_verified = all(self.ping(m_id) for m_id in saved_motor_ids)
                    if all_verified:
                        print(f"[Success] Port {port_name} Verified from JSON!")
                        for dxl_id_str, info in saved_info.items():
                            dxl_id = int(dxl_id_str)
                            self.motor_mappers[dxl_id] = dxl_Mapper(
                                dxl_id,
                                info['model_name'],
                                info['model_number'],
                                info['firmware_version']
                            )
                        return True
                    else:
                        self.close_port()
                        continue
                        
                # 2. Scan all (Broadcast Ping)
                dxl_list, comm_result = self.broadcast_ping()
                if comm_result == COMM_SUCCESS and dxl_list:
                    for dxl_id, data in dxl_list.items():
                        model_num, firmware_ver = data[0], data[1]
                        if model_num in MODEL_MAP:
                            model_name = MODEL_MAP[model_num]
                            self.motor_mappers[dxl_id] = dxl_Mapper(
                                dxl_id,
                                model_name,
                                model_num,
                                firmware_ver
                            )
                    
                    # Check if there are actually registered motors
                    if not self.motor_mappers:
                        print(f"[Fail] Port {port_name}: Devices found, but no supported models.")
                        self.close_port()
                        continue

                    print(f"[Success] Port {port_name} Connected via Scan!")
                    self._save_robot_config()
                    return True
                else:
                    self.close_port()
                    
        print("[Fail] Could not connect automatically.")
        return False
    
    def write_safe(self, dxl_id, address, data_size, value):
        if data_size == 1:
            return self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, address, value)
        elif data_size == 2:
            return self.packetHandler.write2ByteTxRx(self.portHandler, dxl_id, address, value)
        elif data_size == 4:
            return self.packetHandler.write4ByteTxRx(self.portHandler, dxl_id, address, value)
        return COMM_TX_ERROR, 0
    
    def write_fast(self, dxl_id, address, data_size, value):
        if data_size == 1:
            self.packetHandler.write1ByteTxOnly(self.portHandler, dxl_id, address, value)
        elif data_size == 2:
            self.packetHandler.write2ByteTxOnly(self.portHandler, dxl_id, address, value)
        elif data_size == 4:
            self.packetHandler.write4ByteTxOnly(self.portHandler, dxl_id, address, value)

    def read(self, dxl_id, address, data_size):
        if data_size == 1:
            data, comm_result, dxl_error = self.packetHandler.read1ByteTxRx(self.portHandler, dxl_id, address)
        elif data_size == 2:
            data, comm_result, dxl_error = self.packetHandler.read2ByteTxRx(self.portHandler, dxl_id, address)
        elif data_size == 4:
            data, comm_result, dxl_error = self.packetHandler.read4ByteTxRx(self.portHandler, dxl_id, address)
        else:
            return 0, COMM_TX_ERROR, 0

        # Change SDK return value as Signed
        if data_size == 4 and data > 0x7FFFFFFF:
            data -= 0x100000000
        elif data_size == 2 and data > 0x7FFF:
            data -= 0x10000
            
        return data, comm_result, dxl_error
    
    def reboot(self, dxl_id):
        self.packetHandler.reboot(self.portHandler, dxl_id)


# Test
# =============================================================================
if __name__=="__main__":
    from pprint import pprint

    print("--- Testing dxl_CommManager.py ---")
    
    dxl = dxl_CommManager()

    if dxl.auto_connect():
        print("\n[Result] Connected Motors Info:")
        for m_id, motor_info in dxl.motor_mappers.items():
            print(f" -> {motor_info}")
            addr, size = motor_info.get_addr_size('goal position')
            print(f"    * Goal Position Addr: {addr}, Size: {size}")
        
        print("\n")
        pprint(dxl.motor_mappers)
            
    dxl.close_port()

# ./venv/bin/python -m dxl_gripper.dxl_comm