import customtkinter as ctk
from controllers.device_controller import DeviceController
from views.device_manager import DeviceManagerView
from views.serial_terminal import SerialTerminalView
from views.esp32_control import ESP32ControlView
from utils.constants import APP_NAME, APP_GEOMETRY


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(APP_GEOMETRY)
        self.center_window()

        self.device_controller = DeviceController()
        self.setup_ui()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tab_esp32 = self.tab_view.add("ESP32 Control")
        tab_devices = self.tab_view.add("Device Manager")
        tab_terminal = self.tab_view.add("Serial Terminal")

        self.esp32_view = ESP32ControlView(tab_esp32, None, self.device_controller)
        self.esp32_view.pack(fill="both", expand=True)

        self.device_view = DeviceManagerView(tab_devices, None, self.device_controller)
        self.device_view.pack(fill="both", expand=True)

        self.terminal_view = SerialTerminalView(tab_terminal, None, self.device_controller)
        self.terminal_view.pack(fill="both", expand=True)

        self.device_view.set_terminal_refresh(self.terminal_view.refresh_devices)
