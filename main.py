import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from database.db_manager import init_db
from views.app import App


def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    init_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
