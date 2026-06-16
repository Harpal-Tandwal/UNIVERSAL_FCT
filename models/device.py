from database.db_manager import get_connection


class Device:
    def __init__(self, row=None):
        if row:
            r = dict(row)
            self.id = r["id"]
            self.device_id = r["device_id"]
            self.name = r["name"]
            self.idn_command = r["idn_command"]
            self.idn_response = r["idn_response"]
            self.baud_rate = r["baud_rate"]
            self.data_bits = r["data_bits"]
            self.stop_bits = r["stop_bits"]
            self.parity = r["parity"]
            self.timeout = r["timeout"]
            self.notes = r["notes"]
            self.ps_set_voltage_cmd = r.get("ps_set_voltage_cmd", "PSV {value}")
            self.ps_set_current_cmd = r.get("ps_set_current_cmd", "PSC {value}")
            self.ps_on_cmd = r.get("ps_on_cmd", "PSON")
            self.ps_off_cmd = r.get("ps_off_cmd", "PSOFF")
            self.ps_measure_cmd = r.get("ps_measure_cmd", "PSMEAS")
            self.ps_status_cmd = r.get("ps_status_cmd", "PSSTATUS")
            self.ps_set_mode_cmd = r.get("ps_set_mode_cmd", "PSMODE {mode}")
            self.ps_init_cmd = r.get("ps_init_cmd", "")
            self.created_at = r["created_at"]
            self.updated_at = r["updated_at"]

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM serial_devices ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [Device(row) for row in rows]

    @staticmethod
    def get_by_id(device_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM serial_devices WHERE id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Device(row)
        return None

    @staticmethod
    def get_by_device_id(device_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM serial_devices WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Device(row)
        return None

    @staticmethod
    def create(device_id, name, idn_command="*IDN?", idn_response="",
               baud_rate=115200, data_bits=8, stop_bits=1,
               parity="None", timeout=2.0, notes="",
               ps_set_voltage_cmd="PSV {value}",
               ps_set_current_cmd="PSC {value}",
               ps_on_cmd="PSON", ps_off_cmd="PSOFF",
               ps_measure_cmd="PSMEAS", ps_status_cmd="PSSTATUS",
               ps_set_mode_cmd="PSMODE {mode}",
               ps_init_cmd=""):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO serial_devices
                (device_id, name, idn_command, idn_response, baud_rate,
                 data_bits, stop_bits, parity, timeout, notes,
                 ps_set_voltage_cmd, ps_set_current_cmd,
                 ps_on_cmd, ps_off_cmd, ps_measure_cmd,
                 ps_status_cmd, ps_set_mode_cmd, ps_init_cmd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, name, idn_command, idn_response, baud_rate,
              data_bits, stop_bits, parity, timeout, notes,
              ps_set_voltage_cmd, ps_set_current_cmd,
              ps_on_cmd, ps_off_cmd, ps_measure_cmd,
              ps_status_cmd, ps_set_mode_cmd, ps_init_cmd))
        conn.commit()
        pk = cursor.lastrowid
        conn.close()
        return pk

    @staticmethod
    def update(pk, **kwargs):
        allowed = {"device_id", "name", "idn_command", "idn_response",
                   "baud_rate", "data_bits", "stop_bits", "parity",
                   "timeout", "notes",
                   "ps_set_voltage_cmd", "ps_set_current_cmd",
                   "ps_on_cmd", "ps_off_cmd", "ps_measure_cmd",
                   "ps_status_cmd", "ps_set_mode_cmd", "ps_init_cmd"}
        conn = get_connection()
        cursor = conn.cursor()
        fields = []
        values = []
        for key, val in kwargs.items():
            if key in allowed:
                fields.append(f"{key} = ?")
                values.append(val)
        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(pk)
            cursor.execute(
                f"UPDATE serial_devices SET {', '.join(fields)} WHERE id = ?",
                values
            )
            conn.commit()
        conn.close()

    @staticmethod
    def delete(pk):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM serial_devices WHERE id = ?", (pk,))
        conn.commit()
        conn.close()
