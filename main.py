#!/usr/bin/env python3
import sys
from gui.main_window import VirtualizationManagerApp, check_dependencies
import tkinter as tk

def main():
    if not check_dependencies():
        return  # Salir si faltan dependencias
        
    root = tk.Tk()
    app = VirtualizationManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()