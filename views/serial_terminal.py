import customtkinter as ctk
from tkinter import messagebox
from controllers.device_controller import DeviceController


class SerialTerminalView(ctk.CTkFrame):
    def __init__(self, parent, auth_controller, device_controller: DeviceController):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.controller = device_controller
        self.selected_pk = None
        self.setup_ui()
        self.refresh_devices()

    def refresh_devices(self):
        devices = self.controller.get_all_devices()
        if devices:
            names = [f"{d.device_id} - {d.name}" for d in devices]
            self.device_menu.configure(values=names)
            if self.device_var.get() not in names:
                self.device_var.set(names[0])
            self.on_device_change()
        else:
            self.device_menu.configure(values=["(no devices)"])
            self.device_var.set("(no devices)")
            self.selected_pk = None
            self.status_label.configure(text="No devices configured", text_color="gray")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkLabel(self, text="Serial Terminal",
                              font=ctk.CTkFont(size=20, weight="bold"))
        header.grid(row=0, column=0, pady=10)

        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        top_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(top_frame, text="Device:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.device_var = ctk.StringVar()
        self.device_var.trace("w", lambda *a: self.on_device_change())
        self.device_menu = ctk.CTkOptionMenu(top_frame, variable=self.device_var,
                                              values=[], dynamic_resizing=False)
        self.device_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.status_label = ctk.CTkLabel(top_frame, text="Disconnected", text_color="gray")
        self.status_label.grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(top_frame, text="Terminator:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.term_var = ctk.StringVar(value="\\n")
        ctk.CTkOptionMenu(top_frame, variable=self.term_var,
                           values=["\\n", "\\r\\n", "\\r", "None"]).grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=3)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)

        output_frame = ctk.CTkFrame(main_frame)
        output_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(output_frame, text="Response",
                      font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=2)

        self.output_text = ctk.CTkTextbox(output_frame, state="disabled",
                                           font=ctk.CTkFont(family="Consolas", size=12))
        self.output_text.grid(row=1, column=0, sticky="nsew")

        send_frame = ctk.CTkFrame(main_frame)
        send_frame.grid(row=1, column=0, sticky="ew", pady=5)
        send_frame.grid_columnconfigure(0, weight=1)

        self.input_var = ctk.StringVar()
        self.input_entry = ctk.CTkEntry(send_frame, textvariable=self.input_var,
                                         placeholder_text="Type command here...",
                                         font=ctk.CTkFont(family="Consolas", size=12))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.input_entry.bind("<Return>", lambda e: self.send_command())

        ctk.CTkButton(send_frame, text="Send", command=self.send_command, width=100).grid(row=0, column=1, padx=5)

        quick_frame = ctk.CTkFrame(main_frame)
        quick_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        quick_frame.grid_columnconfigure(list(range(6)), weight=1)

        ctk.CTkLabel(quick_frame, text="Quick Send:",
                      font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        for i, cmd in enumerate(["*IDN?", "PING", "HELP", "STATUS"]):
            btn = ctk.CTkButton(quick_frame, text=cmd, width=100, height=28,
                                 command=lambda c=cmd: self.quick_send(c))
            btn.grid(row=0, column=i + 1, padx=3, pady=5)

        ctk.CTkButton(quick_frame, text="Refresh Devices", width=100, height=28,
                       command=self.refresh_devices).grid(row=0, column=5, padx=5, pady=5)
        ctk.CTkButton(quick_frame, text="Clear", width=80, height=28,
                       command=self.clear_output).grid(row=0, column=6, padx=5, pady=5)

    def on_device_change(self):
        self.selected_pk = None
        selection = self.device_var.get()
        if not selection or selection == "(no devices)":
            self.status_label.configure(text="No device selected", text_color="gray")
            return
        device_id = selection.split(" - ")[0]
        for d in self.controller.get_all_devices():
            if d.device_id == device_id:
                self.selected_pk = d.id
                if self.controller.is_connected(d.id):
                    self.status_label.configure(text="Connected", text_color="green")
                else:
                    self.status_label.configure(text="Disconnected", text_color="gray")
                return

    def send_command(self):
        cmd = self.input_var.get()
        if not cmd:
            return
        self.execute_command(cmd)
        self.input_var.set("")

    def quick_send(self, cmd):
        self.execute_command(cmd)

    def execute_command(self, cmd):
        if not self.selected_pk:
            messagebox.showwarning("Warning", "No device selected")
            return
        if not self.controller.is_connected(self.selected_pk):
            messagebox.showwarning("Warning", "Device not connected. Go to Device Manager to connect.")
            return

        term_map = {"\\n": "\n", "\\r\\n": "\r\n", "\\r": "\r", "None": ""}
        term = term_map.get(self.term_var.get(), "\n")

        self.output_text.configure(state="normal")
        self.output_text.insert("end", f">>> {cmd}\n", "cmd")
        self.output_text.tag_config("cmd", foreground="#4CAF50")

        ok, resp = self.controller.send_command(self.selected_pk, cmd, term)
        if ok and resp:
            self.output_text.insert("end", f"{resp}\n")
        elif ok:
            self.output_text.insert("end", "(no response)\n")
        else:
            self.output_text.insert("end", f"Error: {resp}\n", "err")
            self.output_text.tag_config("err", foreground="#F44336")

        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("0.0", "end")
        self.output_text.configure(state="disabled")
