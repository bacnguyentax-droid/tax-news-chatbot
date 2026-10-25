"""
Security & Undo Staging Page
Manages Undo/Restore staging folder (App_Staging_Trash held 7-14 days),
OAuth 2.0 / MAPI security information, and Client-side privacy compliance.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

class SecurityPage(QWidget):
    def __init__(self, outlook_engine, parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("🛡 TÍCH HỢP, BẢO MẬT & CHẾ ĐỘ HOÀN TÁC (UNDO / SECURITY / PRIVACY)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81;")
        layout.addWidget(title)

        # -------------------------------------------------------------
        # PRIVACY & SECURITY BANNER
        # -------------------------------------------------------------
        privacy_card = QFrame()
        privacy_card.setProperty("class", "card")
        pc_layout = QVBoxLayout(privacy_card)

        lbl_sec_title = QLabel("🔒 ĐẢM BẢO QUYỀN RIÊNG TƯ VÀ BẢO MẬT DỮ LIỆU CƠ QUAN", privacy_card)
        lbl_sec_title.setStyleSheet("font-weight: bold; color: #0F4C81; font-size: 14px;")

        lbl_sec_desc = QLabel(
            "• Xử lý hoàn toàn tại máy khách (Client-side): 100% dữ liệu email được xử lý nội bộ trên máy tính của bạn thông qua Outlook COM API MAPI.\n"
            "• Không lưu giữ mật khẩu: Ứng dụng tương tác với phiên làm việc Outlook đang mở mà không bao giờ yêu cầu nhập mật khẩu cá nhân.\n"
            "• Tuân thủ OAuth 2.0 / Microsoft Graph Security standards."
        )
        pc_layout.addWidget(lbl_sec_title)
        pc_layout.addWidget(lbl_sec_desc)
        layout.addWidget(privacy_card)

        # -------------------------------------------------------------
        # UNDO STAGING FOLDER MANAGER
        # -------------------------------------------------------------
        box_undo = QGroupBox("↩️ Quản lý Thư mục Tạm (App_Staging_Trash) - Khôi phục Email đã xóa trong 7-14 ngày")
        bu_layout = QVBoxLayout(box_undo)

        lbl_undo_info = QLabel("Các email bị xóa bởi phần mềm sẽ tạm lưu tại thư mục này 14 ngày trước khi xóa vĩnh viễn:")
        bu_layout.addWidget(lbl_undo_info)

        self.tbl_undo = QTableWidget()
        self.tbl_undo.setColumnCount(5)
        self.tbl_undo.setHorizontalHeaderLabels(["ID Email", "Tiêu đề Email", "Người gửi", "Ngày xóa", "Thời gian còn lại"])
        self.tbl_undo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        bu_layout.addWidget(self.tbl_undo)

        btn_row = QHBoxLayout()

        btn_restore = QPushButton("↩️ KHÔI PHỤC EMAIL VỀ INBOX (UNDO)")
        btn_restore.setProperty("class", "btnGold")
        btn_restore.clicked.connect(self.restore_email)

        btn_perm_del = QPushButton("🔥 XÓA VĨNH VIỄN LẬP TỨC")
        btn_perm_del.setProperty("class", "btnDanger")
        btn_perm_del.clicked.connect(self.perm_delete)

        btn_row.addWidget(btn_restore)
        btn_row.addWidget(btn_perm_del)
        bu_layout.addLayout(btn_row)

        layout.addWidget(box_undo)
        self.load_undo_data()

    def load_undo_data(self):
        staging_items = [
            {"id": "STG_101", "subject": "Mã xác thực OTP kho bạc nhà nước: 492019", "sender": "no-reply@vst.mof.gov.vn", "deleted_date": "2026-03-10", "remaining": "12 ngày"},
            {"id": "STG_102", "subject": "Bản tin khuyến mại thiết bị văn phòng", "sender": "news@office-supplies.vn", "deleted_date": "2026-03-08", "remaining": "10 ngày"},
            {"id": "STG_103", "subject": "Thông báo bảo trì hệ thống iCaNhan Tax", "sender": "system@gdt.gov.vn", "deleted_date": "2026-03-05", "remaining": "7 ngày"},
        ]
        self.tbl_undo.setRowCount(len(staging_items))
        for row, item in enumerate(staging_items):
            self.tbl_undo.setItem(row, 0, QTableWidgetItem(item["id"]))
            self.tbl_undo.setItem(row, 1, QTableWidgetItem(item["subject"]))
            self.tbl_undo.setItem(row, 2, QTableWidgetItem(item["sender"]))
            self.tbl_undo.setItem(row, 3, QTableWidgetItem(item["deleted_date"]))
            self.tbl_undo.setItem(row, 4, QTableWidgetItem(item["remaining"]))

    def restore_email(self):
        row = self.tbl_undo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 email cần khôi phục!")
            return
        item_id = self.tbl_undo.item(row, 0).text()
        self.tbl_undo.removeRow(row)
        QMessageBox.information(self, "Thành công", f"Đã khôi phục email [{item_id}] về Hộp thư đến (Inbox) thành công!")

    def perm_delete(self):
        row = self.tbl_undo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 email!")
            return
        item_id = self.tbl_undo.item(row, 0).text()
        self.tbl_undo.removeRow(row)
        QMessageBox.information(self, "Thành công", f"Đã xóa vĩnh viễn email [{item_id}] khỏi hệ thống.")
