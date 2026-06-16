from models.device import Device
from utils.serial_manager import SerialManager


class DeviceController:
    def __init__(self):
        self.serial_mgr = SerialManager()

    def get_all_devices(self):
        return Device.get_all()

    def get_device(self, pk):
        return Device.get_by_id(pk)

    def add_device(self, device_id, name, idn_command="*IDN?",
                   idn_response="", baud_rate=115200, data_bits=8,
                   stop_bits=1, parity="None", timeout=2.0, notes="",
                   ps_set_voltage_cmd="PSV {value}",
                   ps_set_current_cmd="PSC {value}",
                   ps_on_cmd="PSON", ps_off_cmd="PSOFF",
                   ps_measure_cmd="PSMEAS", ps_status_cmd="PSSTATUS",
                   ps_set_mode_cmd="PSMODE {mode}",
                   ps_init_cmd=""):
        if not device_id.strip():
            return False, "Device ID cannot be empty"
        if not name.strip():
            return False, "Device name cannot be empty"
        existing = Device.get_by_device_id(device_id.strip())
        if existing:
            return False, f"Device ID '{device_id}' already exists"
        Device.create(device_id.strip(), name.strip(), idn_command.strip(),
                      idn_response.strip(), baud_rate, data_bits, stop_bits,
                      parity, timeout, notes.strip(),
                      ps_set_voltage_cmd, ps_set_current_cmd,
                      ps_on_cmd, ps_off_cmd, ps_measure_cmd,
                      ps_status_cmd, ps_set_mode_cmd, ps_init_cmd)
        return True, "Device added"

    def update_device(self, pk, **kwargs):
        Device.update(pk, **kwargs)
        return True, "Device updated"

    def delete_device(self, pk):
        self.serial_mgr.disconnect(pk)
        Device.delete(pk)
        return True, "Device deleted"

    def connect_device(self, pk, port):
        device = Device.get_by_id(pk)
        if not device:
            return False, "Device not found"
        return self.serial_mgr.connect(device, port)

    def disconnect_device(self, pk):
        self.serial_mgr.disconnect(pk)
        return True, "Disconnected"

    def is_connected(self, pk):
        return self.serial_mgr.is_connected(pk)

    def send_command(self, pk, command, terminator="\n"):
        conn = self.serial_mgr.get_connection(pk)
        if not conn:
            return False, "Device not connected"
        return conn.send_and_read(command, terminator)

    def auto_detect(self, pk):
        device = Device.get_by_id(pk)
        if not device:
            return False, "Device not found", []
        results = self.serial_mgr.auto_detect(device)
        if results:
            return True, "Found", results
        return False, "No matching port found", []

    def list_ports(self):
        return self.serial_mgr.list_ports()
