import serial
import serial.tools.list_ports
import time
import threading
from models.device import Device


class SerialConnection:
    def __init__(self, device: Device, port: str):
        self.device = device
        self.port = port
        self._serial: serial.Serial = None
        self._lock = threading.Lock()
        self._open()

    def _open(self):
        parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN,
                      "Odd": serial.PARITY_ODD}
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.device.baud_rate,
            bytesize=self.device.data_bits,
            stopbits=self.device.stop_bits,
            parity=parity_map.get(self.device.parity, serial.PARITY_NONE),
            timeout=self.device.timeout,
            write_timeout=self.device.timeout,
        )
        time.sleep(0.5)

    @property
    def is_open(self):
        return self._serial is not None and self._serial.is_open

    def send(self, command: str, terminator: str = "\n") -> tuple:
        with self._lock:
            if not self.is_open:
                return False, "Not connected"
            try:
                self._serial.reset_input_buffer()
                payload = command + terminator
                self._serial.write(payload.encode())
                return True, ""
            except Exception as e:
                return False, str(e)

    def send_raw(self, data: bytes) -> tuple:
        with self._lock:
            if not self.is_open:
                return False, "Not connected"
            try:
                self._serial.reset_input_buffer()
                self._serial.write(data)
                return True, ""
            except Exception as e:
                return False, str(e)

    def read_line(self) -> tuple:
        with self._lock:
            if not self.is_open:
                return False, ""
            try:
                line = self._serial.readline().decode(errors="replace").strip()
                return (True, line) if line else (False, "")
            except Exception as e:
                return False, f"<read error: {e}>"

    def read_all(self) -> tuple:
        with self._lock:
            if not self.is_open:
                return False, ""
            try:
                data = self._serial.read_all().decode(errors="replace")
                return (True, data) if data else (False, "")
            except Exception as e:
                return False, f"<read error: {e}>"

    def send_and_read(self, command: str, terminator: str = "\n") -> tuple:
        ok, err = self.send(command, terminator)
        if not ok:
            return False, err
        time.sleep(0.2)
        _, data = self.read_all()
        return True, data

    def close(self):
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception:
                    pass


class SerialManager:
    def __init__(self):
        self._connections: dict[int, SerialConnection] = {}

    def get_connection(self, device_id: int) -> SerialConnection:
        return self._connections.get(device_id)

    def connect(self, device: Device, port: str) -> tuple:
        if device.id in self._connections:
            self._connections[device.id].close()

        try:
            conn = SerialConnection(device, port)
            self._connections[device.id] = conn
            return True, f"Connected on {port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self, device_id: int):
        conn = self._connections.pop(device_id, None)
        if conn:
            conn.close()

    def disconnect_all(self):
        for conn in self._connections.values():
            conn.close()
        self._connections.clear()

    def is_connected(self, device_id: int) -> bool:
        conn = self._connections.get(device_id)
        return conn is not None and conn.is_open

    @staticmethod
    def list_ports() -> list:
        return [p.device for p in serial.tools.list_ports.comports()]

    @staticmethod
    def scan_port(port: str, device: Device) -> tuple:
        try:
            s = serial.Serial(
                port=port,
                baudrate=device.baud_rate,
                bytesize=device.data_bits,
                stopbits=device.stop_bits,
                timeout=device.timeout,
                write_timeout=device.timeout,
            )
            time.sleep(0.5)
            s.reset_input_buffer()
            cmd = (device.idn_command + "\n").encode()
            s.write(cmd)
            time.sleep(0.3)
            resp = s.read_all().decode(errors="replace").strip()
            s.close()

            if not resp:
                return False, ""

            expected = device.idn_response.strip()
            if expected and expected.lower() in resp.lower():
                return True, resp
            if not expected and resp:
                return True, resp

            return False, resp
        except Exception:
            return False, ""

    @staticmethod
    def auto_detect(device: Device, scan_bauds=None) -> list:
        if scan_bauds is None:
            from utils.constants import SCAN_BAUD_RATES
            scan_bauds = SCAN_BAUD_RATES

        available_ports = SerialManager.list_ports()
        results = []

        for port in available_ports:
            for baud in [device.baud_rate] + [b for b in scan_bauds if b != device.baud_rate]:
                try:
                    s = serial.Serial(port=port, baudrate=baud,
                                      timeout=2, write_timeout=2)
                    time.sleep(0.3)
                    s.reset_input_buffer()
                    cmd = (device.idn_command + "\n").encode()
                    s.write(cmd)
                    time.sleep(0.3)
                    resp = s.read_all().decode(errors="replace").strip()
                    s.close()

                    expected = device.idn_response.strip()
                    if expected and expected.lower() in resp.lower():
                        results.append((port, baud, resp))
                        break
                    elif resp and not expected:
                        results.append((port, baud, resp))
                        break
                except Exception:
                    continue

        return results
