import customtkinter as ctk
from tkinter import messagebox
from controllers.device_controller import DeviceController


class ESP32ControlView(ctk.CTkFrame):
    def __init__(self, parent, auth_controller, device_controller: DeviceController):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.dc = device_controller
        self.esp32_pk = None
        self.ps_pk = None
        self.esp32_relay_states = [False] * 8
        self.relay_btns = []
        self._ps_cmds = {}
        self.setup_ui()
        self.refresh_all()
        self.update_esp32_ui_state()
        self.update_ps_ui_state()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(self, text="ESP32 Control + Power Supply",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.grid(row=0, column=0, pady=10)

        self.setup_esp32_conn_bar()
        self.setup_ps_conn_bar()

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.setup_relays_panel(main_frame)
        self.setup_buzzer_panel(main_frame)
        self.setup_power_supply_panel(main_frame)
        self.setup_log_panel(main_frame)

    # ──────────── Connection bars ────────────

    def setup_esp32_conn_bar(self):
        f = ctk.CTkFrame(self)
        f.grid(row=1, column=0, sticky="ew", padx=10, pady=3)
        f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f, text="ESP32",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=5)

        ctk.CTkLabel(f, text="Device:").grid(row=0, column=1, padx=5, pady=3, sticky="e")
        self.esp_device_var = ctk.StringVar()
        self.esp_device_menu = ctk.CTkOptionMenu(f, variable=self.esp_device_var, values=[])
        self.esp_device_menu.grid(row=0, column=2, padx=3, pady=3, sticky="ew")

        ctk.CTkLabel(f, text="Port:").grid(row=0, column=3, padx=5, pady=3, sticky="e")
        self.esp_port_var = ctk.StringVar()
        self.esp_port_menu = ctk.CTkOptionMenu(f, variable=self.esp_port_var, values=[])
        self.esp_port_menu.grid(row=0, column=4, padx=3, pady=3, sticky="ew")

        self.esp_connect_btn = ctk.CTkButton(f, text="Connect", command=self.esp_connect,
                                              fg_color="green", width=85)
        self.esp_connect_btn.grid(row=0, column=5, padx=3, pady=3)

        self.esp_disconnect_btn = ctk.CTkButton(f, text="Disconnect", command=self.esp_disconnect,
                                                 fg_color="red", width=85, state="disabled")
        self.esp_disconnect_btn.grid(row=0, column=6, padx=3, pady=3)

        self.esp_auto_btn = ctk.CTkButton(f, text="Auto Port", command=self.esp_auto_port,
                                           width=80)
        self.esp_auto_btn.grid(row=0, column=7, padx=3, pady=3)

        self.esp_refresh_btn = ctk.CTkButton(f, text="Refresh", command=self.refresh_all,
                                              width=70)
        self.esp_refresh_btn.grid(row=0, column=8, padx=3, pady=3)

        self.esp_status_label = ctk.CTkLabel(f, text="Disconnected", text_color="red",
                                              font=ctk.CTkFont(weight="bold"))
        self.esp_status_label.grid(row=0, column=9, padx=8, pady=3)

    def setup_ps_conn_bar(self):
        f = ctk.CTkFrame(self)
        f.grid(row=2, column=0, sticky="ew", padx=10, pady=3)
        f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f, text="PS",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=5)

        ctk.CTkLabel(f, text="Device:").grid(row=0, column=1, padx=5, pady=3, sticky="e")
        self.ps_device_var = ctk.StringVar()
        self.ps_device_menu = ctk.CTkOptionMenu(f, variable=self.ps_device_var, values=[])
        self.ps_device_menu.grid(row=0, column=2, padx=3, pady=3, sticky="ew")

        ctk.CTkLabel(f, text="Port:").grid(row=0, column=3, padx=5, pady=3, sticky="e")
        self.ps_port_var = ctk.StringVar()
        self.ps_port_menu = ctk.CTkOptionMenu(f, variable=self.ps_port_var, values=[])
        self.ps_port_menu.grid(row=0, column=4, padx=3, pady=3, sticky="ew")

        self.ps_connect_btn = ctk.CTkButton(f, text="Connect", command=self.ps_connect,
                                             fg_color="green", width=85)
        self.ps_connect_btn.grid(row=0, column=5, padx=3, pady=3)

        self.ps_disconnect_btn = ctk.CTkButton(f, text="Disconnect", command=self.ps_disconnect,
                                                fg_color="red", width=85, state="disabled")
        self.ps_disconnect_btn.grid(row=0, column=6, padx=3, pady=3)

        self.ps_auto_btn = ctk.CTkButton(f, text="Auto Port", command=self.ps_auto_port,
                                          width=80)
        self.ps_auto_btn.grid(row=0, column=7, padx=3, pady=3)

        self.ps_refresh_btn = ctk.CTkButton(f, text="Refresh", command=self.refresh_all,
                                             width=70)
        self.ps_refresh_btn.grid(row=0, column=8, padx=3, pady=3)

        self.ps_status_label = ctk.CTkLabel(f, text="Disconnected", text_color="red",
                                             font=ctk.CTkFont(weight="bold"))
        self.ps_status_label.grid(row=0, column=9, padx=8, pady=3)

    # ──────────── Control panels ────────────

    def setup_relays_panel(self, parent):
        relay_frame = ctk.CTkFrame(parent)
        relay_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        relay_frame.grid_columnconfigure(list(range(4)), weight=1)

        ctk.CTkLabel(relay_frame, text="Relays",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, pady=5)

        self.relay_btns = []
        for i in range(8):
            r = (i // 4) + 1
            c = i % 4
            btn = ctk.CTkButton(
                relay_frame, text=f"RELAY {i + 1}\nOFF",
                width=100, height=60,
                fg_color="#555555", hover_color="#666666",
                command=lambda idx=i: self.toggle_relay(idx)
            )
            btn.grid(row=r, column=c, padx=5, pady=5)
            self.relay_btns.append(btn)

        ctrl_frame = ctk.CTkFrame(relay_frame, fg_color="transparent")
        ctrl_frame.grid(row=3, column=0, columnspan=4, pady=10)

        self.all_on_btn = ctk.CTkButton(ctrl_frame, text="ALL ON", fg_color="green",
                                          command=self.all_on, width=100, state="disabled")
        self.all_on_btn.grid(row=0, column=0, padx=5)

        self.all_off_btn = ctk.CTkButton(ctrl_frame, text="ALL OFF", fg_color="red",
                                           command=self.all_off, width=100, state="disabled")
        self.all_off_btn.grid(row=0, column=1, padx=5)

        self.ping_btn = ctk.CTkButton(ctrl_frame, text="PING", command=self.ping_test,
                                       width=100, state="disabled")
        self.ping_btn.grid(row=0, column=2, padx=5)

    def setup_buzzer_panel(self, parent):
        buzzer_frame = ctk.CTkFrame(parent)
        buzzer_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        buzzer_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(buzzer_frame, text="Buzzer",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(buzzer_frame, text="Cycles:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.bz_cycles = ctk.CTkEntry(buzzer_frame, width=80)
        self.bz_cycles.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.bz_cycles.insert(0, "3")

        ctk.CTkLabel(buzzer_frame, text="ON Time (s):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.bz_on = ctk.CTkEntry(buzzer_frame, width=80)
        self.bz_on.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.bz_on.insert(0, "1")

        ctk.CTkLabel(buzzer_frame, text="OFF Time (s):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.bz_off = ctk.CTkEntry(buzzer_frame, width=80)
        self.bz_off.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.bz_off.insert(0, "1")

        self.buzzer_btn = ctk.CTkButton(buzzer_frame, text="BUZZ!", command=self.buzzer_start,
                                         fg_color="orange", state="disabled", height=40)
        self.buzzer_btn.grid(row=4, column=0, columnspan=2, pady=10, padx=20, sticky="ew")

    def setup_power_supply_panel(self, parent):
        ps_frame = ctk.CTkFrame(parent)
        ps_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        ps_frame.grid_columnconfigure(list(range(4)), weight=1)

        ctk.CTkLabel(ps_frame, text="Power Supply Controls",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, pady=5)

        vol_frame = ctk.CTkFrame(ps_frame, fg_color="transparent")
        vol_frame.grid(row=1, column=0, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(vol_frame, text="Voltage (V)", font=ctk.CTkFont(weight="bold")).pack()
        self.ps_v_entry = ctk.CTkEntry(vol_frame, width=100, justify="center")
        self.ps_v_entry.pack(pady=2)
        self.ps_v_entry.insert(0, "5.00")
        self.ps_set_v_btn = ctk.CTkButton(vol_frame, text="Set V", command=self.ps_set_voltage,
                                           width=80, state="disabled")
        self.ps_set_v_btn.pack(pady=2)
        self.ps_meas_v_btn = ctk.CTkButton(vol_frame, text="Measure V", command=self.ps_measure_voltage,
                                             width=80, state="disabled")
        self.ps_meas_v_btn.pack(pady=2)

        cur_frame = ctk.CTkFrame(ps_frame, fg_color="transparent")
        cur_frame.grid(row=1, column=1, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(cur_frame, text="Current (A)", font=ctk.CTkFont(weight="bold")).pack()
        self.ps_c_entry = ctk.CTkEntry(cur_frame, width=100, justify="center")
        self.ps_c_entry.pack(pady=2)
        self.ps_c_entry.insert(0, "1.00")
        self.ps_set_c_btn = ctk.CTkButton(cur_frame, text="Set I", command=self.ps_set_current,
                                           width=80, state="disabled")
        self.ps_set_c_btn.pack(pady=2)
        self.ps_meas_c_btn = ctk.CTkButton(cur_frame, text="Measure I", command=self.ps_measure_current,
                                             width=80, state="disabled")
        self.ps_meas_c_btn.pack(pady=2)

        ch_mode_frame = ctk.CTkFrame(ps_frame, fg_color="transparent")
        ch_mode_frame.grid(row=1, column=2, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(ch_mode_frame, text="Channel", font=ctk.CTkFont(weight="bold")).pack()
        self.ps_ch_var = ctk.StringVar(value="1")
        self.ps_ch_menu = ctk.CTkOptionMenu(ch_mode_frame, variable=self.ps_ch_var,
                                              values=["1", "2", "3"], state="disabled", width=80)
        self.ps_ch_menu.pack(pady=2)
        ctk.CTkLabel(ch_mode_frame, text="", height=10).pack()
        ctk.CTkLabel(ch_mode_frame, text="Mode", font=ctk.CTkFont(weight="bold")).pack()
        self.ps_mode_var = ctk.StringVar(value="CV")
        self.ps_mode_menu = ctk.CTkOptionMenu(ch_mode_frame, variable=self.ps_mode_var,
                                                values=["CV", "CC"], state="disabled", width=80)
        self.ps_mode_menu.pack(pady=2)
        self.ps_set_mode_btn = ctk.CTkButton(ch_mode_frame, text="Set Mode", command=self.ps_set_mode,
                                               width=80, state="disabled")
        self.ps_set_mode_btn.pack(pady=2)

        out_frame = ctk.CTkFrame(ps_frame, fg_color="transparent")
        out_frame.grid(row=1, column=3, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(out_frame, text="Output", font=ctk.CTkFont(weight="bold")).pack()
        self.ps_on_btn = ctk.CTkButton(out_frame, text="OUTPUT ON", fg_color="green",
                                        command=self.ps_on, width=100, state="disabled")
        self.ps_on_btn.pack(pady=2)
        self.ps_off_btn = ctk.CTkButton(out_frame, text="OUTPUT OFF", fg_color="red",
                                         command=self.ps_off, width=100, state="disabled")
        self.ps_off_btn.pack(pady=2)
        self.ps_status_btn = ctk.CTkButton(out_frame, text="Status", command=self.ps_status,
                                            width=80, state="disabled")
        self.ps_status_btn.pack(pady=2)

        readings_frame = ctk.CTkFrame(ps_frame, fg_color="transparent")
        readings_frame.grid(row=2, column=0, columnspan=4, pady=5)
        self.ps_v_read = ctk.CTkLabel(readings_frame, text="V: ---", font=ctk.CTkFont(size=14, weight="bold"))
        self.ps_v_read.pack(side="left", padx=20)
        self.ps_i_read = ctk.CTkLabel(readings_frame, text="I: ---", font=ctk.CTkFont(size=14, weight="bold"))
        self.ps_i_read.pack(side="left", padx=20)
        self.ps_mode_read = ctk.CTkLabel(readings_frame, text="Mode: ---", font=ctk.CTkFont(size=14))
        self.ps_mode_read.pack(side="left", padx=20)
        self.ps_out_read = ctk.CTkLabel(readings_frame, text="Output: ---", text_color="red",
                                          font=ctk.CTkFont(size=14))
        self.ps_out_read.pack(side="left", padx=20)

    def setup_log_panel(self, parent):
        log_frame = ctk.CTkFrame(parent)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_frame, text="Activity Log",
                      font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=2)

        self.log_text = ctk.CTkTextbox(log_frame, state="disabled",
                                        font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.grid(row=1, column=0, sticky="nsew")

    # ──────────── Refresh ────────────

    def refresh_all(self):
        devices = self.dc.get_all_devices()
        names = [d.name for d in devices] if devices else []

        for var, menu in [(self.esp_device_var, self.esp_device_menu),
                          (self.ps_device_var, self.ps_device_menu)]:
            menu.configure(values=names if names else ["(none)"])
            if names and var.get() not in names:
                var.set(names[0])
            elif not names:
                var.set("(none)")

        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]

        for var, menu in [(self.esp_port_var, self.esp_port_menu),
                          (self.ps_port_var, self.ps_port_menu)]:
            menu.configure(values=ports if ports else ["(none)"])
            var.set(ports[0] if ports else "(none)")

    # ──────────── PK helpers ────────────

    def _pk_by_name(self, name):
        for d in self.dc.get_all_devices():
            if d.name == name:
                return d.id
        return None

    # ──────────── ESP32 handlers ────────────

    def _send_esp32(self, cmd):
        if not self.esp32_pk:
            return False, "ESP32 not connected"
        return self.dc.send_command(self.esp32_pk, cmd)

    def esp_connect(self):
        pk = self._pk_by_name(self.esp_device_var.get())
        if not pk:
            messagebox.showwarning("Warning", "Select an ESP32 device")
            return
        port = self.esp_port_var.get()
        if not port or port == "(none)":
            messagebox.showwarning("Warning", "Select a port")
            return
        ok, err = self.dc.connect_device(pk, port)
        if ok:
            self.esp32_pk = pk
            self.esp_status_label.configure(text=f"Connected on {port}", text_color="green")
            self.log(f"ESP32 connected on {port}")
            self.esp32_relay_states = [False] * 8
            self.update_esp32_ui_state()
        else:
            self.esp_status_label.configure(text="Connection failed", text_color="red")
            self.log(f"ESP32 connect failed: {err}")
            messagebox.showerror("Error", err)

    def esp_disconnect(self):
        pk = self._pk_by_name(self.esp_device_var.get())
        if pk:
            self.dc.disconnect_device(pk)
        self.esp32_pk = None
        self.esp_status_label.configure(text="Disconnected", text_color="red")
        self.log("ESP32 disconnected")
        self.update_esp32_ui_state()

    def esp_auto_port(self):
        pk = self._pk_by_name(self.esp_device_var.get())
        if not pk:
            messagebox.showwarning("Warning", "Select an ESP32 device")
            return
        self.log(f"Auto-detecting port for '{self.esp_device_var.get()}'...")
        found, msg, results = self.dc.auto_detect(pk)
        if found:
            self.esp_port_var.set(results[0][0])
            self.log(f"Port set to {results[0][0]}")
            messagebox.showinfo("Auto Detect", f"Port set to {results[0]}")
        else:
            self.log(msg)
            messagebox.showinfo("Auto Detect", msg)

    def ping_test(self):
        ok, resp = self._send_esp32("PING")
        if ok and "PONG" in resp.upper():
            self.log("PING -> PONG (ESP32 alive)")
            messagebox.showinfo("PING", "ESP32 is responding!")
        else:
            self.log("PING -> No response")
            messagebox.showerror("PING", "No PONG response")

    def toggle_relay(self, index):
        new_state = not self.esp32_relay_states[index]
        pattern = list("00000000")
        self.esp32_relay_states[index] = new_state
        for i, s in enumerate(self.esp32_relay_states):
            pattern[i] = "1" if s else "0"
        cmd = "".join(pattern)
        ok, resp = self._send_esp32(cmd)
        if ok:
            self.log(f"Relay {index + 1} -> {'ON' if new_state else 'OFF'}")
            self.update_relay_buttons()
        else:
            self.esp32_relay_states[index] = not new_state
            self.log(f"Relay {index + 1} failed: {resp}")
            messagebox.showerror("Error", resp)

    def all_on(self):
        ok, resp = self._send_esp32("11111111")
        if ok:
            self.esp32_relay_states = [True] * 8
            self.log("All relays ON")
            self.update_relay_buttons()
        else:
            self.log(f"All ON failed: {resp}")

    def all_off(self):
        ok, resp = self._send_esp32("00000000")
        if ok:
            self.esp32_relay_states = [False] * 8
            self.log("All relays OFF")
            self.update_relay_buttons()
        else:
            self.log(f"All OFF failed: {resp}")

    def buzzer_start(self):
        try:
            cycles = int(self.bz_cycles.get())
            on_time = int(self.bz_on.get())
            off_time = int(self.bz_off.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for buzzer")
            return
        cmd = f"BZR-{cycles:02d}-{on_time:02d}-{off_time:02d}"
        self.log(f"Buzzer: {cycles} cycles, {on_time}s ON, {off_time}s OFF")
        ok, resp = self._send_esp32(cmd)
        if ok:
            self.log("Buzzer command sent")
        else:
            self.log(f"Buzzer failed: {resp}")

    # ──────────── PS handlers ────────────

    def _send_ps(self, cmd):
        if not self.ps_pk:
            return False, "PS device not connected"
        return self.dc.send_command(self.ps_pk, cmd)

    def _load_ps_cmds(self, pk):
        device = self.dc.get_device(pk)
        if not device:
            return False
        self._ps_cmds = {
            "set_voltage": device.ps_set_voltage_cmd,
            "set_current": device.ps_set_current_cmd,
            "on":          device.ps_on_cmd,
            "off":         device.ps_off_cmd,
            "measure":     device.ps_measure_cmd,
            "status":      device.ps_status_cmd,
            "set_mode":    device.ps_set_mode_cmd,
            "init":        getattr(device, "ps_init_cmd", ""),
        }
        return True

    def _format_ps_cmd(self, key, **kwargs):
        template = self._ps_cmds.get(key, "")
        kwargs.setdefault("ch", self.ps_ch_var.get())
        result = template.format(**kwargs)
        result = result.replace("\\n", "\n")
        return result

    def ps_connect(self):
        pk = self._pk_by_name(self.ps_device_var.get())
        if not pk:
            messagebox.showwarning("Warning", "Select a PS device")
            return
        port = self.ps_port_var.get()
        if not port or port == "(none)":
            messagebox.showwarning("Warning", "Select a port")
            return
        ok, err = self.dc.connect_device(pk, port)
        if ok:
            self.ps_pk = pk
            self._load_ps_cmds(pk)
            init_cmd = self._ps_cmds.get("init", "")
            if init_cmd:
                self.log(f"Sending init: {init_cmd}")
                self.dc.send_command(pk, init_cmd.replace("\\n", "\n"))
            self.ps_status_label.configure(text=f"Connected on {port}", text_color="green")
            self.log(f"PS connected on {port}")
            self.update_ps_ui_state()
        else:
            self.ps_status_label.configure(text="Connection failed", text_color="red")
            self.log(f"PS connect failed: {err}")
            messagebox.showerror("Error", err)

    def ps_disconnect(self):
        pk = self._pk_by_name(self.ps_device_var.get())
        if pk:
            self.dc.disconnect_device(pk)
        self.ps_pk = None
        self._ps_cmds = {}
        self.ps_status_label.configure(text="Disconnected", text_color="red")
        self.log("PS disconnected")
        self.update_ps_ui_state()

    def ps_auto_port(self):
        pk = self._pk_by_name(self.ps_device_var.get())
        if not pk:
            messagebox.showwarning("Warning", "Select a PS device")
            return
        self.log(f"Auto-detecting port for '{self.ps_device_var.get()}'...")
        found, msg, results = self.dc.auto_detect(pk)
        if found:
            self.ps_port_var.set(results[0][0])
            self.log(f"Port set to {results[0][0]}")
            messagebox.showinfo("Auto Detect", f"Port set to {results[0]}")
        else:
            self.log(msg)
            messagebox.showinfo("Auto Detect", msg)

    def ps_set_voltage(self):
        try:
            v = float(self.ps_v_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid voltage")
            return
        cmd = self._format_ps_cmd("set_voltage", value=f"{v:.2f}")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.log(f"PS voltage set ({cmd})")
        else:
            self.log(f"PS set V failed: {resp}")

    def ps_set_current(self):
        try:
            c = float(self.ps_c_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid current")
            return
        cmd = self._format_ps_cmd("set_current", value=f"{c:.2f}")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.log(f"PS current set ({cmd})")
        else:
            self.log(f"PS set I failed: {resp}")

    def _parse_ps_response(self, resp, label_v=None, label_i=None, label_mode=None, label_out=None):
        parsed = False
        for part in resp.split(","):
            part = part.strip()
            if part.startswith("V=") and label_v:
                label_v.configure(text=f"V: {part[2:]}V")
                parsed = True
            elif part.startswith("I=") and label_i:
                label_i.configure(text=f"I: {part[2:]}A")
                parsed = True
            elif part.startswith("Mode=") and label_mode:
                label_mode.configure(text=f"Mode: {part.split('=', 1)[1]}")
                parsed = True
            elif part.startswith("Output=") and label_out:
                val = part.split("=", 1)[1]
                label_out.configure(
                    text=f"Output: {val}",
                    text_color="green" if val.upper() == "ON" else "red"
                )
                parsed = True
        return parsed

    def _parse_scpi_number(self, resp):
        try:
            parts = resp.strip().split(",")
            vals = []
            for p in parts:
                p = p.strip()
                p = p.replace("+", "").replace("V", "").replace("A", "")
                vals.append(float(p))
            return vals
        except (ValueError, TypeError):
            return None

    def ps_measure_voltage(self):
        cmd = self._format_ps_cmd("measure")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.log(f"PS measure V: {resp}")
            if not self._parse_ps_response(resp, label_v=self.ps_v_read, label_i=self.ps_i_read):
                nums = self._parse_scpi_number(resp)
                if nums:
                    self.ps_v_read.configure(text=f"V: {nums[0]:.3f}V")
                    if len(nums) > 1:
                        self.ps_i_read.configure(text=f"I: {nums[1]:.3f}A")
                else:
                    self.ps_v_read.configure(text=f"V: {resp.strip()}")
        else:
            self.log(f"PS measure V failed: {resp}")

    def ps_measure_current(self):
        cmd = self._format_ps_cmd("measure")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.log(f"PS measure I: {resp}")
            if not self._parse_ps_response(resp, label_v=self.ps_v_read, label_i=self.ps_i_read):
                nums = self._parse_scpi_number(resp)
                if nums:
                    idx = 1 if len(nums) > 1 else 0
                    self.ps_i_read.configure(text=f"I: {nums[idx]:.3f}A")
                else:
                    self.ps_i_read.configure(text=f"I: {resp.strip()}")
        else:
            self.log(f"PS measure I failed: {resp}")

    def ps_set_mode(self):
        mode = self.ps_mode_var.get()
        cmd = self._format_ps_cmd("set_mode", mode=mode)
        ok, resp = self._send_ps(cmd)
        if ok:
            self.ps_mode_read.configure(text=f"Mode: {mode}")
            self.log(f"PS mode set ({cmd})")
        else:
            self.log(f"PS set mode failed: {resp}")

    def ps_on(self):
        cmd = self._format_ps_cmd("on")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.ps_out_read.configure(text="Output: ON", text_color="green")
            self.log(f"PS output ON ({cmd})")
        else:
            self.log(f"PS ON failed: {resp}")

    def ps_off(self):
        cmd = self._format_ps_cmd("off")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.ps_out_read.configure(text="Output: OFF", text_color="red")
            self.log(f"PS output OFF ({cmd})")
        else:
            self.log(f"PS OFF failed: {resp}")

    def ps_status(self):
        cmd = self._format_ps_cmd("status")
        ok, resp = self._send_ps(cmd)
        if ok:
            self.log(f"PS status: {resp}")
            if not self._parse_ps_response(resp, self.ps_v_read, self.ps_i_read,
                                           self.ps_mode_read, self.ps_out_read):
                nums = self._parse_scpi_number(resp)
                if nums:
                    if len(nums) >= 1:
                        self.ps_v_read.configure(text=f"V: {nums[0]:.3f}V")
                    if len(nums) >= 2:
                        self.ps_i_read.configure(text=f"I: {nums[1]:.3f}A")
        else:
            self.log(f"PS status failed: {resp}")

    # ──────────── UI state ────────────

    def update_esp32_ui_state(self):
        connected = self.esp32_pk is not None and self.dc.is_connected(self.esp32_pk)
        state = "normal" if connected else "disabled"
        for btn in self.relay_btns:
            btn.configure(state=state)
        self.all_on_btn.configure(state=state)
        self.all_off_btn.configure(state=state)
        self.ping_btn.configure(state=state)
        self.buzzer_btn.configure(state=state)
        self.esp_connect_btn.configure(state="disabled" if connected else "normal")
        self.esp_disconnect_btn.configure(state="normal" if connected else "disabled")
        self.update_relay_buttons()

    def update_ps_ui_state(self):
        ps_connected = self.ps_pk is not None and self.dc.is_connected(self.ps_pk)
        state = "normal" if ps_connected else "disabled"
        self.ps_set_v_btn.configure(state=state)
        self.ps_set_c_btn.configure(state=state)
        self.ps_meas_v_btn.configure(state=state)
        self.ps_meas_c_btn.configure(state=state)
        self.ps_set_mode_btn.configure(state=state)
        self.ps_mode_menu.configure(state=state)
        self.ps_ch_menu.configure(state=state)
        self.ps_on_btn.configure(state=state)
        self.ps_off_btn.configure(state=state)
        self.ps_status_btn.configure(state=state)
        self.ps_connect_btn.configure(state="disabled" if ps_connected else "normal")
        self.ps_disconnect_btn.configure(state="normal" if ps_connected else "disabled")

    def update_relay_buttons(self):
        for i, state in enumerate(self.esp32_relay_states):
            if state:
                self.relay_btns[i].configure(
                    text=f"RELAY {i + 1}\nON",
                    fg_color="#2E7D32", hover_color="#388E3C"
                )
            else:
                self.relay_btns[i].configure(
                    text=f"RELAY {i + 1}\nOFF",
                    fg_color="#555555", hover_color="#666666"
                )

    def log(self, msg):
        self.log_text.configure(state="normal")
        import time
        t = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{t}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
