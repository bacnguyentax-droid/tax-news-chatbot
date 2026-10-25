"""
Main application launcher for Outlook Tax Email Manager
"""

import sys
import os

# Ensure package path is added
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from outlook_tax_manager.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Outlook Tax Email Manager")

    window = MainWindow()
    # Explicitly maximize to full screen as requested
    window.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
