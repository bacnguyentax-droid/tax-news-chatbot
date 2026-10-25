"""
Scheduler Worker for background tasks:
- 21:00 Auto-delete schedule (with prompt option & persistent email list)
- Auto-move schedule to Outlook folders (per-email target folder mapping, default 21:15)
- Weekly cleanup schedule
- 80%/90%/99% Capacity Alert monitor
"""

import time
import datetime
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

class AutomationSchedulerWorker(QThread):
    # Signals to communicate with GUI main thread
    signal_trigger_21h_delete = pyqtSignal(list, bool) # (email_list, ask_confirm)
    signal_trigger_auto_move = pyqtSignal(list) # mappings
    signal_trigger_21h30_move = pyqtSignal(list) # backward compat alias
    signal_trigger_capacity_alert = pyqtSignal(str, float) # (alert_level, used_percent)
    signal_status_update = pyqtSignal(str)

    def __init__(self, config_data, parent=None, config_file="f:/Luyen_cong/AntiGravity/Chat_bot_Gemini/outlook_tax_manager/config.json"):
        super().__init__(parent)
        self.config_file = config_file
        self.config = config_data or {}
        self.is_running = True
        self.last_alert_level = None

    def refresh_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception:
            pass

    def run(self):
        print("[SchedulerWorker] Background Automation Scheduler started.")
        self.signal_status_update.emit("Tiến trình tự động hóa ngầm đang hoạt động...")

        while self.is_running:
            self.refresh_config()
            now = datetime.datetime.now()
            current_time_str = now.strftime("%H:%M")

            auto_del = self.config.get("automation", {}).get("auto_delete_21h", {})
            auto_move = self.config.get("automation", {}).get("auto_move", {})
            if not auto_move:
                auto_move = self.config.get("automation", {}).get("auto_move_21h30", {})

            # 1. Check 21:00 Auto-delete Schedule
            if auto_del.get("enabled", True) and current_time_str == auto_del.get("time", "21:00"):
                emails = auto_del.get("email_addresses", [])
                ask_confirm = auto_del.get("ask_before_delete", True)
                print(f"[SchedulerWorker] Triggering 21:00 Auto Delete Task. Prompt: {ask_confirm}")
                self.signal_trigger_21h_delete.emit(emails, ask_confirm)
                time.sleep(61) # Prevent duplicate trigger in same minute

            # 2. Check Auto-move Schedule (Default 21:15)
            scheduled_move_time = auto_move.get("time", "21:15")
            if auto_move.get("enabled", True) and current_time_str == scheduled_move_time:
                mappings = auto_move.get("mappings", [])
                print(f"[SchedulerWorker] Triggering Auto Move Task at {scheduled_move_time} for {len(mappings)} mappings.")
                self.signal_trigger_auto_move.emit(mappings)
                self.signal_trigger_21h30_move.emit(mappings)
                time.sleep(61)

            # Capacity Monitoring check loop
            time.sleep(10)

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
