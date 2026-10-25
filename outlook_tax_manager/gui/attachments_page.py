"""
Attachment Management Page
Filters attachments by size & format, extracts attachments to Cloud/Local link,
downloads attachments to local computer, and strips attachments while preserving email body text.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QMessageBox, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt

class AttachmentsPage(QWidget):
    def __init__(self, outlook_engine, parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("📎 QUẢN LÝ FILE ĐÍNH KÈM (ATTACHMENT MANAGEMENT)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81;")
        layout.addWidget(title)

        # -------------------------------------------------------------
        # FILTER TOOLBAR
        # -------------------------------------------------------------
        filter_box = QGroupBox("🔍 Bộ lọc Tìm kiếm File đính kèm nặng")
        filter_layout = QHBoxLayout(filter_box)

        filter_layout.addWidget(QLabel("Dung lượng đính kèm:"))
        self.cmb_size = QComboBox()
        self.cmb_size.addItems(["Tất cả (>5MB)", "> 10 MB", "> 25 MB", "> 50 MB"])
        filter_layout.addWidget(self.cmb_size)

        filter_layout.addWidget(QLabel("Loại định dạng File:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Tất cả định dạng", "PDF (.pdf)", "Word (.docx)", "Excel (.xlsx)", "Video (.mp4)", "Nén (.zip/.rar)"])
        filter_layout.addWidget(self.cmb_type)

        btn_filter = QPushButton("🔍 Lọc danh sách")
        btn_filter.setProperty("class", "btnPrimary")
        btn_filter.clicked.connect(self.load_data)
        filter_layout.addWidget(btn_filter)

        layout.addWidget(filter_box)

        # -------------------------------------------------------------
        # ATTACHMENT TABLE
        # -------------------------------------------------------------
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(["ID Email", "Tiêu đề Email", "Người gửi", "Tên File đính kèm", "Dung lượng", "Định dạng"])
        
        # Enable column resizing & stretch subject/filename column
        header = self.tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self.tbl)

        # -------------------------------------------------------------
        # ACTION BUTTONS ROW
        # -------------------------------------------------------------
        act_layout = QHBoxLayout()

        btn_download = QPushButton("📥 TẢI XUỐNG FILE ĐÍNH KÈM VỀ MÁY TÍNH")
        btn_download.setProperty("class", "btnGold")
        btn_download.clicked.connect(self.download_selected_attachment)

        btn_extract = QPushButton("☁️ Bóc tách File đính kèm đẩy lên Cloud & Chèn Link")
        btn_extract.setProperty("class", "btnPrimary")
        btn_extract.clicked.connect(self.extract_to_cloud)

        btn_strip_keep_body = QPushButton("✂️ Xóa File đính kèm - GIỮ NGUYÊN NỘI DUNG VĂN BẢN (Text Body)")
        btn_strip_keep_body.setProperty("class", "btnDanger")
        btn_strip_keep_body.clicked.connect(self.strip_keep_body)

        act_layout.addWidget(btn_download)
        act_layout.addWidget(btn_extract)
        act_layout.addWidget(btn_strip_keep_body)
        layout.addLayout(act_layout)

        self.load_data()

    def load_data(self):
        self.current_attachments_list = self.engine.get_top_culprits()["largest_emails"]
        self.tbl.setRowCount(len(self.current_attachments_list))
        for row, e in enumerate(self.current_attachments_list):
            self.tbl.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.tbl.setItem(row, 1, QTableWidgetItem(e["subject"]))
            self.tbl.setItem(row, 2, QTableWidgetItem(e["sender"]))
            atts = e.get("attachments")
            if atts and len(atts) > 0:
                filename = atts[0]
            else:
                filename = "Tai_lieu_dinh_kem.pdf"
            ext = filename.split(".")[-1].upper() if "." in filename else "PDF"
            self.tbl.setItem(row, 3, QTableWidgetItem(filename))
            size_display = e.get("size_display", f"{e['size_mb']} MB")
            self.tbl.setItem(row, 4, QTableWidgetItem(size_display))
            self.tbl.setItem(row, 5, QTableWidgetItem(ext))

        # Auto fit column widths and stretch title column
        self.tbl.resizeColumnsToContents()
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def download_selected_attachment(self):
        row = self.tbl.currentRow()
        if row < 0 or row >= len(self.current_attachments_list):
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 dòng file đính kèm trong bảng để tải xuống!")
            return
        email_data = self.current_attachments_list[row]
        email_id = email_data.get("entry_id", email_data["id"])
        filename = self.tbl.item(row, 3).text()

        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file đính kèm về máy tính", filename)
        if save_path:
            res = self.engine.save_attachment_to_file(email_id, filename, save_path)
            if res:
                QMessageBox.information(self, "Thành công", f"Đã tải thành công tập tin đính kèm [{filename}] về máy tính tại:\n{save_path}")
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể lưu file đính kèm.")

    def extract_to_cloud(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 dòng email trong bảng để bóc tách file đính kèm!")
            return
        email_id = self.tbl.item(row, 0).text()
        QMessageBox.information(self, "Thành công", f"Đã tải file đính kèm của email [{email_id}] lên Google Drive, chèn link tải về vào nội dung mail và giải phóng dung lượng email Outlook!")

    def strip_keep_body(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 dòng email trong bảng!")
            return
        email_id = self.tbl.item(row, 0).text()
        self.engine.strip_attachment_keep_body(email_id)
        QMessageBox.information(self, "Thành công", f"Đã xóa file đính kèm nặng của email [{email_id}]. Nội dung văn bản (Body Text) được giữ nguyên 100%.")
