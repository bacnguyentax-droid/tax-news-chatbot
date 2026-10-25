"""
GUI Application for VPDT Document Processing Automation
Workflow:
  1. User enters username & password (or uses saved credentials).
  2. User selects document categories: 'CV Cảnh báo rủi ro', 'CV kiểm tra, xử lý hóa đơn'.
  3. User clicks 'Thực hiện'.
  4. App launches browser to http://vpdt.cucthue.hochiminhcity.gov.vn/.
  5. Waits for login completion (auto-fill or manual), then processes documents per workflow.
"""

import sys
import os
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit,
    QFrame, QMessageBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

import threading

from vpdt_manager.config import (
    BASE_URL,
    LOGIN_URL,
    load_config,
    save_config,
    set_credentials,
    get_credentials,
    CONFIG_FILE,
    SESSION_FILE,
    SCREENSHOT_PATH
)
from vpdt_manager.document_processor import VPDTDocumentProcessor


class ProcessWorker(QThread):
    """Background worker thread to execute the unified workflow."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)

    def __init__(
        self,
        doc_types: List[str],
        username: str = "",
        password: str = "",
        headless: bool = False,
        click_transfer: bool = True
    ):
        super().__init__()
        self.doc_types = doc_types
        self.username = username
        self.password = password
        self.headless = headless
        self.click_transfer = click_transfer
        self.stop_event = threading.Event()

    def run(self):
        processor = VPDTDocumentProcessor()
        res = processor.process_workflow(
            doc_types=self.doc_types,
            username=self.username,
            password=self.password,
            headless=self.headless,
            click_transfer=self.click_transfer,
            stop_event=self.stop_event,
            log_callback=lambda msg: self.log_signal.emit(msg)
        )
        self.finished_signal.emit(res)

    def stop_process(self):
        self.stop_event.set()


class VPDTLoginWindow(QMainWindow):
    """Unified Automation Window for VPDT Portal."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPDT Cục Thuế TP.HCM - Tự Động Hóa Xử Lý Văn Bản")
        self.resize(850, 800)
        self.proc_worker = None

        self._init_ui()
        self._load_saved_data()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e3a8a);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        title_label = QLabel("🏛️ HỆ THỐNG VĂN PHÒNG ĐIỆN TỬ - CỤC THUẾ TP.HCM")
        title_label.setStyleSheet("color: #ffffff; font-size: 17px; font-weight: bold;")
        sub_title = QLabel("Ứng dụng Tự động hóa: Mở cổng VPDT ➔ Đăng nhập ➔ Phân công & Luân chuyển văn bản")
        sub_title.setStyleSheet("color: #93c5fd; font-size: 13px;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(sub_title)
        main_layout.addWidget(header_card)

        # Main Control Card
        control_card = QFrame()
        control_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 18px;
            }
            QLabel {
                color: #1e293b;
                font-weight: 600;
                font-size: 13px;
            }
            QLineEdit {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: #f8fafc;
            }
            QLineEdit:focus {
                border-color: #2563eb;
                background-color: #ffffff;
            }
            QCheckBox {
                font-size: 13px;
                color: #1e293b;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        control_layout = QVBoxLayout(control_card)
        control_layout.setSpacing(14)

        # 1. Credentials Section
        cred_layout = QHBoxLayout()
        cred_layout.setSpacing(16)

        # Username
        user_box = QVBoxLayout()
        user_box.addWidget(QLabel("Tên đăng nhập (Username):"))
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Nhập username VPDT...")
        user_box.addWidget(self.txt_username)
        cred_layout.addLayout(user_box, 1)

        # Password
        pwd_box = QVBoxLayout()
        pwd_box.addWidget(QLabel("Mật khẩu (Password):"))
        pwd_inner = QHBoxLayout()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Nhập mật khẩu VPDT...")
        self.btn_toggle_pwd = QPushButton("👁️")
        self.btn_toggle_pwd.setFixedWidth(40)
        self.btn_toggle_pwd.setStyleSheet("""
            QPushButton {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 7px;
                background-color: #f1f5f9;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        self.btn_toggle_pwd.clicked.connect(self._toggle_password_visibility)
        pwd_inner.addWidget(self.txt_password)
        pwd_inner.addWidget(self.btn_toggle_pwd)
        pwd_box.addLayout(pwd_inner)
        cred_layout.addLayout(pwd_box, 1)

        control_layout.addLayout(cred_layout)

        # 2. Document Categories Selection Section
        cat_box = QGroupBox("Chọn các mục Loại văn bản cần xử lý:")
        cat_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
        """)
        cat_layout = QVBoxLayout(cat_box)
        cat_layout.setContentsMargins(14, 12, 14, 12)
        cat_layout.setSpacing(10)

        # Nhóm 1: Phân công chuyên viên
        lbl_group1 = QLabel("🔹 Nhóm 1: Phân công chuyên viên (Nam, Lanh ➔ Lưu văn bản ➔ Chuyển):")
        lbl_group1.setStyleSheet("font-size: 12px; font-weight: bold; color: #0284c7;")
        cat_layout.addWidget(lbl_group1)

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        self.chk_risk = QCheckBox("📄 CV Cảnh báo rủi ro")
        self.chk_invoice = QCheckBox("🧾 CV kiểm tra, xử lý hóa đơn")
        self.chk_invoice.setChecked(True)
        row1_layout.addWidget(self.chk_risk)
        row1_layout.addWidget(self.chk_invoice)
        row1_layout.addStretch()
        cat_layout.addLayout(row1_layout)

        # Phân cách
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.Shape.HLine)
        sep_line.setFrameShadow(QFrame.Shadow.Sunken)
        sep_line.setStyleSheet("color: #e2e8f0;")
        cat_layout.addWidget(sep_line)

        # Nhóm 2: Lưu văn bản trực tiếp
        lbl_group2 = QLabel("🔹 Nhóm 2: Lưu văn bản trực tiếp:")
        lbl_group2.setStyleSheet("font-size: 12px; font-weight: bold; color: #16a34a;")
        cat_layout.addWidget(lbl_group2)

        row2_layout = QVBoxLayout()
        row2_layout.setSpacing(8)
        self.chk_xphc = QCheckBox("⚖️ Quyết định xử phạt vi phạm hành chinh")
        self.chk_dc_xphc = QCheckBox("📝 Quyết định đính chính quyết định XPHC")
        self.chk_nnt_bo_dc = QCheckBox("🏢 TB Người nộp thuế bỏ địa chỉ kinh doanh")

        self.chk_xphc.setChecked(True)
        self.chk_dc_xphc.setChecked(True)
        self.chk_nnt_bo_dc.setChecked(True)

        row2_layout.addWidget(self.chk_xphc)
        row2_layout.addWidget(self.chk_dc_xphc)
        row2_layout.addWidget(self.chk_nnt_bo_dc)
        cat_layout.addLayout(row2_layout)

        control_layout.addWidget(cat_box)

        # 3. Preferences Options
        opts_layout = QHBoxLayout()
        self.chk_show_browser = QCheckBox("Hiển thị cửa sổ Chrome (Khuyến nghị bật để quan sát trực tiếp)")
        self.chk_show_browser.setChecked(True)
        self.chk_save_creds = QCheckBox("Ghi nhớ tài khoản trên máy này")
        self.chk_save_creds.setChecked(True)
        opts_layout.addWidget(self.chk_show_browser)
        opts_layout.addWidget(self.chk_save_creds)
        control_layout.addLayout(opts_layout)

        main_layout.addWidget(control_card)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        self.btn_close_browser = QPushButton("🛑 Đóng Trình duyệt")
        self.btn_close_browser.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 18px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_close_browser.setVisible(False)
        self.btn_close_browser.clicked.connect(self._close_browser)

        self.btn_execute = QPushButton("🚀 THỰC HIỆN")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16a34a, stop:1 #059669);
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px 32px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #15803d, stop:1 #047857);
            }
        """)
        self.btn_execute.clicked.connect(self._start_execution)

        self.btn_stop = QPushButton("🛑 Dừng Xử lý")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_execution)

        btn_layout.addWidget(self.btn_close_browser)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_execute)
        btn_layout.addWidget(self.btn_stop)
        main_layout.addLayout(btn_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                text-align: center;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #16a34a;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Live Logs Console
        log_label = QLabel("📋 Nhật ký hoạt động (Live Logs):")
        log_label.setStyleSheet("font-weight: bold; color: #334155;")
        main_layout.addWidget(log_label)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("""
            QTextEdit {
                background-color: #0b1120;
                color: #38bdf8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.txt_logs)

    def _toggle_password_visibility(self):
        if self.txt_password.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pwd.setText("🔒")
        else:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pwd.setText("👁️")

    def _load_saved_data(self):
        user, pwd = get_credentials()
        if user:
            self.txt_username.setText(user)
        if pwd:
            self.txt_password.setText(pwd)
        self.log("✅ Ứng dụng đã sẵn sàng. Vui lòng kiểm tra tài khoản, chọn loại văn bản và bấm '🚀 THỰC HIỆN'.")

    def log(self, text: str):
        self.txt_logs.append(text)

    def _set_ui_busy(self, busy: bool):
        self.btn_execute.setEnabled(not busy)
        self.btn_execute.setVisible(not busy)
        self.btn_stop.setVisible(busy)
        self.progress_bar.setVisible(busy)
        self.txt_username.setEnabled(not busy)
        self.txt_password.setEnabled(not busy)
        self.chk_risk.setEnabled(not busy)
        self.chk_invoice.setEnabled(not busy)
        self.chk_xphc.setEnabled(not busy)
        self.chk_dc_xphc.setEnabled(not busy)
        self.chk_nnt_bo_dc.setEnabled(not busy)

    def _start_execution(self):
        # 1. Check categories
        selected_types = []
        if self.chk_risk.isChecked():
            selected_types.append("CV Cảnh báo rủi ro")
        if self.chk_invoice.isChecked():
            selected_types.append("CV kiểm tra, xử lý hóa đơn")
        if self.chk_xphc.isChecked():
            selected_types.append("Quyết định xử phạt vi phạm hành chinh")
        if self.chk_dc_xphc.isChecked():
            selected_types.append("Quyết định đính chính quyết định XPHC")
        if self.chk_nnt_bo_dc.isChecked():
            selected_types.append("TB Người nộp thuế bỏ địa chỉ kinh doanh")

        if not selected_types:
            QMessageBox.warning(
                self,
                "Chưa chọn loại văn bản",
                "Vui lòng tích chọn ít nhất một mục văn bản cần xử lý trong danh sách."
            )
            return

        user = self.txt_username.text().strip()
        pwd = self.txt_password.text().strip()

        if self.chk_save_creds.isChecked() and user:
            set_credentials(user, pwd)

        self._set_ui_busy(True)
        self.btn_close_browser.setVisible(False)
        headless = not self.chk_show_browser.isChecked()

        self.log("\n" + "=" * 60)
        self.log("🚀 BẮT ĐẦU QUY TRÌNH THỰC HIỆN:")
        self.log(f"   - Tài khoản: {user or '(Chưa nhập - bạn sẽ tự đăng nhập trên trình duyệt)'}")
        self.log(f"   - Các mục xử lý: {', '.join(selected_types)}")
        self.log(f"   - Chế độ hiển thị: {'Mở cửa sổ Chrome' if not headless else 'Chạy ngầm'}")
        self.log(f"   - Điểm đến: {BASE_URL}")
        self.log("=" * 60)

        self.proc_worker = ProcessWorker(
            doc_types=selected_types,
            username=user,
            password=pwd,
            headless=headless,
            click_transfer=True
        )
        self.proc_worker.log_signal.connect(self.log)
        self.proc_worker.finished_signal.connect(self._on_execution_finished)
        self.proc_worker.start()

    def _stop_execution(self):
        if self.proc_worker:
            self.proc_worker.stop_process()
            self.log("🛑 Đã gửi lệnh dừng quy trình xử lý.")
            self.btn_stop.setEnabled(False)

    def _close_browser(self):
        self.btn_close_browser.setVisible(False)
        self.log("🛑 Đã yêu cầu đóng trình duyệt.")

    def _on_execution_finished(self, result: dict):
        self._set_ui_busy(False)
        self.btn_stop.setEnabled(True)
        self.log("-" * 60)

        if result["success"]:
            self.log(f"🎉 {result['message']}")
            self.btn_close_browser.setVisible(True)
            QMessageBox.information(
                self,
                "Hoàn thành xử lý!",
                f"{result['message']}\n\nTrình duyệt Chrome đang được giữ nguyên để bạn kiểm tra kết quả."
            )
        else:
            self.log(f"❌ {result['message']}")
            QMessageBox.critical(
                self,
                "Thông báo kết quả",
                f"Quá trình xử lý: {result['message']}"
            )

    def closeEvent(self, event):
        if self.proc_worker and hasattr(self.proc_worker, "stop_process"):
            self.proc_worker.stop_process()
        event.accept()


def launch_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("VPDT Automation Login")
    window = VPDTLoginWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
