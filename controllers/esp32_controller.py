import time
from models.device import Device
from controllers.device_controller import DeviceController
from utils.serial_manager import SerialManager


class ESP32Controller:
    ESP32_DEVICE_ID = "ESP32_RELAY_BOARD"
    ESP32_NAME = "ESP32 Relay + Buzzer"
    ESP32_IDN_CMD = "PING"
    ESP32_IDN_RESP = "PONG"
    ESP32_BAUD = 115200

    def __init__(self, device_controller: DeviceController = None):
        self.dc = device_controller or DeviceController()
        self.device_pk = None
        self._relay_states = [False] * 8
        self._ps_output_on = False
        self._ensure_device()

    def _ensure_device(self):
        device = Device.get_by_device_id(self.ESP32_DEVICE_ID)
        if not device:
            pk = Device.create(
                device_id=self.ESP32_DEVICE_ID,
                name=self.ESP32_NAME,
                idn_command=self.ESP32_IDN_CMD,
                idn_response=self.ESP32_IDN_RESP,
                baud_rate=self.ESP32_BAUD,
            )
            self.device_pk = pk
        else:
            self.device_pk = device.id

    def get_pk(self):
        return self.device_pk

    def connect(self, port: str) -> tuple:
        ok, msg = self.dc.connect_device(self.device_pk, port)
        if ok:
            if self.ping():
                return True, f"ESP32 connected on {port}"
            self.disconnect()
            return False, "Connected but PING failed — not an ESP32?"
        return False, msg

    def auto_detect(self) -> tuple:
        ports = SerialManager.list_ports()
        for port in ports:
            try:
                import serial as _serial
                s = _serial.Serial(port=port, baudrate=self.ESP32_BAUD,
                                   timeout=2, write_timeout=2)
                time.sleep(0.3)
                s.reset_input_buffer()
                s.write(b"PING\n")
                time.sleep(0.3)
                resp = s.read_all().decode(errors="replace").strip()
                s.close()
                if "PONG" in resp:
                    return self.connect(port)
            except Exception:
                continue
        return False, "No ESP32 found on any port"

    def disconnect(self):
        self.dc.disconnect_device(self.device_pk)
        self._relay_states = [False] * 8
        self._ps_output_on = False

    def is_connected(self) -> bool:
        return self.dc.is_connected(self.device_pk)

    def ping(self) -> bool:
        ok, resp = self.dc.send_command(self.device_pk, "PING")
        return ok and "PONG" in resp

    def set_relays(self, pattern) -> tuple:
        if isinstance(pattern, int):
            pattern = format(pattern, '08b')
        if len(pattern) != 8 or not all(c in '01' for c in pattern):
            return False, "Pattern must be 8-bit binary (e.g. 11000000)"
        ok, resp = self.dc.send_command(self.device_pk, pattern)
        if ok:
            self._relay_states = [c == '1' for c in pattern]
        return ok, resp

    def set_relay(self, index: int, state: bool) -> tuple:
        if not 0 <= index <= 7:
            return False, "Relay index must be 0-7"
        self._relay_states[index] = state
        pattern = ''.join('1' if s else '0' for s in self._relay_states)
        return self.set_relays(pattern)

    def relay_on(self, index: int) -> tuple:
        return self.set_relay(index, True)

    def relay_off(self, index: int) -> tuple:
        return self.set_relay(index, False)

    def all_on(self) -> tuple:
        return self.set_relays("11111111")

    def all_off(self) -> tuple:
        return self.set_relays("00000000")

    def get_relay_states(self) -> list:
        return list(self._relay_states)

    def buzzer(self, cycles: int, on_time: int, off_time: int) -> tuple:
        if cycles < 1 or on_time < 1 or off_time < 1:
            return False, "All values must be >= 1"
        cycles = min(cycles, 99)
        on_time = min(on_time, 99)
        off_time = min(off_time, 99)
        cmd = f"BZR-{cycles:02d}-{on_time:02d}-{off_time:02d}"
        return self.dc.send_command(self.device_pk, cmd)

    # --- Power Supply Control ---

    def ps_set_voltage(self, voltage: float) -> tuple:
        if voltage < 0 or voltage > 30:
            return False, "Voltage must be 0-30V"
        cmd = f"PSV {voltage:05.2f}"
        return self.dc.send_command(self.device_pk, cmd)

    def ps_set_current(self, current: float) -> tuple:
        if current < 0 or current > 5:
            return False, "Current must be 0-5A"
        cmd = f"PSC {current:05.2f}"
        return self.dc.send_command(self.device_pk, cmd)

    def ps_on(self) -> tuple:
        ok, resp = self.dc.send_command(self.device_pk, "PSON")
        if ok:
            self._ps_output_on = True
        return ok, resp

    def ps_off(self) -> tuple:
        ok, resp = self.dc.send_command(self.device_pk, "PSOFF")
        if ok:
            self._ps_output_on = False
        return ok, resp

    def ps_set_mode(self, mode: str) -> tuple:
        mode = mode.upper()
        if mode not in ("CV", "CC", "CONSTANT_VOLTAGE", "CONSTANT_CURRENT"):
            return False, "Mode must be CV or CC"
        cmd = f"PSMODE {mode}"
        return self.dc.send_command(self.device_pk, cmd)

    def ps_measure(self) -> tuple:
        ok, resp = self.dc.send_command(self.device_pk, "PSMEAS")
        if ok and "OK:V=" in resp:
            try:
                parts = resp.replace("OK:V=", "").split(",I=")
                v = float(parts[0])
                c = float(parts[1])
                return True, (v, c)
            except Exception:
                pass
            return True, resp
        return ok, resp

    def ps_status(self) -> tuple:
        ok, resp = self.dc.send_command(self.device_pk, "PSSTATUS")
        return ok, resp
