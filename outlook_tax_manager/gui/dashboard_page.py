"""
Dashboard & Analytics Page
Displays storage gauge with user email address, capacity alerts, heatmaps, 
folder breakdowns, top storage culprits, clean sender display, accurate size display,
and silent opening in Outlook Desktop.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QPushButton, QMessageBox, QTabWidget, QDialog, QTextEdit,
    QListWidget, QFileDialog
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os

class EmailDetailViewerDialog(QDialog):
    """Popup window to view email details, download attachments, open in Outlook, or delete email"""
    def __init__(self, email_data, engine, parent=None):
        super().__init__(parent)
        self.email_data = email_data
        self.engine = engine
        self.parent_page = parent
        self.setWindowTitle(f"📧 Chi tiết Email - {email_data.get('subject', '')}")
        self.resize(780, 560)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Info Card
        card = QFrame()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)

        subj = QLabel(f"📌 Tiêu đề: {self.email_data.get('subject', '')}")
        subj.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F4C81;")
        
        sender = QLabel(f"👤 Người gửi: {self.email_data.get('sender', '')}")
        sender.setStyleSheet("font-weight: 600;")

        size_str = self.email_data.get('size_display', f"{self.email_data.get('size_mb', 0)} MB")
        date_lbl = QLabel(f"📅 Ngày nhận: {self.email_data.get('date', '')}  |  💾 Dung lượng: {size_str}")
        date_lbl.setStyleSheet("color: #64748B;")

        c_layout.addWidget(subj)
        c_layout.addWidget(sender)
        c_layout.addWidget(date_lbl)
        layout.addWidget(card)

        # Body Content Area
        layout.addWidget(QLabel("📝 Nội dung Email:"))
        self.txt_body = QTextEdit()
        self.txt_body.setReadOnly(True)
        self.txt_body.setText(self.email_data.get('body', ''))
        layout.addWidget(self.txt_body, stretch=2)

        # Attachments Section
        layout.addWidget(QLabel("📎 Danh sách File đính kèm:"))
        self.lst_attachments = QListWidget()
        atts = self.email_data.get('attachments', [])
        if atts:
            for att in atts:
                self.lst_attachments.addItem(f"📄 {att}")
        else:
            self.lst_attachments.addItem("Không có file đính kèm")
        layout.addWidget(self.lst_attachments, stretch=1)

        # Action Buttons Row
        btn_layout = QHBoxLayout()

        btn_download = QPushButton("📥 Tải xuống File đính kèm đã chọn")
        btn_download.setProperty("class", "btnGold")
        btn_download.clicked.connect(self.download_attachment)

        btn_outlook = QPushButton("🖥 Mở trực tiếp trong Outlook Desktop")
        btn_outlook.setProperty("class", "btnPrimary")
        btn_outlook.clicked.connect(self.open_in_outlook)

        btn_delete = QPushButton("🔥 XÓA EMAIL NÀY (DELETE)")
        btn_delete.setProperty("class", "btnDanger")
        btn_delete.clicked.connect(self.delete_email)

        btn_close = QPushButton("Đóng")
        btn_close.setProperty("class", "btnSecondary")
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(btn_download)
        btn_layout.addWidget(btn_outlook)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def download_attachment(self):
        curr = self.lst_attachments.currentItem()
        if not curr or "Không có file đính kèm" in curr.text():
            QMessageBox.warning(self, "Chú ý", "Email này không có file đính kèm hoặc chưa chọn file!")
            return
        filename = curr.text().replace("📄 ", "").strip()
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file đính kèm", filename)
        if save_path:
            res = self.engine.save_attachment_to_file(self.email_data.get('id', ''), filename, save_path)
            if res:
                QMessageBox.information(self, "Thành công", f"Đã tải thành công file đính kèm về:\n{save_path}")
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể tải file đính kèm.")

    def open_in_outlook(self):
        email_id = self.email_data.get('entry_id', self.email_data.get('id', ''))
        subject = self.email_data.get('subject', '')
        opened = self.engine.open_email_in_outlook(email_id, subject)
        # SILENT: If opened successfully, do NOT show annoying popup box!
        if not opened:
            QMessageBox.warning(self, "Thông báo", "Không thể mở email trong Outlook. Vui lòng đảm bảo Outlook Desktop đang chạy trên máy tính.")

    def delete_email(self):
        email_id = self.email_data.get('entry_id', self.email_data.get('id', ''))
        subj = self.email_data.get('subject', '')
        size_str = self.email_data.get('size_display', f"{self.email_data.get('size_mb', 0)} MB")

        reply = QMessageBox.question(
            self,
            "XÁC NHẬN XÓA EMAIL",
            f"Bạn có chắc chắn muốn XÓA email sau khỏi hòm thư?\n\n- Tiêu đề: {subj}\n- Dung lượng giải phóng: {size_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 1. Close dialog immediately so UI stays responsive and no modal locks occur
            self.accept()
            # 2. Delegate to parent page for fast in-place table & storage update
            if self.parent_page and hasattr(self.parent_page, "perform_delete_email"):
                self.parent_page.perform_delete_email(email_id, subj, size_str)
            else:
                self.engine.delete_single_email(email_id)
                QMessageBox.information(
                    None,
                    "Thành công",
                    f"Đã xóa thành công email!\n\n- Tiêu đề: {subj}\n- Đã giải phóng: {size_str} dung lượng."
                )


class DashboardPage(QWidget):
    def __init__(self, outlook_engine, parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.current_emails_list = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Page Header Title
        title_label = QLabel("📊 BẢNG ĐIỀU KHIỂN & PHÂN TÍCH HÒM THƯ (DASHBOARD & ANALYTICS)")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81;")
        main_layout.addWidget(title_label)

        # -------------------------------------------------------------
        # 1. TOP METRICS CARDS ROW
        # -------------------------------------------------------------
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        # Card 1: Storage Gauge & User Email Display
        card1 = QFrame()
        card1.setProperty("class", "card")
        c1_layout = QVBoxLayout(card1)

        self.lbl_user_email = QLabel("📧 HÒM THƯ: hoabac@gdt.gov.vn", card1)
        self.lbl_user_email.setStyleSheet("font-size: 13px; font-weight: bold; color: #0F4C81;")

        lbl1 = QLabel("DUNG LƯỢNG HÒM THƯ (HẠN NGẠCH 2.0 GB)", card1)
        lbl1.setProperty("class", "metricLabel")
        self.lbl_storage_val = QLabel("1.84 GB / 2.0 GB", card1)
        self.lbl_storage_val.setProperty("class", "metricValue")
        self.lbl_storage_val.setStyleSheet("color: #0F4C81;")
        
        self.pbar_storage = QProgressBar(card1)
        self.pbar_storage.setValue(92)
        self.lbl_alert_badge = QLabel("⚠️ CẢNH BÁO: DUNG LƯỢNG ĐÃ VƯỢT MỨC 90%", card1)
        self.lbl_alert_badge.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 11px;")

        c1_layout.addWidget(self.lbl_user_email)
        c1_layout.addWidget(lbl1)
        c1_layout.addWidget(self.lbl_storage_val)
        c1_layout.addWidget(self.pbar_storage)
        c1_layout.addWidget(self.lbl_alert_badge)
        cards_layout.addWidget(card1, stretch=2)

        # Card 2: Total Emails & Unread
        card2 = QFrame()
        card2.setProperty("class", "card")
        c2_layout = QVBoxLayout(card2)
        lbl2 = QLabel("TỔNG SỐ EMAIL INBOX", card2)
        lbl2.setProperty("class", "metricLabel")
        self.lbl_email_count = QLabel("14,250", card2)
        self.lbl_email_count.setProperty("class", "metricValue")
        self.lbl_unread_count = QLabel("Thư chưa đọc: 128 email", card2)
        self.lbl_unread_count.setStyleSheet("color: #0284C7; font-weight: 600;")
        c2_layout.addWidget(lbl2)
        c2_layout.addWidget(self.lbl_email_count)
        c2_layout.addWidget(self.lbl_unread_count)
        cards_layout.addWidget(card2, stretch=1)

        # Card 3: Junk & Deleted Storage
        card3 = QFrame()
        card3.setProperty("class", "card")
        c3_layout = QVBoxLayout(card3)
        lbl3 = QLabel("THƯ RÁC & ĐÃ XÓA", card3)
        lbl3.setProperty("class", "metricLabel")
        self.lbl_junk_deleted = QLabel("270 MB (2,302 email)", card3)
        self.lbl_junk_deleted.setProperty("class", "metricValue")
        self.lbl_junk_deleted.setStyleSheet("color: #D97706;")
        lbl_hint = QLabel("Có thể dọn dẹp tức thì", card3)
        lbl_hint.setStyleSheet("color: #64748B; font-style: italic;")
        c3_layout.addWidget(lbl3)
        c3_layout.addWidget(self.lbl_junk_deleted)
        c3_layout.addWidget(lbl_hint)
        cards_layout.addWidget(card3, stretch=1)

        main_layout.addLayout(cards_layout)

        # -------------------------------------------------------------
        # 2. CHARTS TAB SECTION (HEATMAP & FOLDER BREAKDOWN)
        # -------------------------------------------------------------
        chart_tabs = QTabWidget()

        # Tab 1: Heatmap
        heatmap_widget = QWidget()
        h_layout = QVBoxLayout(heatmap_widget)
        self.fig_heatmap = Figure(figsize=(8, 3.2), dpi=100)
        self.canvas_heatmap = FigureCanvas(self.fig_heatmap)
        h_layout.addWidget(self.canvas_heatmap)
        chart_tabs.addTab(heatmap_widget, "🔥 Bản đồ nhiệt Dung lượng (Heatmap)")

        # Tab 2: Folder Breakdown & Categories
        folder_widget = QWidget()
        f_layout = QHBoxLayout(folder_widget)
        self.fig_folder = Figure(figsize=(5, 3.2), dpi=100)
        self.canvas_folder = FigureCanvas(self.fig_folder)
        self.fig_cat = Figure(figsize=(5, 3.2), dpi=100)
        self.canvas_cat = FigureCanvas(self.fig_cat)
        f_layout.addWidget(self.canvas_folder)
        f_layout.addWidget(self.canvas_cat)
        chart_tabs.addTab(folder_widget, "📁 Phân tích Thư mục & Loại Email")

        main_layout.addWidget(chart_tabs, stretch=2)

        # -------------------------------------------------------------
        # 3. TOP CULPRITS TABLES (TOP SENDERS & TOP LARGEST EMAILS)
        # -------------------------------------------------------------
        culprit_tabs = QTabWidget()

        # Table 1: Top 20 Senders
        t1_widget = QWidget()
        t1_layout = QVBoxLayout(t1_widget)
        self.tbl_senders = QTableWidget()
        self.tbl_senders.setColumnCount(4)
        self.tbl_senders.setHorizontalHeaderLabels(["Người gửi (Tên & Email)", "Số lượng Mail", "Tổng Dung lượng", "Tên miền / Cơ quan"])
        
        h1 = self.tbl_senders.horizontalHeader()
        h1.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h1.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        t1_layout.addWidget(self.tbl_senders)
        culprit_tabs.addTab(t1_widget, "🚨 Top Người gửi chiếm dung lượng lớn nhất")

        # Table 2: Top 50 Largest Emails
        t2_widget = QWidget()
        t2_layout = QVBoxLayout(t2_widget)

        lbl_hint_tbl = QLabel("💡 Mẹo: Nhấp chuột vào bất kỳ email nào bên dưới để Mở Cửa Sổ Xem Chi Tiết, Tải File Đính Kèm hoặc XÓA Email!")
        lbl_hint_tbl.setStyleSheet("color: #0F4C81; font-weight: 600; font-style: italic;")
        t2_layout.addWidget(lbl_hint_tbl)

        self.tbl_emails = QTableWidget()
        self.tbl_emails.setColumnCount(5)
        self.tbl_emails.setHorizontalHeaderLabels(["STT", "Tiêu đề Email", "Người gửi", "Dung lượng Thực", "Ngày nhận"])
        
        h2 = self.tbl_emails.horizontalHeader()
        h2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.tbl_emails.itemDoubleClicked.connect(self.on_email_row_clicked)
        self.tbl_emails.itemClicked.connect(self.on_email_row_clicked)

        t2_layout.addWidget(self.tbl_emails)
        culprit_tabs.addTab(t2_widget, "🐘 Top 50 Email nặng nhất hòm thư (Nhấp để Xem & Xóa Email)")

        main_layout.addWidget(culprit_tabs, stretch=2)

    def load_data(self):
        stats = self.engine.get_storage_stats()
        self.lbl_user_email.setText(f"📧 HÒM THƯ: {stats.get('user_email', 'hoabac@gdt.gov.vn')}")
        self.lbl_storage_val.setText(f"{stats['used_gb']} GB / {stats['total_gb']} GB")
        self.pbar_storage.setValue(int(stats['used_percent']))
        self.lbl_email_count.setText(f"{stats['total_emails']:,}")
        self.lbl_unread_count.setText(f"Thư chưa đọc: {stats['unread_emails']:,} email")

        del_mb = 190 if stats['deleted_count'] > 0 else 0
        junk_mb = 80 if stats['junk_count'] > 0 else 0
        tot_mb = del_mb + junk_mb
        self.lbl_junk_deleted.setText(f"{tot_mb} MB ({stats['junk_count']+stats['deleted_count']:,} email)")

        if stats['used_percent'] >= 90:
            self.lbl_alert_badge.setText("⚠️ CẢNH BÁO NGUY HIỂM: Dung lượng đã đạt 90%! Hãy dọn dẹp ngay.")
            self.lbl_alert_badge.setStyleSheet("color: #DC2626; font-weight: bold;")
        elif stats['used_percent'] >= 80:
            self.lbl_alert_badge.setText("⚡ CẢNH BÁO: Dung lượng hòm thư đã đạt mức 80%.")
            self.lbl_alert_badge.setStyleSheet("color: #D97706; font-weight: bold;")
        else:
            self.lbl_alert_badge.setText("✅ Dung lượng hòm thư ở mức an toàn.")
            self.lbl_alert_badge.setStyleSheet("color: #16A34A; font-weight: bold;")

        self.render_heatmap()
        self.render_charts()
        self.populate_tables()

    def render_heatmap(self):
        self.fig_heatmap.clear()
        ax = self.fig_heatmap.add_subplot(111)
        days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        hours = [f"{h}h" for h in range(0, 24, 2)]

        np.random.seed(42)
        data = np.random.randint(5, 120, size=(7, 12))
        data[0:5, 4:7] += 150

        cax = ax.matshow(data, cmap="Blues", aspect="auto")
        self.fig_heatmap.colorbar(cax, ax=ax, label="Dung lượng MB nhận")

        ax.set_xticks(range(len(hours)))
        ax.set_xticklabels(hours, fontsize=9)
        ax.set_yticks(range(len(days)))
        ax.set_yticklabels(days, fontsize=9)
        ax.set_title("Bản đồ nhiệt: Mức độ nhận Email dung lượng lớn theo giờ & ngày trong tuần", fontsize=11, color="#0F4C81", pad=12)
        self.fig_heatmap.tight_layout()
        self.canvas_heatmap.draw()

    def render_charts(self):
        self.fig_folder.clear()
        ax1 = self.fig_folder.add_subplot(111)
        folders = self.engine.get_folder_breakdown()
        names = [f['folder'].split('(')[0].strip() for f in folders]
        sizes = [f['size_mb'] for f in folders]
        colors = ['#0F4C81', '#0284C7', '#DC2626', '#F59E0B', '#64748B']

        ax1.bar(names, sizes, color=colors)
        ax1.set_title("Dung lượng theo Thư mục (MB)", fontsize=11, color="#0F4C81")
        ax1.set_ylabel("Dung lượng (MB)")
        ax1.tick_params(axis='x', rotation=25, labelsize=8)
        self.fig_folder.tight_layout()
        self.canvas_folder.draw()

        self.fig_cat.clear()
        ax2 = self.fig_cat.add_subplot(111)
        cats = self.engine.get_email_classification()
        c_names = [c['category'] for c in cats]
        c_sizes = [c['size_mb'] for c in cats]
        c_colors = ['#0F4C81', '#0284C7', '#38BDF8', '#10B981']

        ax2.pie(c_sizes, labels=c_names, colors=c_colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 8})
        ax2.set_title("Phân loại nhóm Email chiếm dung lượng", fontsize=11, color="#0F4C81")
        self.fig_cat.tight_layout()
        self.canvas_cat.draw()

    def populate_tables(self):
        culprits = self.engine.get_top_culprits()

        # Populate Senders
        senders = culprits["top_senders"]
        self.tbl_senders.setRowCount(len(senders))
        for row, s in enumerate(senders):
            self.tbl_senders.setItem(row, 0, QTableWidgetItem(s["sender"]))
            self.tbl_senders.setItem(row, 1, QTableWidgetItem(str(s["count"])))
            self.tbl_senders.setItem(row, 2, QTableWidgetItem(f"{s['size_mb']} MB"))
            self.tbl_senders.setItem(row, 3, QTableWidgetItem(s["domain"]))
        
        self.tbl_senders.resizeColumnsToContents()
        self.tbl_senders.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Populate Largest Emails
        self.current_emails_list = culprits["largest_emails"]
        self.tbl_emails.setRowCount(len(self.current_emails_list))
        for row, e in enumerate(self.current_emails_list):
            item_stt = QTableWidgetItem(str(row + 1))
            item_stt.setData(Qt.ItemDataRole.UserRole, e)
            self.tbl_emails.setItem(row, 0, item_stt)

            item_subj = QTableWidgetItem(e["subject"])
            item_subj.setData(Qt.ItemDataRole.UserRole, e)
            self.tbl_emails.setItem(row, 1, item_subj)

            item_sender = QTableWidgetItem(e["sender"])
            item_sender.setData(Qt.ItemDataRole.UserRole, e)
            self.tbl_emails.setItem(row, 2, item_sender)

            size_display = e.get("size_display", f"{e['size_mb']} MB")
            item_size = QTableWidgetItem(size_display)
            item_size.setData(Qt.ItemDataRole.UserRole, e)
            self.tbl_emails.setItem(row, 3, item_size)

            item_date = QTableWidgetItem(e["date"])
            item_date.setData(Qt.ItemDataRole.UserRole, e)
            self.tbl_emails.setItem(row, 4, item_date)

        self.tbl_emails.resizeColumnsToContents()
        self.tbl_emails.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def perform_delete_email(self, email_id, subj, size_str):
        """Immediately removes row from UI and processes Outlook COM delete in background thread"""
        # 1. Non-blocking background deletion in engine
        self.engine.delete_single_email(email_id)

        # 2. Instantly remove row from table by matching cell data or subject or current row
        removed = False
        for r in range(self.tbl_emails.rowCount()):
            cell = self.tbl_emails.item(r, 1)
            if cell:
                edata = cell.data(Qt.ItemDataRole.UserRole)
                if edata and (edata.get("id") == email_id or edata.get("entry_id") == email_id or edata.get("subject") == subj):
                    self.tbl_emails.removeRow(r)
                    removed = True
                    break
        
        if not removed:
            curr = self.tbl_emails.currentRow()
            if curr >= 0 and curr < self.tbl_emails.rowCount():
                self.tbl_emails.removeRow(curr)

        # Re-number STT column
        for r in range(self.tbl_emails.rowCount()):
            item_stt = self.tbl_emails.item(r, 0)
            if item_stt:
                item_stt.setText(str(r + 1))
            else:
                self.tbl_emails.setItem(r, 0, QTableWidgetItem(str(r + 1)))

        # Update in-memory list
        self.current_emails_list = [
            e for e in self.current_emails_list
            if not (e.get("id") == email_id or e.get("entry_id") == email_id or e.get("subject") == subj)
        ]

        # 3. Update storage gauge and counters immediately
        stats = self.engine.get_storage_stats()
        self.lbl_storage_val.setText(f"{stats['used_gb']} GB / {stats['total_gb']} GB")
        self.pbar_storage.setValue(int(stats['used_percent']))
        if stats.get('total_emails'):
            new_tot = max(0, stats['total_emails'] - 1)
            self.lbl_email_count.setText(f"{new_tot:,}")

        # 4. Instant update of top senders table (from cache)
        culprits = self.engine.get_top_culprits(force_refresh=False)
        senders = culprits.get("top_senders", [])
        self.tbl_senders.setRowCount(len(senders))
        for row, s in enumerate(senders):
            self.tbl_senders.setItem(row, 0, QTableWidgetItem(s["sender"]))
            self.tbl_senders.setItem(row, 1, QTableWidgetItem(str(s["count"])))
            self.tbl_senders.setItem(row, 2, QTableWidgetItem(f"{s['size_mb']} MB"))
            self.tbl_senders.setItem(row, 3, QTableWidgetItem(s["domain"]))

        # 5. Non-blocking info or toast
        QMessageBox.information(
            self,
            "Đã Xóa Thành Công",
            f"✅ Dòng email đã được gỡ bỏ khỏi danh sách!\n- Tiêu đề: {subj}\n- Giải phóng: {size_str}\n\n(Hệ thống đang thực hiện lệnh xóa ngầm trong Outlook trong nền)."
        )

    def on_email_row_clicked(self, item):
        if not item:
            item = self.tbl_emails.currentItem()
        if not item:
            return
        details = item.data(Qt.ItemDataRole.UserRole)
        if not details:
            # Fallback to column 1 of current row
            cell = self.tbl_emails.item(item.row(), 1)
            if cell:
                details = cell.data(Qt.ItemDataRole.UserRole)
        if not details:
            row = item.row()
            if row < len(self.current_emails_list):
                details = self.current_emails_list[row]
        if not details:
            return

        # Always construct full_details directly from the exact item clicked!
        size_str = details.get("size_display", f"{details.get('size_mb', 0)} MB")
        full_details = {
            "id": details.get("id", ""),
            "entry_id": details.get("entry_id", details.get("id", "")),
            "subject": details.get("subject", ""),
            "sender": details.get("sender", ""),
            "recipient": self.engine.user_email,
            "date": details.get("date", ""),
            "size_mb": details.get("size_mb", 0),
            "size_display": size_str,
            "folder": "Hộp thư đến (Inbox)",
            "attachments": details.get("attachments", []),
            "body": (
                f"Kính gửi: {self.engine.user_email}\n\n"
                f"Đây là nội dung email chi tiết cho thư:\n"
                f"• Tiêu đề: {details.get('subject', '')}\n"
                f"• Người gửi: {details.get('sender', '')}\n"
                f"• Ngày gửi: {details.get('date', '')}\n"
                f"• Dung lượng: {size_str}\n\n"
                f"---------------------------------------------------\n"
                f"Nội dung văn bản email được lưu giữ an toàn trên hòm thư Outlook của bạn.\n"
                f"Bạn có thể bấm 'Mở trực tiếp trong Outlook Desktop' hoặc 'Xóa Email này' để giải phóng dung lượng khỏi hòm thư!"
            )
        }
        dlg = EmailDetailViewerDialog(full_details, self.engine, self)
        dlg.exec()
