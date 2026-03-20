#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SupeRois - Fighting Game Combo Manager for FightCade2"""
import sys
import os

# Windows DPI awareness
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import customtkinter
except ImportError:
    import tkinter.messagebox as mb
    import tkinter as tk
    root = tk.Tk(); root.withdraw()
    mb.showerror("Missing Dependency", "Please install dependencies:\n\npip install customtkinter Pillow pyautogui")
    sys.exit(1)

from ui.app import SupeRoisApp

if __name__ == "__main__":
    app = SupeRoisApp()
    app.run()
