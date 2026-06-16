import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pcb_tester.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS serial_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            idn_command TEXT DEFAULT '*IDN?',
            idn_response TEXT DEFAULT '',
            baud_rate INTEGER DEFAULT 115200,
            data_bits INTEGER DEFAULT 8,
            stop_bits INTEGER DEFAULT 1,
            parity TEXT DEFAULT 'None',
            timeout REAL DEFAULT 2.0,
            notes TEXT DEFAULT '',
            ps_set_voltage_cmd TEXT DEFAULT 'PSV {value}',
            ps_set_current_cmd TEXT DEFAULT 'PSC {value}',
            ps_on_cmd TEXT DEFAULT 'PSON',
            ps_off_cmd TEXT DEFAULT 'PSOFF',
            ps_measure_cmd TEXT DEFAULT 'PSMEAS',
            ps_status_cmd TEXT DEFAULT 'PSSTATUS',
            ps_set_mode_cmd TEXT DEFAULT 'PSMODE {mode}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", "admin", "admin"),
        )

    # migrate: add PS command columns if missing
    existing_cols = [r[1] for r in cursor.execute("PRAGMA table_info(serial_devices)")]
    ps_cols = [
        ("ps_set_voltage_cmd", "TEXT DEFAULT 'PSV {value}'"),
        ("ps_set_current_cmd", "TEXT DEFAULT 'PSC {value}'"),
        ("ps_on_cmd",         "TEXT DEFAULT 'PSON'"),
        ("ps_off_cmd",        "TEXT DEFAULT 'PSOFF'"),
        ("ps_measure_cmd",    "TEXT DEFAULT 'PSMEAS'"),
        ("ps_status_cmd",     "TEXT DEFAULT 'PSSTATUS'"),
        ("ps_set_mode_cmd",   "TEXT DEFAULT 'PSMODE {mode}'"),
        ("ps_init_cmd",       "TEXT DEFAULT ''"),
    ]
    for col, dtype in ps_cols:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE serial_devices ADD COLUMN {col} {dtype}")

    conn.commit()
    conn.close()
