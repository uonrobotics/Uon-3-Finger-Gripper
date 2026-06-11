from . import DynamixelManager


class uon_3f_gripper:
    DEFAULT_STROKE_LENGTH = 1800
    DEFAULT_STROKE_MIN = 0
    DEFAULT_STROKE_DISABLE_OFFSET = 100
    DEFAULT_GRASPING_FORCE_LIMIT = 1188

    def __init__(
        self,
        stroke_length=DEFAULT_STROKE_LENGTH,
        stroke_min=DEFAULT_STROKE_MIN,
        stroke_disable_offset=DEFAULT_STROKE_DISABLE_OFFSET,
        grasping_force_limit=DEFAULT_GRASPING_FORCE_LIMIT,
    ):
        self.STROKE_LENGTH = stroke_length
        self.STROKE_MIN = stroke_min
        self.STROKE_MAX = self.STROKE_MIN + self.STROKE_LENGTH
        self.STROKE_DISABLE = self.STROKE_MIN + stroke_disable_offset
        self.GRASPING_FORCE_LIMIT = grasping_force_limit

        self.flag_enable = False
        self.dxl = None
        self.dxl_ids = []
        self.id_0 = None

        self.last_force = None

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))

    def _clamp_force(self, value):
        return self._clamp(value, 0, self.GRASPING_FORCE_LIMIT)

    def _clamp_stroke(self, value):
        return self._clamp(value, self.STROKE_MIN, self.STROKE_MAX)

    def connect(self):
        self.dxl = DynamixelManager()
        if not self.dxl.auto_connect():
            print("[System] Failed to connect to Dynamixel.")
            return False

        self.dxl_ids = list(self.dxl.connected_motors.keys())
        if not self.dxl_ids:
            print("[System] No Dynamixel motors found.")
            return False

        self.id_0 = self.dxl_ids[0]
        print(f"[System] Motor connected. ID: {self.id_0}")
        return True

    def enable(self):
        if not self.flag_enable and self.dxl and self.id_0 is not None:
            self.dxl.ACK_write_mode_all()
            self.dxl.set_operating_mode(self.id_0, 'current-based position')
            self.dxl.write(self.id_0, 'current limit', self.GRASPING_FORCE_LIMIT)
            self.dxl.write(self.id_0, 'torque enable', 1)
            self.flag_enable = True

    def disable(self):
        if self.flag_enable and self.dxl and self.id_0 is not None:
            self.dxl.ACK_write_mode_all()
            self.dxl.write(self.id_0, 'goal position', self.STROKE_DISABLE)
            self.dxl.write(self.id_0, 'torque enable', 0)
            self.flag_enable = False

    def open(self, force=50):
        if self.flag_enable:
            self.dxl.FnF_write_mode_all()
            self.dxl.write(self.id_0, 'goal position', self.STROKE_MAX)
            self.dxl.write(self.id_0, 'goal current', self._clamp_force(force))
            self.dxl.ACK_write_mode_all()

    def close(self, force=50):
        if self.flag_enable:
            self.dxl.FnF_write_mode_all()
            self.dxl.write(self.id_0, 'goal position', self.STROKE_MIN)
            self.dxl.write(self.id_0, 'goal current', self._clamp_force(force))
            self.dxl.ACK_write_mode_all()

    def stroke(self, pos, max_effort=50):
        if self.flag_enable:
            self.dxl.FnF_write_mode_all()
            self.dxl.write(self.id_0, 'goal position', self._clamp_stroke(pos))
            if self.last_force != max_effort:
                self.dxl.write(self.id_0, 'goal current', self._clamp_force(max_effort))
                self.last_force = max_effort

            self.dxl.ACK_write_mode_all()

    def get_position(self):
        if self.dxl and self.id_0 is not None:
            pos, _, _ = self.dxl.read(self.id_0, 'present position')
            return pos
        return None

    def get_current(self):
        if self.dxl and self.id_0 is not None:
            current, _, _ = self.dxl.read(self.id_0, 'present current')
            return current
        return None

    def cleanup(self):
        if self.dxl is not None:
            self.dxl.ACK_write_mode_all()
            for dxl_id in self.dxl_ids:
                self.dxl.write(dxl_id, 'led', 0)
                self.dxl.write(dxl_id, 'torque enable', 0)
            self.dxl.close()
