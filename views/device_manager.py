import customtkinter as ctk
from tkinter import ttk, messagebox
from controllers.device_controller import DeviceController
from utils.constants import DEFAULT_BAUD_RATES


class DeviceManagerView(ctk.CTkFrame):
    def __init__(self, parent, auth_controller, device_controller: DeviceController):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.controller = device_controller
        self.selected_device_id = None
        self._terminal_refresh = None
        self.setup_ui()
        self.load_devices()

    def set_terminal_refresh(self, callback):
        self._terminal_refresh = callback

    def _notify_terminal(self):
        if self._terminal_refresh:
            self._terminal_refresh()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self, width=280)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_frame, text="Serial Devices",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=5)

        columns = ("ID", "Name", "Device ID")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=35)
        self.tree.heading("Name", text="Name")
        self.tree.column("Name", width=120)
        self.tree.heading("Device ID", text="Device ID")
        self.tree.column("Device ID", width=100)
        self.tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(left_frame, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ctk.CTkButton(btn_frame, text="Delete", command=self.delete_device,
                       fg_color="red", width=80).grid(row=0, column=0, padx=3)

        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_columnconfigure(1, weight=1)

        tab_view = ctk.CTkTabview(right_frame)
        tab_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.config_tab = tab_view.add("Configuration")
        self.connect_tab = tab_view.add("Connection")

        self.setup_config_tab()
        self.setup_connect_tab()

    def setup_config_tab(self):
        self.config_tab.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(self.config_tab, text="Device ID:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.device_id_var = ctk.StringVar()
        ctk.CTkEntry(self.config_tab, textvariable=self.device_id_var).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Name:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(self.config_tab, textvariable=self.name_var).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="IDN Command:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.idn_cmd_var = ctk.StringVar(value="*IDN?")
        ctk.CTkEntry(self.config_tab, textvariable=self.idn_cmd_var).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Expected IDN Response:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.idn_resp_var = ctk.StringVar()
        ctk.CTkEntry(self.config_tab, textvariable=self.idn_resp_var).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="").grid(row=row, column=0)
        ctk.CTkLabel(self.config_tab, text="(used for auto-detect; leave blank to skip check)",
                      font=ctk.CTkFont(size=11), text_color="gray").grid(row=row, column=1, sticky="w")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Baud Rate:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.baud_var = ctk.StringVar(value="115200")
        baud_menu = ctk.CTkOptionMenu(self.config_tab, variable=self.baud_var,
                                       values=[str(b) for b in DEFAULT_BAUD_RATES])
        baud_menu.grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Parity:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.parity_var = ctk.StringVar(value="None")
        ctk.CTkOptionMenu(self.config_tab, variable=self.parity_var,
                           values=["None", "Even", "Odd"]).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Data Bits:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.data_var = ctk.StringVar(value="8")
        ctk.CTkOptionMenu(self.config_tab, variable=self.data_var,
                           values=["5", "6", "7", "8"]).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Stop Bits:").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.stop_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(self.config_tab, variable=self.stop_var,
                           values=["1", "1.5", "2"]).grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Timeout (s):").grid(row=row, column=0, pady=4, padx=5, sticky="e")
        self.timeout_var = ctk.StringVar(value="2.0")
        ctk.CTkEntry(self.config_tab, textvariable=self.timeout_var, width=80).grid(row=row, column=1, pady=4, padx=5, sticky="w")
        row += 1

        ctk.CTkLabel(self.config_tab, text="Notes:").grid(row=row, column=0, pady=4, padx=5, sticky="ne")
        self.notes_text = ctk.CTkTextbox(self.config_tab, height=50)
        self.notes_text.grid(row=row, column=1, pady=4, padx=5, sticky="ew")
        row += 1

        sep = ctk.CTkFrame(self.config_tab, height=2, fg_color="gray")
        sep.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6, padx=5)
        row += 1

        ctk.CTkLabel(self.config_tab, text="Power Supply Commands",
                      font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, columnspan=2, pady=2)
        row += 1
        ctk.CTkLabel(self.config_tab, text="Use {value} for Set V/I, {mode} for CV/CC",
                      font=ctk.CTkFont(size=10), text_color="gray").grid(row=row, column=0, columnspan=2, pady=2)
        row += 1

        ps_fields = [
            ("Init Cmd:",    "ps_init_cmd"),
            ("Set Voltage:", "ps_set_voltage_cmd"),
            ("Set Current:", "ps_set_current_cmd"),
            ("Measure:",     "ps_measure_cmd"),
            ("Status:",      "ps_status_cmd"),
            ("Output ON:",   "ps_on_cmd"),
            ("Output OFF:",  "ps_off_cmd"),
            ("Set Mode:",    "ps_set_mode_cmd"),
        ]
        self._ps_vars = {}
        for label, key in ps_fields:
            ctk.CTkLabel(self.config_tab, text=label).grid(row=row, column=0, pady=3, padx=5, sticky="e")
            var = ctk.StringVar()
            self._ps_vars[key] = var
            ctk.CTkEntry(self.config_tab, textvariable=var).grid(row=row, column=1, pady=3, padx=5, sticky="ew")
            row += 1

        btn_frame = ctk.CTkFrame(self.config_tab, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text="Add / Update", command=self.save_device).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Clear Form", command=self.clear_form).grid(row=0, column=1, padx=5)

    def setup_connect_tab(self):
        self.connect_tab.grid_columnconfigure(1, weight=1)
        self.connect_tab.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.connect_tab, text="Available Ports:").grid(row=0, column=0, pady=5, padx=5, sticky="e")
        self.port_var = ctk.StringVar()
        self.port_menu = ctk.CTkOptionMenu(self.connect_tab, variable=self.port_var, values=[])
        self.port_menu.grid(row=0, column=1, pady=5, padx=5, sticky="ew")

        btn_frame = ctk.CTkFrame(self.connect_tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        self.connect_btn = ctk.CTkButton(btn_frame, text="Connect", command=self.connect_device, fg_color="green")
        self.connect_btn.grid(row=0, column=0, padx=3)
        self.disconnect_btn = ctk.CTkButton(btn_frame, text="Disconnect", command=self.disconnect_device, fg_color="red")
        self.disconnect_btn.grid(row=0, column=1, padx=3)
        self.scan_btn = ctk.CTkButton(btn_frame, text="Refresh Ports", command=self.refresh_ports)
        self.scan_btn.grid(row=0, column=2, padx=3)
        self.auto_btn = ctk.CTkButton(btn_frame, text="Auto Detect", command=self.auto_detect)
        self.auto_btn.grid(row=0, column=3, padx=3)

        self.conn_status = ctk.CTkLabel(self.connect_tab, text="Not connected", text_color="gray")
        self.conn_status.grid(row=2, column=0, columnspan=2, pady=5)

        log_frame = ctk.CTkFrame(self.connect_tab)
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5, padx=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def load_devices(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        devices = self.controller.get_all_devices()
        for d in devices:
            self.tree.insert("", "end", values=(d.id, d.name, d.device_id))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        pk = item["values"][0]
        self.selected_device_id = pk
        device = self.controller.get_device(pk)
        if device:
            self.device_id_var.set(device.device_id)
            self.name_var.set(device.name)
            self.idn_cmd_var.set(device.idn_command)
            self.idn_resp_var.set(device.idn_response)
            self.baud_var.set(str(device.baud_rate))
            self.parity_var.set(device.parity)
            self.data_var.set(str(device.data_bits))
            self.stop_var.set(str(device.stop_bits))
            self.timeout_var.set(str(device.timeout))
            self.notes_text.delete("0.0", "end")
            self.notes_text.insert("0.0", device.notes)
            for key in self._ps_vars:
                self._ps_vars[key].set(getattr(device, key, ""))
            self.refresh_ports()
            if self.controller.is_connected(pk):
                self.conn_status.configure(text="Connected", text_color="green")
            else:
                self.conn_status.configure(text="Not connected", text_color="gray")

    def save_device(self):
        device_id = self.device_id_var.get()
        name = self.name_var.get()

        ps_kwargs = {key: var.get() for key, var in self._ps_vars.items()}

        if self.selected_device_id:
            kwargs = {
                "device_id": device_id,
                "name": name,
                "idn_command": self.idn_cmd_var.get(),
                "idn_response": self.idn_resp_var.get(),
                "baud_rate": int(self.baud_var.get()),
                "parity": self.parity_var.get(),
                "data_bits": int(self.data_var.get()),
                "stop_bits": int(self.stop_var.get()),
                "timeout": float(self.timeout_var.get()),
                "notes": self.notes_text.get("0.0", "end").strip(),
                **ps_kwargs,
            }
            ok, msg = self.controller.update_device(self.selected_device_id, **kwargs)
        else:
            ok, msg = self.controller.add_device(
                device_id, name, self.idn_cmd_var.get(), self.idn_resp_var.get(),
                int(self.baud_var.get()), int(self.data_var.get()),
                int(self.stop_var.get()), self.parity_var.get(),
                float(self.timeout_var.get()), self.notes_text.get("0.0", "end").strip(),
                **ps_kwargs,
            )

        if ok:
            messagebox.showinfo("Success", msg)
            self.load_devices()
            self._notify_terminal()
        else:
            messagebox.showerror("Error", msg)

    def delete_device(self):
        if not self.selected_device_id:
            messagebox.showwarning("Warning", "Select a device first")
            return
        if messagebox.askyesno("Confirm", "Delete this device?"):
            self.controller.delete_device(self.selected_device_id)
            self.selected_device_id = None
            self.clear_form()
            self.load_devices()
            self._notify_terminal()

    def clear_form(self):
        self.selected_device_id = None
        self.device_id_var.set("")
        self.name_var.set("")
        self.idn_cmd_var.set("*IDN?")
        self.idn_resp_var.set("")
        self.baud_var.set("115200")
        self.parity_var.set("None")
        self.data_var.set("8")
        self.stop_var.set("1")
        self.timeout_var.set("2.0")
        self.notes_text.delete("0.0", "end")
        self._ps_vars["ps_init_cmd"].set("")
        self._ps_vars["ps_set_voltage_cmd"].set("PSV {value}")
        self._ps_vars["ps_set_current_cmd"].set("PSC {value}")
        self._ps_vars["ps_on_cmd"].set("PSON")
        self._ps_vars["ps_off_cmd"].set("PSOFF")
        self._ps_vars["ps_measure_cmd"].set("PSMEAS")
        self._ps_vars["ps_status_cmd"].set("PSSTATUS")
        self._ps_vars["ps_set_mode_cmd"].set("PSMODE {mode}")
        self.conn_status.configure(text="Not connected", text_color="gray")
        self.tree.selection_remove(*self.tree.selection())

    def refresh_ports(self):
        ports = self.controller.list_ports()
        self.port_menu.configure(values=ports if ports else ["(none)"])
        self.port_var.set(ports[0] if ports else "(none)")

    def connect_device(self):
        if not self.selected_device_id:
            messagebox.showwarning("Warning", "Select a device first")
            return
        port = self.port_var.get()
        if not port or port == "(none)":
            messagebox.showwarning("Warning", "No port selected")
            return
        ok, msg = self.controller.connect_device(self.selected_device_id, port)
        if ok:
            self.conn_status.configure(text=f"Connected on {port}", text_color="green")
            self.log_msg(f"Connected to {port}")
            self._notify_terminal()
        else:
            self.conn_status.configure(text=f"Failed: {msg}", text_color="red")
            self.log_msg(f"Connection failed: {msg}")

    def disconnect_device(self):
        self.controller.disconnect_device(self.selected_device_id)
        self.conn_status.configure(text="Disconnected", text_color="gray")
        self.log_msg("Disconnected")
        self._notify_terminal()

    def auto_detect(self):
        if not self.selected_device_id:
            messagebox.showwarning("Warning", "Select a device first")
            return
        self.log_msg("Scanning ports...")
        ok, msg, results = self.controller.auto_detect(self.selected_device_id)
        if results:
            ports_str = ", ".join([f"{r[0]} @ {r[1]} baud" for r in results])
            self.log_msg(f"Found on: {ports_str}")
            self.port_menu.configure(values=[r[0] for r in results])
            self.port_var.set(results[0][0])
            messagebox.showinfo("Auto Detect", f"Device found on:\n{ports_str}")
        else:
            self.log_msg("No matching port found")
            messagebox.showinfo("Auto Detect", "No matching port found")

    def log_msg(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
