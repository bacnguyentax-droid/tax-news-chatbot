"""
Main Application Window for Outlook Email Tax Manager
Combines Header, Sidebar navigation, Stacked Pages, and System Tray background integration.
Màu sắc ứng dụng chuẩn dichvucong.gdt.gov.vn, hiển thị Mặc định FULL MÀN HÌNH.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QSystemTrayIcon,
    QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

from outlook_tax_manager.theme import TAX_THEME_QSS
from outlook_tax_manager.core.outlook_engine import OutlookEngine
from outlook_tax_manager.core.rule_engine import RuleEngine
from outlook_tax_manager.core.cloud_sync import CloudSyncManager
from outlook_tax_manager.automation.scheduler import AutomationSchedulerWorker

from outlook_tax_manager.gui.dashboard_page import DashboardPage
from outlook_tax_manager.gui.cleanup_page import CleanupPage
from outlook_tax_manager.gui.attachments_page import AttachmentsPage
from outlook_tax_manager.gui.automation_page import AutomationPage
from outlook_tax_manager.gui.extensions_page import ExtensionsPage
from outlook_tax_manager.gui.security_page import SecurityPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PHẦN MỀM QUẢN LÝ & DỌN DẸP EMAIL OUTLOOK - PHÂN HỆ THUẾ")
        
        # Initialize Core Engines
        self.outlook_engine = OutlookEngine()
        self.rule_engine = RuleEngine()
        self.cloud_sync = CloudSyncManager()

        # Apply QSS Styling
        self.setStyleSheet(TAX_THEME_QSS)

        # Build UI Structure
        self.init_ui()

        # Launch Background Automation Worker Thread
        self.start_automation_worker()

        # Show Fullscreen / Maximized by default as requested
        self.showMaximized()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. HEADER BANNER (MÀU ĐỎ THUẾ DICHVUCONG.GDT.GOV.VN)
        # -------------------------------------------------------------
        header = QFrame()
        header.setObjectName("headerBanner")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title_container = QVBoxLayout()
        title = QLabel("HỆ THỐNG QUẢN LÝ & DỌN DẸP EMAIL OUTLOOK")
        title.setObjectName("headerTitle")
        subtitle = QLabel("TỔNG CỤC THUẾ - CỔNG DỊCH VỤ CÔNG TỰ ĐỘNG HÓA HÒM THƯ DOANH NGHIỆP / CƠ QUAN")
        subtitle.setObjectName("headerSubtitle")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        # System Status Indicator
        status_lbl = QLabel("🟢 Đã kết nối Outlook COM")
        status_lbl.setStyleSheet("color: #FFECB3; font-weight: bold; background: rgba(0,0,0,0.2); padding: 6px 12px; border-radius: 14px;")

        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(status_lbl)

        root_layout.addWidget(header)

        # -------------------------------------------------------------
        # 2. BODY CONTENT (SIDEBAR + STACKED PAGES)
        # -------------------------------------------------------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 10, 0, 10)
        sb_layout.setSpacing(4)

        self.nav_buttons = []

        nav_items = [
            ("📊  Bảng điều khiển & Phân tích", 0),
            ("🧹  Công cụ Dọn dẹp Thông minh", 1),
            ("📎  Quản lý File Đính kèm", 2),
            ("⚙️  Tự động hóa & Lịch trình", 3),
            ("🧩  Tiện ích & Google Drive", 4),
            ("🛡  Bảo mật & Hoàn tác Undo", 5),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_page(idx))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Quick Manual Refresh Button
        btn_refresh = QPushButton("🔄  Làm mới dữ liệu")
        btn_refresh.setStyleSheet("color: #FFD700; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh_all)
        sb_layout.addWidget(btn_refresh)

        body_layout.addWidget(sidebar)

        # Stacked Pages Widget
        self.stacked_pages = QStackedWidget()

        self.page_dashboard = DashboardPage(self.outlook_engine)
        self.page_cleanup = CleanupPage(self.outlook_engine, self.rule_engine)
        self.page_attachments = AttachmentsPage(self.outlook_engine)
        self.page_automation = AutomationPage(self.outlook_engine)
        self.page_extensions = ExtensionsPage(self.outlook_engine, self.cloud_sync)
        self.page_security = SecurityPage(self.outlook_engine)

        self.stacked_pages.addWidget(self.page_dashboard)
        self.stacked_pages.addWidget(self.page_cleanup)
        self.stacked_pages.addWidget(self.page_attachments)
        self.stacked_pages.addWidget(self.page_automation)
        self.stacked_pages.addWidget(self.page_extensions)
        self.stacked_pages.addWidget(self.page_security)

        body_layout.addWidget(self.stacked_pages, stretch=1)
        root_layout.addLayout(body_layout)

        # Select first tab by default
        self.switch_page(0)

    def switch_page(self, index):
        self.stacked_pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 3 and hasattr(self, "page_automation") and hasattr(self.page_automation, "load_folder_choices"):
            self.page_automation.load_folder_choices()

    def refresh_all(self):
        self.page_dashboard.load_data()
        self.page_cleanup.load_data()
        self.page_attachments.load_data()
        if hasattr(self, "page_automation") and hasattr(self.page_automation, "load_folder_choices"):
            self.page_automation.load_folder_choices()
        QMessageBox.information(self, "Làm mới", "Đã cập nhật lại toàn bộ dữ liệu hòm thư Outlook mới nhất!")

    def start_automation_worker(self):
        self.worker = AutomationSchedulerWorker(self.cloud_sync.config, self)
        self.worker.signal_trigger_21h_delete.connect(self.handle_21h_delete_event)
        self.worker.signal_trigger_auto_move.connect(self.handle_auto_move_event)
        self.worker.signal_trigger_21h30_move.connect(self.handle_auto_move_event)
        self.worker.start()

    def handle_21h_delete_event(self, emails, ask_confirm):
        if ask_confirm:
            reply = QMessageBox.question(
                self,
                "🕒 LỊCH 21:00 - TỰ ĐỘNG XÓA EMAIL",
                f"Đã đến 21:00. Bạn có đồng ý xóa tự động {len(emails)} email từ danh sách cấu hình không?\n\nDanh sách: {', '.join(emails)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                res = self.outlook_engine.delete_emails_by_senders(emails)
                QMessageBox.information(self, "Thành công", f"Đã xóa tự động các email từ danh sách (Giải phóng {res['freed_mb']} MB).")
        else:
            res = self.outlook_engine.delete_emails_by_senders(emails)
            print(f"[Automation] Silent 21:00 delete executed for {len(emails)} senders.")

    def handle_auto_move_event(self, mappings):
        res = self.outlook_engine.move_emails_by_rules(mappings, background=True)
        print(f"[Automation] Scheduled auto move executed for {len(mappings)} mappings.")

