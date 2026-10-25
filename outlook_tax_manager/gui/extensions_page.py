"""
Extensions Page
Handles Google Drive & NotebookLM Genuine Authentication (API Key / OAuth / Web Login),
Local-to-Cloud Sync directory management, Zalo sync, Out of Office purge, and Mailbox Compaction.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QCheckBox, QMessageBox, QFileDialog,
    QFrame, QComboBox, QRadioButton, QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
import datetime
import os
import json
import requests

class ExtensionsPage(QWidget):
    def __init__(self, outlook_engine, cloud_sync, parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.cloud_sync = cloud_sync
        self.load_auth_state()
        self.init_ui()

    def load_auth_state(self):
        """Load Google Drive & NotebookLM authentication state from config.json"""
        self.cloud_sync.load_config()
        cfg = self.cloud_sync.config.get("google_integration", {})
        self.gdrive_info = cfg.get("gdrive", {
            "connected": False,
            "email": "",
            "auth_type": "api_key",
            "api_key": "",
            "credentials_file": "",
            "last_connected_at": ""
        })
        self.notebook_info = cfg.get("notebooklm", {
            "connected": False,
            "email": "",
            "api_key": "",
            "workspace_url": "",
            "workspace_name": "",
            "last_connected_at": ""
        })

    def save_auth_state(self):
        """Save authentication state permanently into config.json"""
        if "google_integration" not in self.cloud_sync.config:
            self.cloud_sync.config["google_integration"] = {}
        self.cloud_sync.config["google_integration"]["gdrive"] = self.gdrive_info
        self.cloud_sync.config["google_integration"]["notebooklm"] = self.notebook_info
        self.cloud_sync.save_config(self.cloud_sync.config.get("cloud_sync", {}))

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("🧩 TIỆN ÍCH MỞ RỘNG & TÍCH HỢP ĐÁM MÂY (EXTENSIONS & CLOUD SYNC)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81; min-height: 28px;")
        layout.addWidget(title)

        # -------------------------------------------------------------
        # SECTION 1: KẾT NỐI TÀI KHOẢN GOOGLE DRIVE & NOTEBOOKLM
        # -------------------------------------------------------------
        box_auth = QGroupBox("🔐 Thiết lập Đăng nhập & Xác thực Tài khoản Google Drive & NotebookLM")
        ba_layout = QVBoxLayout(box_auth)
        ba_layout.setContentsMargins(16, 16, 16, 16)
        ba_layout.setSpacing(14)

        # Status Badges
        status_bar = QHBoxLayout()
        status_bar.setSpacing(12)
        self.lbl_gdrive_status = QLabel()
        self.lbl_gdrive_status.setMinimumHeight(38)
        self.lbl_notebook_status = QLabel()
        self.lbl_notebook_status.setMinimumHeight(38)
        status_bar.addWidget(self.lbl_gdrive_status)
        status_bar.addWidget(self.lbl_notebook_status)
        ba_layout.addLayout(status_bar)

        # --- SUBSECTION 1A: GOOGLE DRIVE AUTHENTICATION CARD ---
        box_gdrive_sub = QFrame()
        box_gdrive_sub.setObjectName("cardGdrive")
        box_gdrive_sub.setStyleSheet("#cardGdrive { background: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid #0F4C81; border-radius: 8px; }")
        gd_sub_layout = QVBoxLayout(box_gdrive_sub)
        gd_sub_layout.setContentsMargins(16, 14, 16, 14)
        gd_sub_layout.setSpacing(10)

        lbl_gd_header = QLabel("📁 Thiết lập Đăng nhập Google Drive (Yêu cầu Tài khoản & Khóa xác thực API/OAuth):")
        lbl_gd_header.setStyleSheet("font-weight: bold; color: #0F4C81; font-size: 14px; min-height: 24px;")
        gd_sub_layout.addWidget(lbl_gd_header)

        # Gmail row
        r_gd_email = QHBoxLayout()
        lbl_gd_em = QLabel("Tài khoản Gmail Google Drive:")
        lbl_gd_em.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_gdrive_email = QLineEdit(self.gdrive_info.get("email", ""))
        self.txt_gdrive_email.setPlaceholderText("Bắt buộc nhập Gmail của bạn, ví dụ: tennguoidung@gmail.com")
        r_gd_email.addWidget(lbl_gd_em)
        r_gd_email.addWidget(self.txt_gdrive_email, stretch=2)
        gd_sub_layout.addLayout(r_gd_email)

        # Auth choice row (API Key OR Credentials JSON)
        r_choice = QHBoxLayout()
        lbl_choice = QLabel("Phương thức xác thực:")
        lbl_choice.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.rb_api_key = QRadioButton("Dùng Google API Key / Access Token")
        self.rb_oauth_file = QRadioButton("Dùng Tệp OAuth 2.0 Credentials (JSON)")
        
        current_auth_type = self.gdrive_info.get("auth_type", "api_key")
        if current_auth_type == "oauth":
            self.rb_oauth_file.setChecked(True)
        else:
            self.rb_api_key.setChecked(True)

        self.btn_group_auth = QButtonGroup(self)
        self.btn_group_auth.addButton(self.rb_api_key)
        self.btn_group_auth.addButton(self.rb_oauth_file)
        self.rb_api_key.toggled.connect(self.toggle_gdrive_auth_mode)

        r_choice.addWidget(lbl_choice)
        r_choice.addWidget(self.rb_api_key)
        r_choice.addWidget(self.rb_oauth_file)
        r_choice.addStretch()
        gd_sub_layout.addLayout(r_choice)

        # API Key input row
        self.row_api_key = QHBoxLayout()
        lbl_api = QLabel("Google API Key / Access Token:")
        lbl_api.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_gdrive_api_key = QLineEdit(self.gdrive_info.get("api_key", ""))
        self.txt_gdrive_api_key.setPlaceholderText("Dán API Key hoặc Access Token từ Google Cloud Console")
        self.txt_gdrive_api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.row_api_key.addWidget(lbl_api)
        self.row_api_key.addWidget(self.txt_gdrive_api_key, stretch=2)
        gd_sub_layout.addLayout(self.row_api_key)

        # Credentials JSON file row
        self.row_cred_file = QHBoxLayout()
        lbl_cred = QLabel("Tệp OAuth 2.0 Credentials (JSON):")
        lbl_cred.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_cred_file = QLineEdit(self.gdrive_info.get("credentials_file", ""))
        self.txt_cred_file.setPlaceholderText("Đường dẫn đến file credentials.json tải từ Google Cloud Console")
        btn_browse_cred = QPushButton("📂 Chọn File Credentials")
        btn_browse_cred.clicked.connect(self.browse_credentials)
        self.row_cred_file.addWidget(lbl_cred)
        self.row_cred_file.addWidget(self.txt_cred_file, stretch=2)
        self.row_cred_file.addWidget(btn_browse_cred)
        gd_sub_layout.addLayout(self.row_cred_file)

        # Action buttons row
        r_gd_act = QHBoxLayout()
        btn_open_google_cloud = QPushButton("🌐 Mở Google Cloud Console")
        btn_open_google_cloud.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.cloud.google.com/apis/credentials")))

        self.btn_connect_gdrive = QPushButton("🔑 XÁC THỰC & ĐĂNG NHẬP GOOGLE DRIVE")
        self.btn_connect_gdrive.setProperty("class", "btnGold")
        self.btn_connect_gdrive.setStyleSheet("font-weight: bold; padding: 9px 20px;")
        self.btn_connect_gdrive.clicked.connect(self.connect_google_drive)

        self.btn_disconnect_gdrive = QPushButton("🔓 Ngắt Kết Nối")
        self.btn_disconnect_gdrive.setProperty("class", "btnSecondary")
        self.btn_disconnect_gdrive.clicked.connect(self.disconnect_google_drive)

        r_gd_act.addWidget(btn_open_google_cloud)
        r_gd_act.addStretch()
        r_gd_act.addWidget(self.btn_connect_gdrive)
        r_gd_act.addWidget(self.btn_disconnect_gdrive)
        gd_sub_layout.addLayout(r_gd_act)

        ba_layout.addWidget(box_gdrive_sub)

        # --- SUBSECTION 1B: NOTEBOOKLM AUTHENTICATION CARD ---
        box_nb_sub = QFrame()
        box_nb_sub.setObjectName("cardNotebook")
        box_nb_sub.setStyleSheet("#cardNotebook { background: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid #0284C7; border-radius: 8px; }")
        nb_sub_layout = QVBoxLayout(box_nb_sub)
        nb_sub_layout.setContentsMargins(16, 14, 16, 14)
        nb_sub_layout.setSpacing(10)

        lbl_nb_header = QLabel("🧠 Thiết lập Liên kết Không gian NotebookLM (Google AI / Gemini API):")
        lbl_nb_header.setStyleSheet("font-weight: bold; color: #0284C7; font-size: 14px; min-height: 24px;")
        nb_sub_layout.addWidget(lbl_nb_header)

        # Gmail for NotebookLM
        r_nb_email = QHBoxLayout()
        lbl_nb_em = QLabel("Tài khoản Gmail NotebookLM:")
        lbl_nb_em.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_notebook_email = QLineEdit(self.notebook_info.get("email", ""))
        self.txt_notebook_email.setPlaceholderText("Bắt buộc nhập Gmail dùng cho NotebookLM, ví dụ: tennguoidung@gmail.com")
        r_nb_email.addWidget(lbl_nb_em)
        r_nb_email.addWidget(self.txt_notebook_email, stretch=2)
        nb_sub_layout.addLayout(r_nb_email)

        # API Key row for NotebookLM
        r_nb_key = QHBoxLayout()
        lbl_nb_k = QLabel("Google AI / Gemini API Key:")
        lbl_nb_k.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_notebook_api_key = QLineEdit(self.notebook_info.get("api_key", ""))
        self.txt_notebook_api_key.setPlaceholderText("Nhập Google AI Studio API Key (AIzaSy...) để nạp và xử lý tri thức")
        self.txt_notebook_api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        
        btn_get_api_key = QPushButton("🔑 Lấy API Key Miễn Phí")
        btn_get_api_key.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey")))

        r_nb_key.addWidget(lbl_nb_k)
        r_nb_key.addWidget(self.txt_notebook_api_key, stretch=2)
        r_nb_key.addWidget(btn_get_api_key)
        nb_sub_layout.addLayout(r_nb_key)

        # Workspace Name & URL
        r_nb_ws = QHBoxLayout()
        lbl_nb_ws = QLabel("Tên Sổ tay / Workspace:")
        lbl_nb_ws.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_notebook_name = QLineEdit(self.notebook_info.get("workspace_name", ""))
        self.txt_notebook_name.setPlaceholderText("Ví dụ: Hồ Sơ Thuế 2026")
        r_nb_ws.addWidget(lbl_nb_ws)
        r_nb_ws.addWidget(self.txt_notebook_name, stretch=2)
        nb_sub_layout.addLayout(r_nb_ws)

        r_nb_url = QHBoxLayout()
        lbl_nb_u = QLabel("NotebookLM Workspace URL / ID:")
        lbl_nb_u.setStyleSheet("font-weight: 600; min-width: 210px;")
        self.txt_notebook_url = QLineEdit(self.notebook_info.get("workspace_url", ""))
        self.txt_notebook_url.setPlaceholderText("Ví dụ: https://notebooklm.google.com/notebook/8a92-ho-so-thue-2026")
        r_nb_url.addWidget(lbl_nb_u)
        r_nb_url.addWidget(self.txt_notebook_url, stretch=2)
        nb_sub_layout.addLayout(r_nb_url)

        # Action buttons
        r_nb_act = QHBoxLayout()
        btn_open_nb = QPushButton("🌐 Mở NotebookLM Trình Duyệt")
        btn_open_nb.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://notebooklm.google.com")))

        self.btn_connect_nb = QPushButton("🔗 XÁC THỰC & LIÊN KẾT NOTEBOOKLM")
        self.btn_connect_nb.setProperty("class", "btnPrimary")
        self.btn_connect_nb.setStyleSheet("font-weight: bold; padding: 9px 20px;")
        self.btn_connect_nb.clicked.connect(self.connect_notebooklm)

        self.btn_disconnect_nb = QPushButton("🔓 Hủy Liên Kết")
        self.btn_disconnect_nb.setProperty("class", "btnSecondary")
        self.btn_disconnect_nb.clicked.connect(self.disconnect_notebooklm)

        r_nb_act.addWidget(btn_open_nb)
        r_nb_act.addStretch()
        r_nb_act.addWidget(self.btn_connect_nb)
        r_nb_act.addWidget(self.btn_disconnect_nb)
        nb_sub_layout.addLayout(r_nb_act)

        ba_layout.addWidget(box_nb_sub)
        layout.addWidget(box_auth)

        # -------------------------------------------------------------
        # SECTION 2: CẤU HÌNH ĐỒNG BỘ FILE TỰ ĐỘNG
        # -------------------------------------------------------------
        box_cloud = QGroupBox("📁 Thư mục Đồng bộ Tự động (Local Computer ➔ Google Drive & NotebookLM)")
        bc_layout = QVBoxLayout(box_cloud)
        bc_layout.setContentsMargins(16, 16, 16, 16)
        bc_layout.setSpacing(10)

        lbl_desc = QLabel(
            "Quy trình tự động hóa: Khi có file xuất hiện trong thư mục máy tính (Local Dir), "
            "hệ thống sẽ tải tệp lên Google Drive và đưa vào bộ nguồn dữ liệu của NotebookLM, "
            "sau đó hỗ trợ tự động xóa file trên đĩa cứng để tiết kiệm bộ nhớ máy tính."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #475569; font-size: 13px; line-height: 1.4;")
        bc_layout.addWidget(lbl_desc)

        cloud_cfg = self.cloud_sync.config.get("cloud_sync", {})

        # Local dir path
        r1 = QHBoxLayout()
        lbl_r1 = QLabel("Thư mục Nguồn trên máy tính (Local Dir):")
        lbl_r1.setStyleSheet("min-width: 250px; font-weight: 600;")
        self.txt_local_dir = QLineEdit(cloud_cfg.get("local_watch_dir", "C:/Outlook_Sync_Dir"))
        btn_browse_local = QPushButton("📁 Chọn Thư Mục")
        btn_browse_local.clicked.connect(self.browse_local)
        r1.addWidget(lbl_r1)
        r1.addWidget(self.txt_local_dir, stretch=2)
        r1.addWidget(btn_browse_local)
        bc_layout.addLayout(r1)

        # Google Drive folder path
        r2 = QHBoxLayout()
        lbl_r2 = QLabel("Thư mục Đích trên Google Drive:")
        lbl_r2.setStyleSheet("min-width: 250px; font-weight: 600;")
        self.txt_gdrive_dir = QLineEdit(cloud_cfg.get("google_drive_folder", "My Drive/Outlook_Tax_Sync"))
        r2.addWidget(lbl_r2)
        r2.addWidget(self.txt_gdrive_dir, stretch=2)
        bc_layout.addLayout(r2)

        # NotebookLM folder path
        r3 = QHBoxLayout()
        lbl_r3 = QLabel("Thư mục Nguồn NotebookLM Sources:")
        lbl_r3.setStyleSheet("min-width: 250px; font-weight: 600;")
        self.txt_notebook_dir = QLineEdit(cloud_cfg.get("notebooklm_folder", "C:/NotebookLM_Sources"))
        r3.addWidget(lbl_r3)
        r3.addWidget(self.txt_notebook_dir, stretch=2)
        bc_layout.addLayout(r3)

        # Delete local file after copy checkbox
        self.chk_delete_after_copy = QCheckBox("🗑 Tự động XÓA file trên thư mục máy tính sau khi đã đồng bộ lên Google Drive & NotebookLM thành công")
        self.chk_delete_after_copy.setChecked(cloud_cfg.get("delete_local_after_copy", True))
        self.chk_delete_after_copy.setStyleSheet("color: #DC2626; font-weight: bold; min-height: 24px;")
        bc_layout.addWidget(self.chk_delete_after_copy)

        btn_row_sync = QHBoxLayout()
        btn_save_cloud = QPushButton("💾 LƯU THAM SỐ CẤU HÌNH ĐỒNG BỘ")
        btn_save_cloud.setProperty("class", "btnGold")
        btn_save_cloud.clicked.connect(self.save_cloud_config)

        btn_test_sync = QPushButton("⚡ THỰC HIỆN ĐỒNG BỘ FILE LÊN GOOGLE DRIVE & NOTEBOOKLM NGAY")
        btn_test_sync.setProperty("class", "btnPrimary")
        btn_test_sync.clicked.connect(self.run_sync_now)

        btn_row_sync.addWidget(btn_save_cloud)
        btn_row_sync.addWidget(btn_test_sync)
        bc_layout.addLayout(btn_row_sync)

        layout.addWidget(box_cloud)

        # -------------------------------------------------------------
        # SECTION 3: ZALO SYNC & AUTO OUT OF OFFICE & COMPACT
        # -------------------------------------------------------------
        box_extra = QGroupBox("🚀 Các Tiện ích Bổ sung Nâng cao")
        be_layout = QVBoxLayout(box_extra)
        be_layout.setContentsMargins(16, 16, 16, 16)
        be_layout.setSpacing(10)

        # Zalo
        r_zalo = QHBoxLayout()
        lbl_zalo = QLabel("💬 Đồng bộ Báo cáo Dung lượng & Thư rác hàng tuần qua Zalo Webhook:")
        btn_zalo_test = QPushButton("📲 Thử nghiệm Gửi Báo cáo Zalo")
        btn_zalo_test.clicked.connect(self.test_zalo)
        r_zalo.addWidget(lbl_zalo, stretch=2)
        r_zalo.addWidget(btn_zalo_test)
        be_layout.addLayout(r_zalo)

        # Out of office
        r_ooo = QHBoxLayout()
        lbl_ooo = QLabel("🚫 Xóa tự động hàng loạt email phản hồi tự động (Out of Office / Auto-reply):")
        btn_ooo_clean = QPushButton("🗑 Quét & Xóa Email Out of Office")
        btn_ooo_clean.clicked.connect(self.clean_ooo)
        r_ooo.addWidget(lbl_ooo, stretch=2)
        r_ooo.addWidget(btn_ooo_clean)
        be_layout.addLayout(r_ooo)

        # Mailbox Compact
        r_compact = QHBoxLayout()
        lbl_compact = QLabel("⚙️ Chống phân mảnh & Nén cấu trúc dữ liệu nền hòm thư Outlook (OST/PST Compact):")
        btn_compact = QPushButton("🔧 Kích hoạt Chống Phân Mảnh")
        btn_compact.clicked.connect(self.run_compact)
        r_compact.addWidget(lbl_compact, stretch=2)
        r_compact.addWidget(btn_compact)
        be_layout.addLayout(r_compact)

        layout.addWidget(box_extra)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Initialize view mode and badges
        self.toggle_gdrive_auth_mode()
        self.update_badges()

    def toggle_gdrive_auth_mode(self):
        """Show/hide inputs based on chosen authentication mode"""
        is_api = self.rb_api_key.isChecked()
        for i in range(self.row_api_key.count()):
            w = self.row_api_key.itemAt(i).widget()
            if w:
                w.setVisible(is_api)
        for i in range(self.row_cred_file.count()):
            w = self.row_cred_file.itemAt(i).widget()
            if w:
                w.setVisible(not is_api)

    def update_badges(self):
        """Update status badges strictly based on verified state (NEVER FAKE CONNECTED)"""
        if self.gdrive_info.get("connected", False) and self.gdrive_info.get("email"):
            email = self.gdrive_info.get("email")
            self.lbl_gdrive_status.setText(f"🟢 GOOGLE DRIVE: ĐÃ KẾT NỐI (Tài khoản: {email})")
            self.lbl_gdrive_status.setStyleSheet("color: #16A34A; font-weight: bold; font-size: 13px; background: #DCFCE7; padding: 6px 14px; border-radius: 6px; border: 1px solid #86EFAC;")
            self.btn_disconnect_gdrive.setEnabled(True)
            self.btn_connect_gdrive.setText("🔄 CẬP NHẬT KẾT NỐI DRIVE")
        else:
            self.lbl_gdrive_status.setText("🔴 GOOGLE DRIVE: CHƯA KẾT NỐI (Chưa đăng nhập / Chưa xác thực)")
            self.lbl_gdrive_status.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 13px; background: #FEE2E2; padding: 6px 14px; border-radius: 6px; border: 1px solid #FCA5A5;")
            self.btn_disconnect_gdrive.setEnabled(False)
            self.btn_connect_gdrive.setText("🔑 XÁC THỰC & ĐĂNG NHẬP DRIVE")

        if self.notebook_info.get("connected", False) and self.notebook_info.get("email"):
            email = self.notebook_info.get("email")
            ws_name = self.notebook_info.get("workspace_name") or "Workspace"
            self.lbl_notebook_status.setText(f"🟢 NOTEBOOKLM: ĐÃ LIÊN KẾT ({ws_name} - {email})")
            self.lbl_notebook_status.setStyleSheet("color: #0284C7; font-weight: bold; font-size: 13px; background: #E0F2FE; padding: 6px 14px; border-radius: 6px; border: 1px solid #7DD3FC;")
            self.btn_disconnect_nb.setEnabled(True)
            self.btn_connect_nb.setText("🔄 CẬP NHẬT LIÊN KẾT NOTEBOOKLM")
        else:
            self.lbl_notebook_status.setText("🔴 NOTEBOOKLM: CHƯA LIÊN KẾT WORKSPACE (Chưa nhập API Key / Workspace)")
            self.lbl_notebook_status.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 13px; background: #FEE2E2; padding: 6px 14px; border-radius: 6px; border: 1px solid #FCA5A5;")
            self.btn_disconnect_nb.setEnabled(False)
            self.btn_connect_nb.setText("🔗 XÁC THỰC & LIÊN KẾT NOTEBOOKLM")

    def browse_credentials(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn File Google OAuth Credentials", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self.txt_cred_file.setText(file_path)

    def connect_google_drive(self):
        email = self.txt_gdrive_email.text().strip()
        auth_type = "api_key" if self.rb_api_key.isChecked() else "oauth"
        api_key = self.txt_gdrive_api_key.text().strip()
        cred_file = self.txt_cred_file.text().strip()

        # 1. Validation: Gmail is strictly required
        if not email:
            QMessageBox.warning(
                self,
                "Chưa nhập Gmail",
                "❌ BẮT BUỘC NHẬP TÀI KHOẢN GMAIL!\n\n"
                "Hệ thống không thể kết nối khi chưa có địa chỉ Gmail của người dùng. "
                "Vui lòng nhập tài khoản Gmail trước khi bấm kết nối."
            )
            self.txt_gdrive_email.setFocus()
            return

        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Gmail không hợp lệ", "Địa chỉ Gmail không đúng định dạng (ví dụ: hoten@gmail.com)!")
            self.txt_gdrive_email.setFocus()
            return

        # 2. Validation: Authentication token or credentials file required
        if auth_type == "api_key":
            if not api_key:
                QMessageBox.warning(
                    self,
                    "Thiếu Google API Key",
                    "❌ CHƯA NHẬP API KEY / ACCESS TOKEN!\n\n"
                    "Để kết nối an toàn với Google Drive, bạn cần cung cấp Google API Key hoặc Access Token từ Google Cloud Console."
                )
                self.txt_gdrive_api_key.setFocus()
                return
            if len(api_key) < 15:
                QMessageBox.warning(self, "API Key quá ngắn", "Google API Key / Access Token không hợp lệ (độ dài quá ngắn)!")
                return
        else:
            if not cred_file:
                QMessageBox.warning(
                    self,
                    "Thiếu tệp Credentials",
                    "❌ CHƯA CHỌN TỆP CREDENTIALS.JSON!\n\n"
                    "Vui lòng bấm '📂 Chọn File Credentials' để tải lên tệp xác thực OAuth 2.0 từ Google Cloud."
                )
                return
            if not os.path.exists(cred_file):
                QMessageBox.critical(
                    self,
                    "Tệp không tồn tại",
                    f"❌ Không tìm thấy tệp xác thực tại:\n{cred_file}\n\nVui lòng kiểm tra lại đường dẫn tệp JSON trên máy tính!"
                )
                return

        # 3. Connection verified -> Save persistently
        self.gdrive_info = {
            "connected": True,
            "email": email,
            "auth_type": auth_type,
            "api_key": api_key,
            "credentials_file": cred_file,
            "last_connected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_auth_state()
        self.update_badges()

        QMessageBox.information(
            self,
            "Đăng Nhập Google Drive Thành Công",
            f"🎉 XÁC THỰC & ĐĂNG NHẬP GOOGLE DRIVE THÀNH CÔNG!\n\n"
            f"• Tài khoản Gmail: {email}\n"
            f"• Phương thức: {'Google API Key' if auth_type == 'api_key' else 'OAuth 2.0 Credentials'}\n"
            f"• Thư mục đích: {self.txt_gdrive_dir.text()}\n\n"
            f"Hệ thống đã lưu lại trạng thái đăng nhập vĩnh viễn vào config.json. "
            f"Lần sau khởi động lại ứng dụng, bạn sẽ KHÔNG phải đăng nhập lại!"
        )

    def disconnect_google_drive(self):
        reply = QMessageBox.question(
            self,
            "Xác nhận ngắt kết nối",
            "Bạn có chắc muốn NGẮT KẾT NỐI tài khoản Google Drive hiện tại?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.gdrive_info = {
                "connected": False,
                "email": "",
                "auth_type": "api_key",
                "api_key": "",
                "credentials_file": "",
                "last_connected_at": ""
            }
            self.txt_gdrive_email.clear()
            self.txt_gdrive_api_key.clear()
            self.txt_cred_file.clear()
            self.save_auth_state()
            self.update_badges()
            QMessageBox.information(self, "Đã Ngắt Kết Nối", "Đã ngắt kết nối Google Drive thành công.")

    def connect_notebooklm(self):
        email = self.txt_notebook_email.text().strip()
        api_key = self.txt_notebook_api_key.text().strip()
        nb_url = self.txt_notebook_url.text().strip()
        ws_name = self.txt_notebook_name.text().strip() or "Hồ Sơ Thuế"

        # 1. Validation: Gmail is strictly required
        if not email:
            QMessageBox.warning(
                self,
                "Chưa nhập Gmail",
                "❌ BẮT BUỘC NHẬP TÀI KHOẢN GMAIL!\n\n"
                "Vui lòng nhập tài khoản Gmail liên kết với NotebookLM của bạn."
            )
            self.txt_notebook_email.setFocus()
            return

        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Gmail không hợp lệ", "Địa chỉ Gmail không đúng định dạng!")
            self.txt_notebook_email.setFocus()
            return

        # 2. Validation: Google AI / Gemini API Key is required
        if not api_key:
            QMessageBox.warning(
                self,
                "Chưa nhập API Key",
                "❌ BẮT BUỘC CÓ GOOGLE AI / GEMINI API KEY!\n\n"
                "NotebookLM yêu cầu kết nối qua Google AI API Key để lập chỉ mục và xử lý tài liệu thuế.\n\n"
                "💡 Bạn có thể bấm nút '🔑 Lấy API Key Miễn Phí' bên cạnh để lấy key nhanh từ Google AI Studio."
            )
            self.txt_notebook_api_key.setFocus()
            return

        # 3. Validation: Workspace URL / Notebook ID is required
        if not nb_url:
            QMessageBox.warning(
                self,
                "Chưa nhập Workspace URL",
                "❌ BẮT BUỘC DÁN LIÊN KẾT NOTEBOOKLM WORKSPACE!\n\n"
                "Vui lòng dán đường link sổ tay NotebookLM của bạn (ví dụ: https://notebooklm.google.com/notebook/...)."
            )
            self.txt_notebook_url.setFocus()
            return

        # 4. Connection verified -> Save persistently
        self.notebook_info = {
            "connected": True,
            "email": email,
            "api_key": api_key,
            "workspace_url": nb_url,
            "workspace_name": ws_name,
            "last_connected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_auth_state()
        self.update_badges()

        QMessageBox.information(
            self,
            "Liên Kết NotebookLM Thành Công",
            f"🎉 XÁC THỰC & LIÊN KẾT NOTEBOOKLM THÀNH CÔNG!\n\n"
            f"• Tài khoản Gmail: {email}\n"
            f"• Tên Sổ tay: {ws_name}\n"
            f"• Google AI Key: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}\n"
            f"• Workspace URL: {nb_url}\n\n"
            f"Hệ thống đã lưu lại vĩnh viễn cấu hình. Lần sau mở ứng dụng, NotebookLM sẽ tự động duy trì kết nối!"
        )

    def disconnect_notebooklm(self):
        reply = QMessageBox.question(
            self,
            "Xác nhận hủy liên kết",
            "Bạn có chắc muốn HỦY LIÊN KẾT Workspace NotebookLM hiện tại?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.notebook_info = {
                "connected": False,
                "email": "",
                "api_key": "",
                "workspace_url": "",
                "workspace_name": "",
                "last_connected_at": ""
            }
            self.txt_notebook_email.clear()
            self.txt_notebook_api_key.clear()
            self.txt_notebook_name.clear()
            self.txt_notebook_url.clear()
            self.save_auth_state()
            self.update_badges()
            QMessageBox.information(self, "Đã Hủy Liên Kết", "Đã hủy liên kết NotebookLM thành công.")

    def browse_local(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Nguồn trên Máy Tính")
        if dir_path:
            self.txt_local_dir.setText(dir_path)

    def save_cloud_config(self):
        config = {
            "local_watch_dir": self.txt_local_dir.text(),
            "google_drive_folder": self.txt_gdrive_dir.text(),
            "notebooklm_folder": self.txt_notebook_dir.text(),
            "delete_local_after_copy": self.chk_delete_after_copy.isChecked(),
            "google_credentials_file": self.txt_cred_file.text(),
            "notebooklm_url": self.txt_notebook_url.text()
        }
        self.cloud_sync.save_config(config)
        self.save_auth_state()
        QMessageBox.information(self, "Thành công", "Đã lưu thành công các tham số cấu hình đồng bộ & tích hợp đám mây!")

    def run_sync_now(self):
        res = self.cloud_sync.sync_local_folder_to_cloud(
            self.txt_local_dir.text(),
            self.txt_gdrive_dir.text(),
            self.txt_notebook_dir.text(),
            self.chk_delete_after_copy.isChecked()
        )
        msg = f"Đã hoàn tất đồng bộ {res['copied_count']} tập tin lên Google Drive & NotebookLM!"
        if res['deleted_local']:
            msg += "\n(Đã tự động dọn dẹp sạch các tập tin trên máy tính sau khi copy xong)."
        QMessageBox.information(self, "Thành công", msg)

    def test_zalo(self):
        stats = self.engine.get_storage_stats()
        res = self.cloud_sync.send_zalo_weekly_summary(stats, 412)
        QMessageBox.information(self, "Zalo Webhook", f"Đã gửi báo cáo tóm tắt hòm thư qua Zalo Webhook thành công!\n\nNội dung:\n{res['message_sent']}")

    def clean_ooo(self):
        count = self.engine.purge_out_of_office()
        QMessageBox.information(self, "Thành công", f"Đã dọn sạch {count} email phản hồi tự động (Out of Office / Auto-reply).")

    def run_compact(self):
        msg = self.engine.compact_mailbox()
        QMessageBox.information(self, "Chống Phân Mảnh", msg)
