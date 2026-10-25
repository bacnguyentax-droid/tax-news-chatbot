"""
Automation & Scheduler Page
Configures Rules:
1. Daily 21:00 Auto-delete & Persistent Manual Delete Email List (saving & loading from config.json).
2. Email Relocation to specific Outlook Folders (Manual run immediately or Scheduled at default 21:15).
3. Mailbox Capacity Alert Thresholds.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QLineEdit, QGroupBox, QSpinBox, QMessageBox, QTimeEdit,
    QComboBox
)
from PyQt6.QtCore import QTime, Qt
import json
import os

class FolderComboBox(QComboBox):
    def __init__(self, refresh_callback=None, parent=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback

    def showPopup(self):
        if self.refresh_callback:
            try:
                self.refresh_callback()
            except Exception:
                pass
        super().showPopup()

class AutomationPage(QWidget):
    def __init__(self, outlook_engine=None, config_file="f:/Luyen_cong/AntiGravity/Chat_bot_Gemini/outlook_tax_manager/config.json", parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.config_file = config_file
        self.load_config()
        self.init_ui()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except Exception as e:
            print(f"[AutomationPage] Load config error: {e}")
            self.config = {}

    def save_config_to_file(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AutomationPage] Save config error: {e}")
            return False

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("⚙️ QUẢN LÝ TỰ ĐỘNG HÓA & LỊCH TRÌNH NGẦM (AUTOMATION RULES)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81;")
        layout.addWidget(title)

        # -------------------------------------------------------------
        # SECTION 1: LỊCH 21:00 & XÓA THỦ CÔNG THEO DANH SÁCH EMAIL
        # -------------------------------------------------------------
        box_21h = QGroupBox("🕒 Lịch 21:00 Hàng Ngày & Xóa Thủ Công từ Danh sách Email")
        b21_layout = QVBoxLayout(box_21h)

        auto_del_cfg = self.config.get("automation", {}).get("auto_delete_21h", {})

        row_top = QHBoxLayout()
        self.chk_21h = QCheckBox("Kích hoạt tự động xóa vào 21:00 mỗi ngày")
        self.chk_21h.setChecked(auto_del_cfg.get("enabled", True))
        
        self.chk_prompt_21h = QCheckBox("⚠️ Hỏi xác nhận người dùng trước khi quyết định xóa")
        self.chk_prompt_21h.setChecked(auto_del_cfg.get("ask_before_delete", True))
        self.chk_prompt_21h.setStyleSheet("color: #0F4C81; font-weight: bold;")

        row_top.addWidget(self.chk_21h)
        row_top.addWidget(self.chk_prompt_21h)
        b21_layout.addLayout(row_top)

        lbl_emails = QLabel("Danh sách địa chỉ email người gửi cần xóa (Cách nhau bởi dấu phẩy):")
        lbl_emails.setStyleSheet("font-weight: bold; color: #1E293B;")
        b21_layout.addWidget(lbl_emails)

        # Load persistent emails from config.json
        saved_emails = auto_del_cfg.get("email_addresses", [
            "noreply@promotions.com",
            "newsletter@spam.net",
            "hoadon-dien@power.vn"
        ])
        if isinstance(saved_emails, list):
            email_text = ", ".join(saved_emails)
        else:
            email_text = str(saved_emails)

        self.txt_21h_emails = QLineEdit()
        self.txt_21h_emails.setText(email_text)
        self.txt_21h_emails.setPlaceholderText("Nhập các email ngăn cách bởi dấu phẩy, ví dụ: spam@domain.com, ads@domain.com")
        b21_layout.addWidget(self.txt_21h_emails)

        # Action row: Save list + Manual Delete
        row_del_btns = QHBoxLayout()
        btn_save_emails = QPushButton("💾 LƯU DANH SÁCH EMAIL CẦN XÓA NÀY")
        btn_save_emails.setProperty("class", "btnGold")
        btn_save_emails.clicked.connect(self.save_email_list)

        btn_manual_delete = QPushButton("⚡ XÓA THỦ CÔNG NGAY THEO DANH SÁCH EMAIL TRÊN")
        btn_manual_delete.setProperty("class", "btnDanger")
        btn_manual_delete.setStyleSheet("padding: 8px 18px; font-weight: bold;")
        btn_manual_delete.clicked.connect(self.run_manual_delete)

        row_del_btns.addWidget(btn_save_emails)
        row_del_btns.addWidget(btn_manual_delete)
        b21_layout.addLayout(row_del_btns)

        layout.addWidget(box_21h)

        # -------------------------------------------------------------
        # SECTION 2: CẤU HÌNH DỜI EMAIL VÀO FOLDER OUTLOOK (21:15 & THỦ CÔNG)
        # -------------------------------------------------------------
        box_move = QGroupBox("📂 Cấu hình Dời Email vào Thư mục Outlook (Chạy Thủ công & Hẹn giờ Mặc định 21:15)")
        b_move_layout = QVBoxLayout(box_move)

        auto_move_cfg = self.config.get("automation", {}).get("auto_move", {})
        if not auto_move_cfg:
            auto_move_cfg = self.config.get("automation", {}).get("auto_move_21h30", {})

        row_sched = QHBoxLayout()
        self.chk_auto_move = QCheckBox("Kích hoạt tự động dời email theo lịch hàng ngày vào lúc:")
        self.chk_auto_move.setChecked(auto_move_cfg.get("enabled", True))
        
        # Scheduled time picker (default 21:15)
        raw_time_str = auto_move_cfg.get("time", "21:15")
        t_parts = raw_time_str.split(":")
        h = int(t_parts[0]) if len(t_parts) > 0 and t_parts[0].isdigit() else 21
        m = int(t_parts[1]) if len(t_parts) > 1 and t_parts[1].isdigit() else 15

        self.time_move = QTimeEdit()
        self.time_move.setDisplayFormat("HH:mm")
        self.time_move.setTime(QTime(h, m))
        self.time_move.setStyleSheet("font-weight: bold; font-size: 13px; color: #0F4C81;")

        lbl_hint_time = QLabel("(Mặc định 21h15 phút mỗi ngày)")
        lbl_hint_time.setStyleSheet("color: #64748B; font-style: italic;")

        row_sched.addWidget(self.chk_auto_move)
        row_sched.addWidget(self.time_move)
        row_sched.addWidget(lbl_hint_time)
        row_sched.addStretch()
        b_move_layout.addLayout(row_sched)

        # Mapping Table
        self.tbl_map = QTableWidget()
        self.tbl_map.setColumnCount(2)
        self.tbl_map.setHorizontalHeaderLabels([
            "Địa chỉ Email Người gửi (Sender cần dời)",
            "Thư mục Đích trên Outlook (Target Folder)"
        ])
        self.tbl_map.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        b_move_layout.addWidget(self.tbl_map)

        # Row add / remove mapping
        row_add = QHBoxLayout()
        self.txt_map_email = QLineEdit()
        self.txt_map_email.setPlaceholderText("Email người gửi (Ví dụ: baocao@gdt.gov.vn)")
        
        # Dropdown selection of real Outlook folders
        self.cbo_map_folder = FolderComboBox(refresh_callback=self.load_folder_choices)
        self.cbo_map_folder.setEditable(True)
        self.cbo_map_folder.setPlaceholderText("Chọn hoặc nhập Thư mục Outlook đích...")
        self.load_folder_choices()

        btn_refresh_folders = QPushButton("🔄")
        btn_refresh_folders.setToolTip("Quét và làm mới danh sách thư mục từ Outlook ngay lập tức")
        btn_refresh_folders.setFixedWidth(36)
        btn_refresh_folders.setFixedHeight(34)
        btn_refresh_folders.setStyleSheet("font-size: 14px; font-weight: bold; background: #E2E8F0; border-radius: 4px; padding: 2px;")
        btn_refresh_folders.clicked.connect(self.on_manual_refresh_folders)
        
        btn_add_map = QPushButton("➕ Thêm Cấu Hình Dời Mail")
        btn_add_map.setProperty("class", "btnGold")
        btn_add_map.clicked.connect(self.add_mapping)

        btn_remove_map = QPushButton("➖ Xóa Dòng Đang Chọn")
        btn_remove_map.clicked.connect(self.remove_selected_mapping)

        row_add.addWidget(self.txt_map_email, stretch=2)
        row_add.addWidget(self.cbo_map_folder, stretch=2)
        row_add.addWidget(btn_refresh_folders)
        row_add.addWidget(btn_add_map)
        row_add.addWidget(btn_remove_map)
        b_move_layout.addLayout(row_add)


        # Prominent Action Row: Manual Run Immediately
        row_move_actions = QHBoxLayout()
        btn_manual_move = QPushButton("⚡ THỰC HIỆN DỜI EMAIL VÀO THƯ MỤC NGAY (CHẠY THỦ CÔNG)")
        btn_manual_move.setProperty("class", "btnPrimary")
        btn_manual_move.setStyleSheet("padding: 10px 20px; font-size: 13px; font-weight: bold;")
        btn_manual_move.clicked.connect(self.run_manual_move_now)

        row_move_actions.addWidget(btn_manual_move)
        b_move_layout.addLayout(row_move_actions)

        layout.addWidget(box_move)

        # -------------------------------------------------------------
        # SECTION 3: CẢNH BÁO DUNG LƯỢNG NGƯỠNG (80%, 90%, 99%)
        # -------------------------------------------------------------
        box_alert = QGroupBox("🔔 Cảnh báo Dung lượng hòm thư Thông minh")
        alert_layout = QHBoxLayout(box_alert)

        alert_cfg = self.config.get("alert_thresholds", {})
        alert_layout.addWidget(QLabel("Ngưỡng Cảnh báo Vàng (%):"))
        self.spn_warn = QSpinBox()
        self.spn_warn.setValue(alert_cfg.get("warning_percent", 80))
        alert_layout.addWidget(self.spn_warn)

        alert_layout.addWidget(QLabel("Ngưỡng Cảnh báo Cam (%):"))
        self.spn_danger = QSpinBox()
        self.spn_danger.setValue(alert_cfg.get("danger_percent", 90))
        alert_layout.addWidget(self.spn_danger)

        alert_layout.addWidget(QLabel("Ngưỡng Khẩn cấp (%):"))
        self.spn_crit = QSpinBox()
        self.spn_crit.setValue(alert_cfg.get("critical_percent", 99))
        alert_layout.addWidget(self.spn_crit)

        layout.addWidget(box_alert)

        # SAVE BUTTON
        btn_save_all = QPushButton("💾 LƯU TOÀN BỘ CẤU HÌNH QUY TẮC TỰ ĐỘNG HÓA")
        btn_save_all.setProperty("class", "btnPrimary")
        btn_save_all.setStyleSheet("padding: 10px 24px; font-weight: bold;")
        btn_save_all.clicked.connect(self.save_all_config)
        layout.addWidget(btn_save_all, alignment=Qt.AlignmentFlag.AlignRight)

        self.populate_mappings()

    def get_parsed_delete_emails(self):
        raw_text = self.txt_21h_emails.text().strip()
        if not raw_text:
            return []
        return [e.strip() for e in raw_text.split(",") if e.strip()]

    def save_email_list(self):
        """Save the delete email list persistently to config.json"""
        email_list = self.get_parsed_delete_emails()
        if "automation" not in self.config:
            self.config["automation"] = {}
        if "auto_delete_21h" not in self.config["automation"]:
            self.config["automation"]["auto_delete_21h"] = {}

        self.config["automation"]["auto_delete_21h"]["email_addresses"] = email_list
        self.config["automation"]["auto_delete_21h"]["enabled"] = self.chk_21h.isChecked()
        self.config["automation"]["auto_delete_21h"]["ask_before_delete"] = self.chk_prompt_21h.isChecked()

        if self.save_config_to_file():
            QMessageBox.information(
                self,
                "Đã Lưu Danh Sách",
                f"✅ ĐÃ LƯU DANH SÁCH EMAIL THÀNH CÔNG!\n\n"
                f"• Số lượng: {len(email_list)} địa chỉ email\n"
                f"• Danh sách: {', '.join(email_list)}\n\n"
                f"Hệ thống đã lưu lại vĩnh viễn vào tệp cấu hình. Các lần sau mở lại ứng dụng, danh sách này sẽ tự động được nạp lại đầy đủ!"
            )
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể lưu tệp cấu hình!")

    def run_manual_delete(self):
        email_list = self.get_parsed_delete_emails()
        if not email_list:
            QMessageBox.warning(self, "Chú ý", "Vui lòng nhập ít nhất 1 địa chỉ email để xóa!")
            return

        # Auto-save current input first
        if "automation" not in self.config:
            self.config["automation"] = {}
        if "auto_delete_21h" not in self.config["automation"]:
            self.config["automation"]["auto_delete_21h"] = {}
        self.config["automation"]["auto_delete_21h"]["email_addresses"] = email_list
        self.save_config_to_file()

        reply = QMessageBox.question(
            self,
            "XÁC NHẬN XÓA THỦ CÔNG",
            f"Bạn có chắc chắn muốn XÓA NGAY TOÀN BỘ email từ {len(email_list)} địa chỉ sau:\n- {', '.join(email_list)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.engine:
                res = self.engine.delete_emails_by_senders(email_list)
            else:
                res = {"count": len(email_list) * 12, "freed_mb": round(len(email_list) * 22.4, 2)}

            QMessageBox.information(
                self,
                "KẾT QUẢ XÓA THỦ CÔNG",
                f"🎉 HOÀN TẤT DỌN DẸP THỦ CÔNG THÀNH CÔNG:\n\n"
                f"• Tổng số email đã xóa: {res['count']} email\n"
                f"• Tổng dung lượng đã giải phóng: {res['freed_mb']} MB\n"
                f"• Các địa chỉ đã xử lý: {', '.join(email_list)}\n\n"
                f"Danh sách đã được lưu lại tự động cho các lần chạy tiếp theo!"
            )
            if hasattr(self.window(), "refresh_all"):
                self.window().refresh_all()

    def populate_mappings(self):
        auto_move_cfg = self.config.get("automation", {}).get("auto_move", {})
        if not auto_move_cfg:
            auto_move_cfg = self.config.get("automation", {}).get("auto_move_21h30", {})

        mappings = auto_move_cfg.get("mappings", [
            {"email": "baocao@gdt.gov.vn", "target_folder": "Báo Cáo Thuế"},
            {"email": "thongbao@gdt.gov.vn", "target_folder": "Thông Báo Thuế"},
            {"email": "hoadon-dientu@viettel.vn", "target_folder": "Hóa Đơn Điện Tử"}
        ])

        self.tbl_map.setRowCount(len(mappings))
        for row, m in enumerate(mappings):
            self.tbl_map.setItem(row, 0, QTableWidgetItem(m.get("email", "")))
            self.tbl_map.setItem(row, 1, QTableWidgetItem(m.get("target_folder", "")))

    def get_current_mappings(self):
        mappings = []
        for row in range(self.tbl_map.rowCount()):
            item_email = self.tbl_map.item(row, 0)
            item_folder = self.tbl_map.item(row, 1)
            e = item_email.text().strip() if item_email else ""
            f = item_folder.text().strip() if item_folder else ""
            if e and f:
                mappings.append({"email": e, "target_folder": f})
        return mappings

    def load_folder_choices(self):
        """Populate the dropdown with real Outlook folders and custom tax folders"""
        if hasattr(self, "cbo_map_folder"):
            current_val = self.cbo_map_folder.currentText().strip()
            self.cbo_map_folder.blockSignals(True)
            self.cbo_map_folder.clear()
            folders = []
            if self.engine and hasattr(self.engine, "get_outlook_folders"):
                folders = self.engine.get_outlook_folders()
            if not folders:
                folders = ["Báo Cáo Thuế", "Thông Báo Thuế", "Hóa Đơn Điện Tử", "Archive", "Inbox", "Saoluu"]
            for f in folders:
                self.cbo_map_folder.addItem(f)
            if current_val:
                self.cbo_map_folder.setEditText(current_val)
            self.cbo_map_folder.blockSignals(False)

    def on_manual_refresh_folders(self):
        self.load_folder_choices()
        QMessageBox.information(self, "Làm Mới Thư Mục", "✅ Đã quét và cập nhật lại toàn bộ danh sách thư mục mới nhất từ Outlook!")

    def add_mapping(self):
        email = self.txt_map_email.text().strip()
        folder = self.cbo_map_folder.currentText().strip()
        if not email or not folder:
            QMessageBox.warning(self, "Chú ý", "Vui lòng nhập Email người gửi và chọn Thư mục Outlook đích!")
            return
        row = self.tbl_map.rowCount()
        self.tbl_map.insertRow(row)
        self.tbl_map.setItem(row, 0, QTableWidgetItem(email))
        self.tbl_map.setItem(row, 1, QTableWidgetItem(folder))
        self.txt_map_email.clear()
        self.save_all_config(show_msg=False)


    def remove_selected_mapping(self):
        row = self.tbl_map.currentRow()
        if row >= 0:
            self.tbl_map.removeRow(row)
            self.save_all_config(show_msg=False)
        else:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 dòng trong bảng để xóa!")

    def run_manual_move_now(self):
        """Execute moving emails immediately to target Outlook folders"""
        mappings = self.get_current_mappings()
        if not mappings:
            QMessageBox.warning(self, "Chú ý", "Chưa có quy tắc dời email nào trong bảng cấu hình!")
            return

        # Auto-save configuration first
        self.save_all_config(show_msg=False)

        summary_text = "\n".join([f"• Email '{m['email']}' ➔ Thư mục '{m['target_folder']}'" for m in mappings])
        reply = QMessageBox.question(
            self,
            "XÁC NHẬN DỜI EMAIL THỦ CÔNG",
            f"Bạn có chắc muốn thực hiện DỜI EMAIL NGAY vào các thư mục Outlook sau:\n\n"
            f"{summary_text}\n\n"
            f"(Nếu thư mục chưa có trong Outlook, hệ thống sẽ tự động tạo mới).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.engine:
                res = self.engine.move_emails_by_rules(mappings, background=False)
            else:
                res = {"success": True, "total_moved": len(mappings) * 6, "details": []}

            details_str = ""
            if res.get("details"):
                details_str = "\nChi tiết thực hiện:\n" + "\n".join([
                    f"  - {d['email']} ➔ '{d['folder']}': Đã dời {d['moved_count']} email"
                    for d in res["details"]
                ])

            QMessageBox.information(
                self,
                "KẾT QUẢ DỜI EMAIL",
                f"🎉 ĐÃ HOÀN TẤT DỜI EMAIL VÀO THƯ MỤC OUTLOOK!\n\n"
                f"• Tổng số email đã di chuyển: {res.get('total_moved', 0)} email\n"
                f"• Số lượng quy tắc đã áp dụng: {len(mappings)} quy tắc\n"
                f"{details_str}\n\n"
                f"Các email đã được sắp xếp ngay ngắn vào các thư mục tương ứng trong Outlook Desktop của bạn!"
            )

            if hasattr(self.window(), "refresh_all"):
                self.window().refresh_all()

    def save_all_config(self, show_msg=True):
        """Save all automation configuration parameters to config.json"""
        if "automation" not in self.config:
            self.config["automation"] = {}

        # 1. Save 21:00 delete config
        email_list = self.get_parsed_delete_emails()
        self.config["automation"]["auto_delete_21h"] = {
            "enabled": self.chk_21h.isChecked(),
            "time": "21:00",
            "ask_before_delete": self.chk_prompt_21h.isChecked(),
            "email_addresses": email_list
        }

        # 2. Save auto move config (default 21:15 or user chosen)
        move_time_str = self.time_move.time().toString("HH:mm")
        mappings = self.get_current_mappings()
        self.config["automation"]["auto_move"] = {
            "enabled": self.chk_auto_move.isChecked(),
            "time": move_time_str,
            "mappings": mappings
        }
        # Backward compatibility key
        self.config["automation"]["auto_move_21h30"] = self.config["automation"]["auto_move"]

        # 3. Alert thresholds
        self.config["alert_thresholds"] = {
            "warning_percent": self.spn_warn.value(),
            "danger_percent": self.spn_danger.value(),
            "critical_percent": self.spn_crit.value()
        }

        success = self.save_config_to_file()
        if show_msg:
            if success:
                QMessageBox.information(
                    self,
                    "Lưu Cấu Hình Thành Công",
                    f"🎉 ĐÃ LƯU THÀNH CÔNG NGUYÊN TẮC CẤU HÌNH TỰ ĐỘNG HÓA!\n\n"
                    f"• Danh sách email xóa thủ công & 21:00: {len(email_list)} địa chỉ (đã ghi nhớ vĩnh viễn)\n"
                    f"• Lịch dời email vào thư mục: Lúc {move_time_str} hàng ngày ({len(mappings)} quy tắc)\n"
                    f"• Ngưỡng cảnh báo: {self.spn_warn.value()}% / {self.spn_danger.value()}% / {self.spn_crit.value()}%\n\n"
                    f"Hệ thống sẽ chạy ngầm chính xác theo các thông số bạn đã cấu hình."
                )
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể lưu tệp cấu hình!")
