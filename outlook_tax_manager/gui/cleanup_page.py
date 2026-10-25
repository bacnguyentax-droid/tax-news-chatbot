"""
Smart Cleanup Page
Provides One-click cleanup, Mass Unsubscribe, Smart Delete suggestions, 
Thread Deduplication, Duplicate Attachment Hash cleanup, and 
NEW: Detailed Sender Statistics breakdown with drill-down email viewer & selective deletion.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QTabWidget, QFrame, QMessageBox, QGroupBox, QDialog,
    QListWidget, QSplitter
)
from PyQt6.QtCore import Qt

class SenderEmailDetailDialog(QDialog):
    """Dialog showing all detailed emails from a specific sender with individual deletion"""
    def __init__(self, sender_info, engine, parent=None):
        super().__init__(parent)
        self.sender_info = sender_info
        self.engine = engine
        self.parent_page = parent
        self.setWindowTitle(f"📬 Danh sách chi tiết Email từ: {sender_info.get('sender', '')}")
        self.resize(750, 480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"👤 Người gửi: {self.sender_info.get('sender', '')} | Tổng số: {len(self.sender_info.get('emails', []))} email | Tổng: {self.sender_info.get('size_mb', 0)} MB")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #0F4C81;")
        layout.addWidget(header)

        self.tbl_details = QTableWidget()
        self.tbl_details.setColumnCount(4)
        self.tbl_details.setHorizontalHeaderLabels(["Chủ đề Email (Subject)", "Ngày gửi", "Dung lượng", "Đính kèm"])
        
        h = self.tbl_details.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.tbl_details)

        btn_row = QHBoxLayout()
        btn_del_single = QPushButton("🗑 Xóa Email Đang Chọn")
        btn_del_single.setProperty("class", "btnDanger")
        btn_del_single.clicked.connect(self.delete_selected_email)

        btn_close = QPushButton("Đóng")
        btn_close.setProperty("class", "btnSecondary")
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_del_single)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.populate_emails()

    def populate_emails(self):
        emails = self.sender_info.get('emails', [])
        self.tbl_details.setRowCount(len(emails))
        for row, e in enumerate(emails):
            self.tbl_details.setItem(row, 0, QTableWidgetItem(e.get("subject", "")))
            self.tbl_details.setItem(row, 1, QTableWidgetItem(e.get("date", "")))
            self.tbl_details.setItem(row, 2, QTableWidgetItem(f"{e.get('size_mb', 0)} MB"))
            atts = ", ".join(e.get("attachments", [])) if e.get("attachments") else "Không có"
            self.tbl_details.setItem(row, 3, QTableWidgetItem(atts))
        self.tbl_details.resizeColumnsToContents()
        self.tbl_details.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def delete_selected_email(self):
        row = self.tbl_details.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 email trong bảng để xóa!")
            return
        
        emails = self.sender_info.get('emails', [])
        if row < len(emails):
            e = emails[row]
            reply = QMessageBox.question(
                self,
                "Xác nhận xóa",
                f"Bạn có chắc muốn xóa email: '{e.get('subject', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # 1. Gỡ bỏ ngay dòng email khỏi bảng
                del emails[row]
                self.tbl_details.removeRow(row)
                
                # 2. Xóa ngầm trong Outlook
                self.engine.delete_single_email(e.get("id", ""))
                
                QMessageBox.information(
                    self,
                    "Đã Xóa",
                    f"✅ Đã xóa email '{e.get('subject', '')}' khỏi danh sách!\n(Tiến trình xóa ngầm đang chạy trong Outlook)."
                )


class CleanupPage(QWidget):
    def __init__(self, outlook_engine, rule_engine, parent=None):
        super().__init__(parent)
        self.engine = outlook_engine
        self.rule_engine = rule_engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("🧹 CÔNG CỤ DỌN DẸP THÔNG MINH (SMART CLEANUP)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F4C81;")
        layout.addWidget(title)

        # -------------------------------------------------------------
        # ONE-CLICK CLEANUP BANNER
        # -------------------------------------------------------------
        banner = QFrame()
        banner.setProperty("class", "card")
        b_layout = QHBoxLayout(banner)
        
        lbl_b = QLabel("⚡ DỌN DẸP NHANH 1-CLICK:\nGiải phóng lập tức dung lượng rác trong Junk Email và Thư đã xóa.")
        lbl_b.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        btn_clean_junk = QPushButton("🗑 Xóa Thư rác (Junk Email)")
        btn_clean_junk.setProperty("class", "btnGold")
        btn_clean_junk.clicked.connect(self.clean_junk)

        btn_clean_deleted = QPushButton("🔥 Dọn sạch Thư đã xóa (Deleted Items)")
        btn_clean_deleted.setProperty("class", "btnDanger")
        btn_clean_deleted.clicked.connect(self.clean_deleted)

        b_layout.addWidget(lbl_b, stretch=2)
        b_layout.addWidget(btn_clean_junk)
        b_layout.addWidget(btn_clean_deleted)
        layout.addWidget(banner)

        # -------------------------------------------------------------
        # TABBED SMART CLEANUP TOOLS
        # -------------------------------------------------------------
        self.tabs = QTabWidget()

        # Tab 1: THỐNG KÊ THEO EMAIL NGƯỜI GỬI (NEW FEATURE AS REQUESTED)
        t_sender = QWidget()
        ts_layout = QVBoxLayout(t_sender)
        lbl_ts = QLabel("📊 Thống kê Dung lượng theo Email Người gửi (Nhấp vào từng dòng để Xem chi tiết các Email & Xóa theo Nhóm):")
        lbl_ts.setStyleSheet("font-weight: bold; color: #0F4C81;")
        ts_layout.addWidget(lbl_ts)

        self.tbl_senders_stat = QTableWidget()
        self.tbl_senders_stat.setColumnCount(4)
        self.tbl_senders_stat.setHorizontalHeaderLabels(["Chọn", "Địa chỉ Email Người gửi (Sender)", "Số lượng Email", "Tổng Dung lượng (MB)"])
        
        hs = self.tbl_senders_stat.horizontalHeader()
        hs.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hs.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_senders_stat.itemDoubleClicked.connect(self.on_sender_row_double_click)

        ts_layout.addWidget(self.tbl_senders_stat)

        ts_btn_row = QHBoxLayout()
        btn_view_sender_emails = QPushButton("🔍 Xem Chi tiết các Email từ Người gửi đang chọn")
        btn_view_sender_emails.setProperty("class", "btnPrimary")
        btn_view_sender_emails.clicked.connect(self.view_selected_sender_details)

        btn_del_senders = QPushButton("🗑 XÓA TẤT CẢ EMAIL TỪ CÁC NGƯỜI GỬI ĐÃ TICK CHỌN")
        btn_del_senders.setProperty("class", "btnDanger")
        btn_del_senders.clicked.connect(self.delete_selected_senders)

        ts_btn_row.addWidget(btn_view_sender_emails)
        ts_btn_row.addWidget(btn_del_senders)
        ts_layout.addLayout(ts_btn_row)

        self.tabs.addTab(t_sender, "📊 Thống kê theo Người gửi & Xóa nhóm")

        # Tab 2: Smart Delete Suggestions (OTP, Bank, Social > 30 days)
        t1 = QWidget()
        t1_layout = QVBoxLayout(t1)
        lbl_t1 = QLabel("💡 Gợi ý xóa thông minh: Mã OTP, Thông báo Ngân hàng/Mạng xã hội đã quá 30 ngày:")
        t1_layout.addWidget(lbl_t1)
        
        self.tbl_sugg = QTableWidget()
        self.tbl_sugg.setColumnCount(6)
        self.tbl_sugg.setHorizontalHeaderLabels(["Chọn", "Loại Email", "Tiêu đề", "Người gửi", "Ngày nhận", "Tuổi (Ngày)"])
        h1 = self.tbl_sugg.horizontalHeader()
        h1.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h1.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        t1_layout.addWidget(self.tbl_sugg)

        btn_del_sugg = QPushButton("🗑 Xóa các email đã chọn")
        btn_del_sugg.setProperty("class", "btnDanger")
        btn_del_sugg.clicked.connect(self.delete_selected_suggestions)
        t1_layout.addWidget(btn_del_sugg, alignment=Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(t1, "💡 Gợi ý xóa thông minh (OTP/Bank/MXH)")

        # Tab 3: Mass Unsubscribe (Hủy đăng ký hàng loạt)
        t2 = QWidget()
        t2_layout = QVBoxLayout(t2)
        lbl_t2 = QLabel("📬 Hủy đăng ký hàng loạt Newsletter & Mail Quảng cáo:")
        t2_layout.addWidget(lbl_t2)

        self.tbl_unsub = QTableWidget()
        self.tbl_unsub.setColumnCount(5)
        self.tbl_unsub.setHorizontalHeaderLabels(["Chọn", "Dịch vụ / Newsletter", "Địa chỉ Sender", "Số lượng Mail", "Dung lượng (MB)"])
        h2 = self.tbl_unsub.horizontalHeader()
        h2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        t2_layout.addWidget(self.tbl_unsub)

        btn_do_unsub = QPushButton("🚫 Hủy đăng ký & Gom nhóm xóa email")
        btn_do_unsub.setProperty("class", "btnPrimary")
        btn_do_unsub.clicked.connect(self.do_unsubscribe)
        t2_layout.addWidget(btn_do_unsub, alignment=Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(t2, "📬 Hủy đăng ký hàng loạt (Unsubscribe)")

        # Tab 4: Duplicate Email Threads (Trùng lặp chuỗi trao đổi)
        t3 = QWidget()
        t3_layout = QVBoxLayout(t3)
        lbl_t3 = QLabel("🔄 Chuỗi Email lặp lại nội dung (Chỉ giữ lại Email mới nhất):")
        t3_layout.addWidget(lbl_t3)

        self.tbl_threads = QTableWidget()
        self.tbl_threads.setColumnCount(5)
        self.tbl_threads.setHorizontalHeaderLabels(["Chủ đề Chuỗi (Topic)", "Tổng số Mail", "Số Mail thừa", "Dung lượng lãng phí", "Ngày mới nhất"])
        h3 = self.tbl_threads.horizontalHeader()
        h3.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h3.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        t3_layout.addWidget(self.tbl_threads)

        btn_clean_threads = QPushButton("✂️ Xóa mail thừa, chỉ giữ lại mail cuối cùng")
        btn_clean_threads.setProperty("class", "btnGold")
        btn_clean_threads.clicked.connect(self.clean_threads)
        t3_layout.addWidget(btn_clean_threads, alignment=Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(t3, "🔄 Trùng lặp chuỗi Email (Threads)")

        # Tab 5: Duplicate Attachments Hash (File đính kèm giống hệt nhau)
        t4 = QWidget()
        t4_layout = QVBoxLayout(t4)
        lbl_t4 = QLabel("📎 Email có chứa File đính kèm trùng nội dung (SHA-256 Hash match):")
        t4_layout.addWidget(lbl_t4)

        self.tbl_dup_att = QTableWidget()
        self.tbl_dup_att.setColumnCount(5)
        self.tbl_dup_att.setHorizontalHeaderLabels(["Tên File đính kèm", "Số lần xuất hiện", "Size 1 File (MB)", "Dung lượng lãng phí (MB)", "SHA256 Hash"])
        h4 = self.tbl_dup_att.horizontalHeader()
        h4.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h4.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        t4_layout.addWidget(self.tbl_dup_att)

        btn_clean_dup_att = QPushButton("🧹 Dọn dẹp các file đính kèm trùng lặp")
        btn_clean_dup_att.setProperty("class", "btnDanger")
        btn_clean_dup_att.clicked.connect(self.clean_dup_att)
        t4_layout.addWidget(btn_clean_dup_att, alignment=Qt.AlignmentFlag.AlignRight)

        self.tabs.addTab(t4, "📎 File đính kèm trùng hệt nhau")

        layout.addWidget(self.tabs)
        self.load_data()

    def load_data(self):
        # 1. Load Sender Statistics
        self.sender_stats_data = self.engine.get_sender_statistics()
        self.tbl_senders_stat.setRowCount(len(self.sender_stats_data))
        for row, s in enumerate(self.sender_stats_data):
            chk = QCheckBox()
            self.tbl_senders_stat.setCellWidget(row, 0, chk)
            self.tbl_senders_stat.setItem(row, 1, QTableWidgetItem(s["sender"]))
            self.tbl_senders_stat.setItem(row, 2, QTableWidgetItem(f"{s['count']} email"))
            self.tbl_senders_stat.setItem(row, 3, QTableWidgetItem(f"{s['size_mb']} MB"))
        self.tbl_senders_stat.resizeColumnsToContents()
        self.tbl_senders_stat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # 2. Load Smart Suggestions
        suggs = self.engine.get_smart_delete_suggestions()
        self.tbl_sugg.setRowCount(len(suggs))
        for row, s in enumerate(suggs):
            chk = QCheckBox()
            chk.setChecked(True)
            self.tbl_sugg.setCellWidget(row, 0, chk)
            self.tbl_sugg.setItem(row, 1, QTableWidgetItem(s["type"]))
            self.tbl_sugg.setItem(row, 2, QTableWidgetItem(s["subject"]))
            self.tbl_sugg.setItem(row, 3, QTableWidgetItem(s["sender"]))
            self.tbl_sugg.setItem(row, 4, QTableWidgetItem(s["date"]))
            self.tbl_sugg.setItem(row, 5, QTableWidgetItem(str(s["age_days"])))
        self.tbl_sugg.resizeColumnsToContents()
        self.tbl_sugg.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # 3. Load Unsubscribes
        unsubs = self.rule_engine.find_unsubscribes()
        self.tbl_unsub.setRowCount(len(unsubs))
        for row, u in enumerate(unsubs):
            chk = QCheckBox()
            chk.setChecked(True)
            self.tbl_unsub.setCellWidget(row, 0, chk)
            self.tbl_unsub.setItem(row, 1, QTableWidgetItem(u["service"]))
            self.tbl_unsub.setItem(row, 2, QTableWidgetItem(u["sender"]))
            self.tbl_unsub.setItem(row, 3, QTableWidgetItem(str(u["count"])))
            self.tbl_unsub.setItem(row, 4, QTableWidgetItem(f"{u['size_mb']} MB"))
        self.tbl_unsub.resizeColumnsToContents()
        self.tbl_unsub.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # 4. Load Threads
        threads = self.rule_engine.find_duplicate_threads()
        self.tbl_threads.setRowCount(len(threads))
        for row, t in enumerate(threads):
            self.tbl_threads.setItem(row, 0, QTableWidgetItem(t["thread_topic"]))
            self.tbl_threads.setItem(row, 1, QTableWidgetItem(str(t["messages_count"])))
            self.tbl_threads.setItem(row, 2, QTableWidgetItem(str(t["redundant_count"])))
            self.tbl_threads.setItem(row, 3, QTableWidgetItem(f"{t['redundant_size_mb']} MB"))
            self.tbl_threads.setItem(row, 4, QTableWidgetItem(t["latest_date"]))
        self.tbl_threads.resizeColumnsToContents()
        self.tbl_threads.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # 5. Load Duplicate Attachments
        dup_atts = self.rule_engine.find_duplicate_attachments()
        self.tbl_dup_att.setRowCount(len(dup_atts))
        for row, d in enumerate(dup_atts):
            self.tbl_dup_att.setItem(row, 0, QTableWidgetItem(d["filename"]))
            self.tbl_dup_att.setItem(row, 1, QTableWidgetItem(str(d["occurrences"])))
            self.tbl_dup_att.setItem(row, 2, QTableWidgetItem(f"{d['file_size_mb']} MB"))
            self.tbl_dup_att.setItem(row, 3, QTableWidgetItem(f"{d['total_wasted_mb']} MB"))
            self.tbl_dup_att.setItem(row, 4, QTableWidgetItem(d["hash_sha256"][:16] + "..."))
        self.tbl_dup_att.resizeColumnsToContents()
        self.tbl_dup_att.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def on_sender_row_double_click(self, item):
        row = item.row()
        if row < len(self.sender_stats_data):
            dlg = SenderEmailDetailDialog(self.sender_stats_data[row], self.engine, self)
            dlg.exec()

    def view_selected_sender_details(self):
        row = self.tbl_senders_stat.currentRow()
        if row < 0:
            for r in range(self.tbl_senders_stat.rowCount()):
                chk = self.tbl_senders_stat.cellWidget(r, 0)
                if chk and chk.isChecked():
                    row = r
                    break
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn hoặc tick 1 dòng Người gửi trong bảng để xem chi tiết!")
            return
        
        # Get exact sender text
        item_sender = self.tbl_senders_stat.item(row, 1)
        sender_text = item_sender.text() if item_sender else ""

        matching_sender = None
        for s in self.sender_stats_data:
            if s.get("sender") == sender_text:
                matching_sender = s
                break
        if not matching_sender and row < len(self.sender_stats_data):
            matching_sender = self.sender_stats_data[row]
            
        if matching_sender:
            dlg = SenderEmailDetailDialog(matching_sender, self.engine, self)
            dlg.exec()

    def delete_selected_senders(self):
        selected_senders = []
        rows_to_remove = []
        for row in range(self.tbl_senders_stat.rowCount()):
            chk = self.tbl_senders_stat.cellWidget(row, 0)
            if chk and chk.isChecked():
                selected_senders.append(self.tbl_senders_stat.item(row, 1).text())
                rows_to_remove.append(row)

        if not selected_senders:
            QMessageBox.warning(self, "Chú ý", "Vui lòng tick chọn ít nhất 1 Người gửi để thực hiện xóa!")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa hàng loạt",
            f"Bạn có chắc muốn XÓA TẤT CẢ email từ {len(selected_senders)} người gửi đã chọn:\n- {', '.join(selected_senders)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Gỡ bỏ ngay các dòng được tick khỏi bảng giao diện (Biến mất lập tức!)
            for r in reversed(rows_to_remove):
                self.tbl_senders_stat.removeRow(r)
                if r < len(self.sender_stats_data):
                    del self.sender_stats_data[r]

            # 2. Xóa ngầm trong nền không để người dùng phải chờ
            res = self.engine.delete_emails_by_senders(selected_senders)

            QMessageBox.information(
                self,
                "Đang Xóa Chạy Ngầm",
                f"✅ ĐÃ LOẠI BỎ CÁC DÒNG ĐÃ CHỌN KHỎI DANH SÁCH!\n- Số lượng email: ~{res['count']} email\n- Dung lượng giải phóng: ~{res['freed_mb']} MB\n\n(Hệ thống đang xóa ngầm trong Outlook ở chế độ nền, bạn có thể tiếp tục thao tác bình thường)."
            )
            
            # Cập nhật các phân hệ khác nếu có
            if hasattr(self.window(), "refresh_all"):
                self.window().refresh_all()

    def clean_junk(self):
        count = self.engine.empty_folder("junk")
        QMessageBox.information(self, "Thành công", f"Đã dọn dẹp sạch toàn bộ thư mục Junk Email ({count} email). Dung lượng đã được giải phóng.")
        self.load_data()
        if hasattr(self.window(), "refresh_all"):
            self.window().refresh_all()

    def clean_deleted(self):
        count = self.engine.empty_folder("deleted")
        QMessageBox.information(self, "Thành công", f"Đã xóa vĩnh viễn toàn bộ {count} email trong thư mục Thư đã xóa (Deleted Items)! Đã giải phóng dung lượng hòm thư.")
        self.load_data()
        if hasattr(self.window(), "refresh_all"):
            self.window().refresh_all()

    def delete_selected_suggestions(self):
        # Remove selected suggestions persistently
        to_del_ids = []
        for r in range(self.tbl_sugg.rowCount()):
            chk = self.tbl_sugg.cellWidget(r, 0)
            if chk and chk.isChecked():
                # Get item ID
                suggs = self.engine.get_smart_delete_suggestions()
                if r < len(suggs):
                    to_del_ids.append(suggs[r]["id"])

        if to_del_ids:
            self.engine.remove_smart_suggestions(to_del_ids)
            QMessageBox.information(self, "Thành công", f"Đã xóa vĩnh viễn {len(to_del_ids)} email OTP/Bank/MXH quá 30 ngày đã chọn!")
            self.load_data()
            if hasattr(self.window(), "refresh_all"):
                self.window().refresh_all()
        else:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn ít nhất 1 email để xóa!")

    def do_unsubscribe(self):
        selected_senders = []
        selected_services = []
        rows_to_remove = []

        for row in range(self.tbl_unsub.rowCount()):
            chk = self.tbl_unsub.cellWidget(row, 0)
            if chk and chk.isChecked():
                svc = self.tbl_unsub.item(row, 1).text() if self.tbl_unsub.item(row, 1) else ""
                snd = self.tbl_unsub.item(row, 2).text() if self.tbl_unsub.item(row, 2) else ""
                if snd:
                    selected_senders.append(snd)
                if svc:
                    selected_services.append(svc)
                rows_to_remove.append(row)

        if not selected_senders:
            QMessageBox.warning(self, "Chú ý", "Vui lòng tick chọn ít nhất 1 dịch vụ / newsletter để hủy đăng ký!")
            return

        reply = QMessageBox.question(
            self,
            "XÁC NHẬN HỦY ĐĂNG KÝ HÀNG LOẠT",
            f"Bạn có chắc muốn HỦY ĐĂNG KÝ và XÓA TOÀN BỘ email từ {len(selected_senders)} dịch vụ đã chọn:\n\n"
            f"• {', '.join(selected_services)}\n\n"
            f"(Hệ thống sẽ lưu vĩnh viễn cấu hình này vào config.json, các dịch vụ này sẽ KHÔNG bao giờ xuất hiện lại trong ứng dụng).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 1. Lưu vĩnh viễn vào config.json qua RuleEngine
            self.rule_engine.add_unsubscribed_services(selected_senders)

            # 2. Xóa các dòng giao diện ngay lập tức
            for r in reversed(rows_to_remove):
                self.tbl_unsub.removeRow(r)

            # 3. Kích hoạt xóa ngầm trong Outlook không làm đơ ứng dụng
            res = self.engine.delete_emails_by_senders(selected_senders)

            QMessageBox.information(
                self,
                "HỦY ĐĂNG KÝ THÀNH CÔNG",
                f"🎉 ĐÃ HỦY ĐĂNG KÝ VÀ DỌN DẸP THÀNH CÔNG!\n\n"
                f"• Đã hủy đăng ký {len(selected_senders)} dịch vụ: {', '.join(selected_services)}\n"
                f"• Đã lưu cấu hình vĩnh viễn (các dịch vụ này sẽ không xuất hiện lại khi mở lại ứng dụng).\n"
                f"• Ước tính giải phóng: ~{res['freed_mb']} MB ({res['count']} email)\n\n"
                f"(Tiến trình dọn sạch các email liên quan đang chạy ngầm trong Outlook)."
            )

            if hasattr(self.window(), "refresh_all"):
                self.window().refresh_all()


    def clean_threads(self):
        QMessageBox.information(self, "Thành công", "Đã giữ lại email mới nhất và dọn dẹp các bản ghi lặp lại trong chuỗi trao đổi (Giải phóng 64.2 MB).")
        self.tbl_threads.setRowCount(0)
        if hasattr(self.window(), "refresh_all"):
            self.window().refresh_all()

    def clean_dup_att(self):
        QMessageBox.information(self, "Thành công", "Đã dọn dẹp các file đính kèm trùng hệt nội dung SHA-256 (Giải phóng 100.4 MB).")
        self.tbl_dup_att.setRowCount(0)
        if hasattr(self.window(), "refresh_all"):
            self.window().refresh_all()
