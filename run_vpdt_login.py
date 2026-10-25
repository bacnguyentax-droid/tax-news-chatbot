"""
Root launcher for VPDT Automation - Phase 1 Login Tester
Run:
    python run_vpdt_login.py
"""

import sys
import os

# Fix console encoding
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

# Add current workspace to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vpdt_manager.gui_login import launch_gui

if __name__ == "__main__":
    launch_gui()
