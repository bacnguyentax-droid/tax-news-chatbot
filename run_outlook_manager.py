"""
Root launcher for Outlook Tax Email Manager
Run: python run_outlook_manager.py
"""

import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import traceback

# Add package directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def log_uncaught_exceptions(exctype, value, tb):
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("".join(traceback.format_exception(exctype, value, tb)))
    except Exception:
        pass
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = log_uncaught_exceptions

from PyQt6.QtWidgets import QApplication
from outlook_tax_manager.gui.main_window import MainWindow


def main():
    try:
        print("[Launcher] Starting QApplication...", flush=True)
        app = QApplication(sys.argv)
        app.setApplicationName("Phần mềm Quản lý Email Outlook - Phân hệ Thuế")

        print("[Launcher] Instantiating MainWindow...", flush=True)
        window = MainWindow()
        print("[Launcher] Showing MainWindow maximized...", flush=True)
        window.showMaximized()

        print("[Launcher] MainWindow is visible! Entering event loop...", flush=True)
        exit_code = app.exec()
        print(f"[Launcher] Event loop exited with code: {exit_code}", flush=True)
        sys.exit(0)
    except SystemExit:
        pass
    except Exception as e:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
