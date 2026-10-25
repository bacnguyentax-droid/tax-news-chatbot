import os
import sys
import threading
import datetime
import textwrap
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

from config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_EXCEL_PATH,
    DEFAULT_CHANNELS,
    DEFAULT_TAX_KEYWORDS,
    DEFAULT_YOUTUBE_API_KEY
)
from youtube_searcher import YouTubeSearcher
from transcript_analyzer import TranscriptAnalyzer
from downloader import VideoDownloader
from excel_logger import ExcelLogger

class AppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tax Video AI Bot - Quy Trình 2 Giai Đoạn Bóc Tách Video Thuế")
        self.root.geometry("980x850")
        self.root.minsize(850, 700)

        # Theme & Colors - Modern AI Slate / Cyber Theme
        self.bg_dark = "#0F172A"       # Slate 900
        self.card_bg = "#1E293B"       # Slate 800
        self.card_border = "#334155"   # Slate 700
        self.accent_indigo = "#6366F1" # Indigo 500
        self.accent_cyan = "#06B6D4"   # Cyan 500
        self.btn_green = "#10B981"     # Emerald 500
        self.btn_amber = "#F59E0B"     # Amber 500
        self.btn_red = "#EF4444"       # Red 500
        self.text_light = "#F8FAFC"    # Slate 50
        self.text_muted = "#94A3B8"    # Slate 400
        self.console_bg = "#090D16"    # Obsidian Deep

        self.root.configure(bg=self.bg_dark)
        try:
            self.root.deiconify()
            self.root.state('zoomed')
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(1500, lambda: self.root.attributes('-topmost', False))
            self.root.focus_force()
        except Exception:
            pass

        self.is_running = False
        self.stage1_results = [] # Danh sách lưu trữ video từ Giai đoạn 1
        self.active_edit_win = None # Quản lý cửa sổ chỉnh sửa chữ duy nhất (Singleton modal)

        self._apply_custom_styles()
        self._build_ui()

    def _apply_custom_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Frame styles
        self.style.configure('TFrame', background=self.bg_dark)
        self.style.configure('Card.TFrame', background=self.card_bg)

        # LabelFrame styles
        self.style.configure(
            'Card.TLabelframe',
            background=self.card_bg,
            foreground=self.accent_cyan,
            bordercolor=self.card_border,
            darkcolor=self.card_bg,
            lightcolor=self.card_border,
            borderwidth=1,
            relief="solid"
        )
        self.style.configure(
            'Card.TLabelframe.Label',
            background=self.card_bg,
            foreground=self.accent_cyan,
            font=("Segoe UI", 10, "bold")
        )

        # Label styles
        self.style.configure('TLabel', background=self.card_bg, foreground=self.text_light, font=("Segoe UI", 9))
        self.style.configure('Muted.TLabel', background=self.card_bg, foreground=self.text_muted, font=("Segoe UI", 8))

        # Entry styles
        self.style.configure(
            'TEntry',
            fieldbackground="#334155",
            foreground="#FFFFFF",
            insertcolor="#FFFFFF",
            bordercolor="#475569",
            lightcolor="#475569",
            darkcolor="#334155",
            borderwidth=1,
            padding=5
        )

        # Checkbutton styles
        self.style.configure(
            'TCheckbutton',
            background=self.card_bg,
            foreground=self.text_light,
            font=("Segoe UI", 9)
        )
        self.style.map(
            'TCheckbutton',
            background=[('active', self.card_bg)],
            foreground=[('active', self.accent_cyan)]
        )

        # Treeview styling
        self.style.configure(
            "Treeview",
            background="#1E293B",
            foreground="#F8FAFC",
            fieldbackground="#1E293B",
            rowheight=160,
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Treeview.Heading",
            background="#0F172A",
            foreground=self.accent_cyan,
            font=("Segoe UI", 10, "bold")
        )
        self.style.map("Treeview", background=[("selected", "#334155")], foreground=[("selected", "#38BDF8")])

        # Progressbar
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor="#1E293B",
            background=self.accent_cyan,
            thickness=6
        )

    def _build_ui(self):
        # 1. Header Bar
        header_frame = tk.Frame(self.root, bg="#1E1B4B", height=75)
        header_frame.pack(fill="x", side="top")

        header_content = tk.Frame(header_frame, bg="#1E1B4B")
        header_content.pack(fill="both", expand=True, padx=20, pady=10)

        icon_label = tk.Label(
            header_content,
            text="⚡",
            font=("Segoe UI Emoji", 22),
            fg=self.accent_cyan,
            bg="#1E1B4B"
        )
        icon_label.pack(side="left", padx=(0, 10))

        title_box = tk.Frame(header_content, bg="#1E1B4B")
        title_box.pack(side="left")

        title_label = tk.Label(
            title_box,
            text="TAX VIDEO AI BOT - XỬ LÝ VIDEO THUẾ 2 GIAI ĐOẠN",
            font=("Segoe UI", 12, "bold"),
            fg=self.text_light,
            bg="#1E1B4B"
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            title_box,
            text="Giai đoạn 1: Quét Tiêu đề/Mô tả ➔ Giai đoạn 2: Bóc tách phụ đề & Cắt video chọn lọc",
            font=("Segoe UI", 8),
            fg=self.text_muted,
            bg="#1E1B4B"
        )
        subtitle_label.pack(anchor="w")

        # Main Scrollable Container
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill="both", expand=True)

        # 2. Input Parameters Section
        input_group = ttk.LabelFrame(main_container, text=" 🔑 CẤU HÌNH & THỜI GIAN QUÉT ", style="Card.TLabelframe", padding=8)
        input_group.pack(fill="x", pady=(0, 6))

        # API Key
        ttk.Label(input_group, text="YouTube API Key:").grid(row=0, column=0, sticky="w", pady=3)
        self.api_key_var = tk.StringVar(value=DEFAULT_YOUTUBE_API_KEY)
        self.api_entry = ttk.Entry(input_group, textvariable=self.api_key_var, width=58, show="*")
        self.api_entry.grid(row=0, column=1, columnspan=2, sticky="w", pady=3, padx=5)

        self.show_key_var = tk.BooleanVar(value=False)
        show_btn = ttk.Checkbutton(input_group, text="Hiện Key", variable=self.show_key_var, command=self._toggle_api_visibility)
        show_btn.grid(row=0, column=3, sticky="w", padx=5)

        # Date Range
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        ttk.Label(input_group, text="Từ ngày (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=3)
        self.start_date_var = tk.StringVar(value=today_str)
        ttk.Entry(input_group, textvariable=self.start_date_var, width=18).grid(row=1, column=1, sticky="w", pady=3, padx=5)

        ttk.Label(input_group, text="Đến ngày (DD/MM/YYYY):").grid(row=1, column=2, sticky="w", pady=3)
        self.end_date_var = tk.StringVar(value=today_str)
        ttk.Entry(input_group, textvariable=self.end_date_var, width=18).grid(row=1, column=3, sticky="w", pady=3, padx=5)

        # Output Folder & Keywords
        ttk.Label(input_group, text="Thư mục lưu video:").grid(row=2, column=0, sticky="w", pady=3)
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        ttk.Entry(input_group, textvariable=self.output_dir_var, width=58).grid(row=2, column=1, columnspan=2, sticky="w", pady=3, padx=5)
        ttk.Button(input_group, text="📁 Chọn", command=self._browse_output_dir).grid(row=2, column=3, sticky="w", padx=5)

        # Keywords Input
        ttk.Label(input_group, text="Từ khóa tìm kiếm:").grid(row=3, column=0, sticky="w", pady=3)
        self.keywords_var = tk.StringVar(value=", ".join(DEFAULT_TAX_KEYWORDS))
        ttk.Entry(input_group, textvariable=self.keywords_var, width=76).grid(row=3, column=1, columnspan=3, sticky="w", pady=3, padx=5)

        # Channels Selection & Buffers
        config_sub = ttk.Frame(input_group, style="Card.TFrame")
        config_sub.grid(row=4, column=0, columnspan=4, sticky="ew", pady=4)

        # Row 1 of config_sub: Channel Checkboxes (7 channels)
        ch_frame = ttk.Frame(config_sub, style="Card.TFrame")
        ch_frame.pack(fill="x", side="top", pady=(0, 4))
        ttk.Label(ch_frame, text="Kênh YouTube quét:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))

        self.channel_vars = {}
        for idx, ch in enumerate(DEFAULT_CHANNELS):
            ch_name = ch["name"]
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(ch_frame, text=ch_name, variable=var)
            cb.pack(side="left", padx=4)
            self.channel_vars[ch_name] = (var, ch)

        # Row 2 of config_sub: Buffer Settings
        buf_frame = ttk.Frame(config_sub, style="Card.TFrame")
        buf_frame.pack(fill="x", side="top")

        ttk.Label(buf_frame, text="⚙ Thời gian cắt bài tin: ", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        ttk.Label(buf_frame, text="Buffer Lùi:").pack(side="left", padx=(5, 2))
        self.buf_start_var = tk.StringVar(value="25")
        ttk.Entry(buf_frame, textvariable=self.buf_start_var, width=4).pack(side="left")

        ttk.Label(buf_frame, text="giây | Tiến:").pack(side="left", padx=(5, 2))
        self.buf_end_var = tk.StringVar(value="35")
        ttk.Entry(buf_frame, textvariable=self.buf_end_var, width=4).pack(side="left")

        ttk.Label(buf_frame, text="giây | Ghép ranh giới:").pack(side="left", padx=(5, 2))
        self.max_gap_var = tk.StringVar(value="60")
        ttk.Entry(buf_frame, textvariable=self.max_gap_var, width=4).pack(side="left")
        ttk.Label(buf_frame, text="giây").pack(side="left")

        # 3. Stage 1 Section: Video Search & Selection Table
        table_group = ttk.LabelFrame(main_container, text=" 📋 GIAI ĐOẠN 1: TÌM KIẾM & CHỌN VIDEO (TIÊU ĐỀ / MÔ TẢ) ", style="Card.TLabelframe", padding=6)
        table_group.pack(fill="both", expand=True, pady=(0, 6))

        # Action bar for Stage 1 & Stage 2
        btn_bar = ttk.Frame(table_group, style="Card.TFrame")
        btn_bar.pack(fill="x", pady=(0, 6))

        self.btn_stage1 = tk.Button(
            btn_bar,
            text="🔍 GIAI ĐOẠN 1: QUÉT TÌM VIDEO",
            font=("Segoe UI", 9, "bold"),
            bg=self.accent_indigo,
            fg="#FFFFFF",
            activebackground="#4F46E5",
            activeforeground="#FFFFFF",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.start_stage1_search
        )
        self.btn_stage1.pack(side="left", padx=(0, 8))

        btn_select_all = tk.Button(
            btn_bar,
            text="☑ Chọn tất cả",
            font=("Segoe UI", 8),
            bg="#334155",
            fg="#FFFFFF",
            bd=0,
            padx=8,
            pady=6,
            command=lambda: self._set_all_selection(True)
        )
        btn_select_all.pack(side="left", padx=(0, 4))

        btn_deselect_all = tk.Button(
            btn_bar,
            text="☐ Bỏ chọn tất cả",
            font=("Segoe UI", 8),
            bg="#334155",
            fg="#FFFFFF",
            bd=0,
            padx=8,
            pady=6,
            command=lambda: self._set_all_selection(False)
        )
        btn_deselect_all.pack(side="left", padx=(0, 6))

        btn_edit_text = tk.Button(
            btn_bar,
            text="✏️ Sửa chữ 9:16 dòng chọn",
            font=("Segoe UI", 8, "bold"),
            bg=self.btn_amber,
            fg="#FFFFFF",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self._edit_selected_overlay_text
        )
        btn_edit_text.pack(side="left", padx=(0, 8))

        btn_cookies = tk.Button(
            btn_bar,
            text="🍪 Nạp Cookies (.txt)",
            font=("Segoe UI", 8, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self._browse_cookie_file
        )
        btn_cookies.pack(side="left", padx=(0, 15))

        self.btn_stage2 = tk.Button(
            btn_bar,
            text="🎬 GIAI ĐOẠN 2: XỬ LÝ VIDEO ĐÃ CHỌN",
            font=("Segoe UI", 9, "bold"),
            bg=self.btn_green,
            fg="#FFFFFF",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.start_stage2_process
        )
        self.btn_stage2.pack(side="left", padx=(0, 8))

        self.btn_stop = tk.Button(
            btn_bar,
            text="⏹ Dừng",
            font=("Segoe UI", 9, "bold"),
            bg=self.btn_red,
            fg="#FFFFFF",
            bd=0,
            state="disabled",
            padx=10,
            pady=6,
            command=self.stop_process
        )
        self.btn_stop.pack(side="left")

        self.progress = ttk.Progressbar(btn_bar, style="Custom.Horizontal.TProgressbar", mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        # Treeview Table
        tree_frame = ttk.Frame(table_group, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)

        columns = ("select", "stt", "channel", "title", "overlay_text", "desc", "keywords", "url")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

        self.tree.heading("select", text="Chọn [X]")
        self.tree.heading("stt", text="STT")
        self.tree.heading("channel", text="Kênh YouTube")
        self.tree.heading("title", text="Tên Video")
        self.tree.heading("overlay_text", text="📝 Chữ đưa vào Video (9:16)")
        self.tree.heading("desc", text="Nội dung mô tả")
        self.tree.heading("keywords", text="🔑 Từ khóa")
        self.tree.heading("url", text="Đường dẫn Video")

        self.tree.column("select", width=75, minwidth=65, stretch=False, anchor="center")
        self.tree.column("stt", width=40, minwidth=35, stretch=False, anchor="center")
        self.tree.column("channel", width=140, minwidth=120, stretch=False, anchor="w")
        self.tree.column("title", width=200, minwidth=160, stretch=True, anchor="w")
        self.tree.column("overlay_text", width=240, minwidth=180, stretch=True, anchor="w")
        self.tree.column("desc", width=250, minwidth=180, stretch=True, anchor="w")
        self.tree.column("keywords", width=180, minwidth=130, stretch=True, anchor="w")
        self.tree.column("url", width=160, minwidth=120, stretch=False, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.tree.bind("<Button-2>", self._on_tree_right_click)

        # 4. Live Console Log View (Khu vực theo dõi Log quy trình ở đáy màn hình)
        log_group = ttk.LabelFrame(
            main_container,
            text=" 🖥️ NHẬT KÝ THỰC THI THỜI GIAN THỰC (REALTIME LOG - THEO DÕI QUY TRÌNH CHẠY NỀN) ",
            style="Card.TLabelframe",
            padding=6
        )
        log_group.pack(fill="x", side="bottom", pady=(4, 0))

        self.log_text = ScrolledText(
            log_group,
            wrap="word",
            font=("Consolas", 9),
            bg=self.console_bg,
            fg="#E2E8F0",
            insertbackground="#06B6D4",
            bd=0,
            height=6
        )
        self.log_text.pack(fill="both", expand=True)

        # Configure color tags in log
        self.log_text.tag_config("TIME", foreground="#64748B")
        self.log_text.tag_config("INFO", foreground="#38BDF8")
        self.log_text.tag_config("SUCCESS", foreground="#34D399")
        self.log_text.tag_config("WARNING", foreground="#FBBF24")
        self.log_text.tag_config("ERROR", foreground="#F87171")

        self.log("Hệ thống sẵn sàng. Bấm 'GIAI ĐOẠN 1: QUÉT TÌM VIDEO' để tìm kiếm danh sách.", level="INFO")

    def _toggle_api_visibility(self):
        if self.show_key_var.get():
            self.api_entry.config(show="")
        else:
            self.api_entry.config(show="*")

    def _browse_output_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if chosen:
            self.output_dir_var.set(chosen)

    def log(self, message: str, level: str = "INFO"):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        def _append():
            try:
                self.log_text.insert(tk.END, f"[{now}] ", "TIME")
                self.log_text.insert(tk.END, f"[{level}] ", level)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
            except Exception:
                pass
        
        try:
            self.root.after(0, _append)
        except Exception:
            pass

    @staticmethod
    def _wrap_text(text: str, width: int = 70) -> str:
        clean_text = text.replace("\n", " ").strip()
        if not clean_text:
            return ""
        if clean_text.endswith("..."):
            clean_text = clean_text[:-3].strip()
        elif clean_text.endswith("…"):
            clean_text = clean_text[:-1].strip()
        lines = textwrap.wrap(clean_text, width=width)
        return "\n".join(lines)

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                # Chỉ toggle Chọn [X] nếu click đúng vào Cột #1 (Chọn [X])
                if column == "#1":
                    vals = list(self.tree.item(item_id, "values"))
                    current_sel = vals[0]
                    vals[0] = "⚪ KHÔNG" if ("✅" in current_sel or "CÓ" in current_sel) else "✅ CÓ"
                    self.tree.item(item_id, values=vals)
                    self._sort_tree_by_selection()
                elif column == "#5":
                    # Nhấp chuột vào cột #5 (Chữ đưa vào Video 9:16) -> Mở ngay hộp thoại sửa chữ!
                    self._edit_overlay_text(item_id)

    def _edit_selected_overlay_text(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn 1 dòng video trong bảng để sửa chữ 9:16!")
            return
        self._edit_overlay_text(selected_items[0])

    def _on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        column = self.tree.identify_column(event.x)
        # Nếu nhấp đúp vào cột #5 (Chữ đưa vào Video 9:16) -> Mở hộp thoại sửa chữ
        if column == "#5":
            self._edit_overlay_text(item_id)
            return

        video_dict = {v["video_id"]: v for v in self.stage1_results}
        vid = video_dict.get(item_id)
        if not vid:
            return

        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"Chi Tiết Video - {vid.get('channel_name', '')}")
        detail_win.geometry("750x550")
        detail_win.configure(bg=self.bg_dark)

        frame = ttk.Frame(detail_win, padding=15, style="Card.TFrame")
        frame.pack(fill="both", expand=True)

        lbl_title = tk.Label(frame, text=f"🎬 {vid['title']}", font=("Segoe UI", 11, "bold"), fg=self.accent_cyan, bg=self.card_bg, wraplength=700, justify="left")
        lbl_title.pack(anchor="w", pady=(0, 5))

        lbl_url = tk.Label(frame, text=f"🔗 {vid['url']}", font=("Segoe UI", 9), fg=self.accent_indigo, bg=self.card_bg)
        lbl_url.pack(anchor="w", pady=(0, 10))

        lbl_desc_heading = tk.Label(frame, text="📄 NỘI DUNG MÔ TẢ ĐẦY ĐỦ 100% (FULL UNTRUNCATED DESCRIPTION):", font=("Segoe UI", 10, "bold"), fg=self.text_light, bg=self.card_bg)
        lbl_desc_heading.pack(anchor="w", pady=(0, 5))

        txt = ScrolledText(frame, wrap="word", font=("Segoe UI", 9), bg="#0F172A", fg="#F8FAFC", bd=1, relief="solid")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", vid["description"])
        txt.config(state="disabled")

        btn_close = tk.Button(frame, text="Đóng cửa sổ", font=("Segoe UI", 9, "bold"), bg=self.card_border, fg="#FFFFFF", bd=0, padx=15, pady=5, command=detail_win.destroy)
        btn_close.pack(anchor="e", pady=(10, 0))

    def _edit_overlay_text(self, item_id: str):
        if not item_id:
            return
        video_dict = {v["video_id"]: v for v in self.stage1_results}
        vid = video_dict.get(item_id)
        if not vid:
            return

        # Yêu cầu 1: Đảm bảo chỉ hiển thị duy nhất 1 cửa sổ nhập chỉnh sửa chữ
        if hasattr(self, "active_edit_win") and self.active_edit_win is not None:
            try:
                if self.active_edit_win.winfo_exists():
                    self.active_edit_win.lift()
                    self.active_edit_win.focus_force()
                    return
            except Exception:
                pass

        current_text = vid.get("overlay_text", "")

        edit_win = tk.Toplevel(self.root)
        self.active_edit_win = edit_win
        edit_win.title("✏️ Chỉnh Sửa Chữ Hiển Thị Trên Video 9:16 (Banner Bottom)")
        edit_win.geometry("620x340")
        edit_win.configure(bg=self.bg_dark)
        try:
            edit_win.transient(self.root)
            edit_win.grab_set()
        except Exception:
            pass

        def _on_close():
            try:
                edit_win.grab_release()
            except Exception:
                pass
            edit_win.destroy()
            self.active_edit_win = None

        edit_win.protocol("WM_DELETE_WINDOW", _on_close)

        frame = ttk.Frame(edit_win, padding=15, style="Card.TFrame")
        frame.pack(fill="both", expand=True)

        lbl = tk.Label(
            frame,
            text="✏️ NỘI DUNG CHỮ HIỂN THỊ CHỒNG LÊN BANNER DƯỚI (Dưới 'THÔNG TIN VỀ THUẾ'):",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_cyan,
            bg=self.card_bg,
            wraplength=570,
            justify="left"
        )
        lbl.pack(anchor="w", pady=(0, 6))

        sub_lbl = tk.Label(
            frame,
            text="📌 Chữ sẽ xuất hiện dưới ô 'THÔNG TIN VỀ THUẾ' (Lề trái 3cm, lề phải 5cm). Hệ thống tự động VIẾT HOA TOÀN BỘ, CỠ CHỮ 52 BOLD (nổi bật chuẩn Thumbnail TikTok/Mobile) khi xuất Video 9:16.",
            font=("Segoe UI", 9),
            fg=self.text_muted,
            bg=self.card_bg,
            wraplength=570,
            justify="left"
        )
        sub_lbl.pack(anchor="w", pady=(0, 10))

        txt_entry = ScrolledText(frame, wrap="word", font=("Segoe UI", 10), bg="#0F172A", fg="#F8FAFC", bd=1, height=5)
        txt_entry.pack(fill="both", expand=True)
        txt_entry.insert("1.0", current_text)

        def _save():
            new_val = txt_entry.get("1.0", "end").strip()
            vid["overlay_text"] = new_val
            vals = list(self.tree.item(item_id, "values"))
            if len(vals) >= 7:
                vals[4] = self._wrap_text(new_val, width=32)
                self.tree.item(item_id, values=vals)
            self.log(f"Đã cập nhật chữ Overlay 9:16: '{new_val}'", level="SUCCESS")
            _on_close()

        btn_box = ttk.Frame(frame, style="Card.TFrame")
        btn_box.pack(fill="x", pady=(10, 0))

        btn_save = tk.Button(btn_box, text="💾 Lưu & Cập Nhật", font=("Segoe UI", 9, "bold"), bg=self.btn_green, fg="#FFFFFF", bd=0, padx=15, pady=5, command=_save)
        btn_save.pack(side="right", padx=(5, 0))

        btn_cancel = tk.Button(btn_box, text="Hủy", font=("Segoe UI", 9), bg=self.card_border, fg="#FFFFFF", bd=0, padx=12, pady=5, command=_on_close)
        btn_cancel.pack(side="right")

    def _on_tree_right_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            vals = self.tree.item(item_id, "values")
            if not vals:
                return

            video_dict = {v["video_id"]: v for v in self.stage1_results}
            vid = video_dict.get(item_id)

            menu = tk.Menu(self.root, tearoff=0, bg="#1E293B", fg="#F8FAFC", activebackground="#6366F1", activeforeground="#FFFFFF")

            title_val = vid["title"] if vid else vals[3]
            overlay_val = vid.get("overlay_text", "") if vid else (vals[4] if len(vals) > 4 else "")
            desc_val = vid["description"] if vid else (vals[5] if len(vals) > 5 else "")
            kw_val = vid.get("keywords_str", "") if vid else (vals[6] if len(vals) > 6 else "")
            url_val = vid["url"] if vid else (vals[7] if len(vals) > 7 else "")
            channel_val = vid["channel_name"] if vid else vals[2]

            def _copy(val: str, label: str):
                self.root.clipboard_clear()
                self.root.clipboard_append(val)
                self.log(f"Đã sao chép {label} vào Clipboard.", level="SUCCESS")

            menu.add_command(label="✏️ Chỉnh sửa chữ đưa vào Video (9:16)", command=lambda: self._edit_overlay_text(item_id))
            menu.add_separator()
            menu.add_command(label="📋 Sao chép Chữ hiển thị 9:16", command=lambda: _copy(overlay_val, "Chữ 9:16"))
            menu.add_command(label="📋 Sao chép Tên Video", command=lambda: _copy(title_val, "Tên Video"))
            menu.add_command(label="📋 Sao chép Nội dung mô tả", command=lambda: _copy(desc_val, "Nội dung mô tả"))
            menu.add_command(label="📋 Sao chép Từ khóa khớp", command=lambda: _copy(kw_val, "Từ khóa"))
            menu.add_command(label="📋 Sao chép Đường dẫn Video (URL)", command=lambda: _copy(url_val, "Đường dẫn Video"))
            menu.add_command(label="📋 Sao chép Kênh YouTube", command=lambda: _copy(channel_val, "Kênh YouTube"))
            menu.add_separator()
            full_str = f"Kênh: {channel_val}\nTiêu đề: {title_val}\nChữ 9:16: {overlay_val}\nMô tả: {desc_val}\nTừ khóa: {kw_val}\nURL: {url_val}"
            menu.add_command(label="📋 Sao chép Tất cả thông tin dòng này", command=lambda: _copy(full_str, "Tất cả thông tin dòng"))

            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _sort_tree_by_selection(self):
        """
        Sắp xếp lại bảng Treeview:
        - Các dòng được chọn (✅ CÓ) sẽ tự động đẩy lên phía trên cùng.
        - Các dòng không chọn (⚪ KHÔNG) sẽ nằm bên dưới.
        - Tự động đánh lại thứ tự STT (Cột 2) từ 1..N.
        """
        items = self.tree.get_children()
        if not items:
            return

        selected_items = []
        unselected_items = []
        for item_id in items:
            vals = self.tree.item(item_id, "values")
            if vals and ("✅" in vals[0] or "CÓ" in vals[0]):
                selected_items.append(item_id)
            else:
                unselected_items.append(item_id)

        ordered_items = selected_items + unselected_items

        for index, item_id in enumerate(ordered_items, start=1):
            self.tree.move(item_id, "", index - 1)
            vals = list(self.tree.item(item_id, "values"))
            if len(vals) >= 2:
                vals[1] = index
                self.tree.item(item_id, values=vals)

    def _set_all_selection(self, select_state: bool):
        mark = "✅ CÓ" if select_state else "⚪ KHÔNG"
        for item_id in self.tree.get_children():
            vals = list(self.tree.item(item_id, "values"))
            vals[0] = mark
            self.tree.item(item_id, values=vals)
        self._sort_tree_by_selection()

    def _browse_cookie_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file cookies.txt của YouTube",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path and os.path.exists(file_path):
            try:
                from config import DEFAULT_COOKIE_PATH
                import shutil
                shutil.copy2(file_path, DEFAULT_COOKIE_PATH)
                self.log(f"[COOKIES] Nạp thành công file cookies: '{file_path}' ➔ Đã lưu vào assets/cookies.txt!", level="SUCCESS")
                messagebox.showinfo(
                    "Nạp Cookies Thành Công",
                    f"Đã nạp file cookies.txt thành công!\n\nYouTube Stage 2 sẽ tự động sử dụng file cookie này để vượt Bot Protection và tải video mượt mà 100%!"
                )
            except Exception as e:
                self.log(f"[LỖI NẠP COOKIES] {e}", level="ERROR")
                messagebox.showerror("Lỗi Nạp Cookies", f"Không thể lưu file cookies: {e}")

    def start_stage1_search(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Thiếu thông tin", "Vui lòng nhập YouTube Data API Key v3!")
            return

        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()

        selected_channels = [
            info for ch_name, (var, info) in self.channel_vars.items() if var.get()
        ]
        if not selected_channels:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất 1 đài truyền hình!")
            return

        kw_list = [k.strip() for k in self.keywords_var.get().split(",") if k.strip()]

        self.is_running = True
        self.btn_stage1.config(state="disabled", bg="#475569")
        self.btn_stage2.config(state="disabled", bg="#475569")
        self.btn_stop.config(state="normal", bg=self.btn_red)
        self.progress.start(10)

        # Clear old tree items
        for item in self.tree.get_children():
            self.tree.delete(item)

        thread = threading.Thread(
            target=self._worker_stage1,
            args=(api_key, start_date, end_date, selected_channels, kw_list),
            daemon=True
        )
        thread.start()

    def _worker_stage1(self, api_key: str, start_date: str, end_date: str, channels: list, keywords: list):
        try:
            ch_names = ", ".join([c["name"] for c in channels])
            self.log(f"[GIAI ĐOẠN 1 START] Quét các kênh [{ch_names}] từ {start_date} đến {end_date} theo từ khóa thuế...", level="INFO")
            searcher = YouTubeSearcher(api_key=api_key)
            videos = searcher.search_multi_channels(
                start_date=start_date,
                end_date=end_date,
                channels=channels,
                tax_keywords=keywords,
                filter_by_metadata=True
            )

            self.stage1_results = videos

            def _update_ui():
                for idx, vid in enumerate(videos, 1):
                    clean_topic = vid["title"].split("|")[0].split("-")[0].strip()
                    vid["overlay_text"] = clean_topic

                    wrapped_title = self._wrap_text(vid["title"], width=32)
                    wrapped_overlay = self._wrap_text(clean_topic, width=32)
                    wrapped_desc = self._wrap_text(vid["description"], width=45)
                    wrapped_kws = self._wrap_text(vid.get("keywords_str", "Thuế"), width=25)

                    self.tree.insert(
                        "",
                        "end",
                        iid=vid["video_id"],
                        values=("⚪ KHÔNG", idx, vid["channel_name"], wrapped_title, wrapped_overlay, wrapped_desc, wrapped_kws, vid["url"])
                    )

                self.is_running = False
                self._sort_tree_by_selection()
                self.progress.stop()
                self.btn_stage1.config(state="normal", bg=self.accent_indigo)
                self.btn_stage2.config(state="normal", bg=self.btn_green)
                self.btn_stop.config(state="disabled", bg="#475569")

                if not videos:
                    self.log("[GIAI ĐOẠN 1] Không tìm thấy video nào có Tiêu đề / Mô tả khớp từ khóa.", level="WARNING")
                    messagebox.showinfo("Giai đoạn 1", "Không tìm thấy video nào phù hợp điều kiện.")
                else:
                    self.log(f"[GIAI ĐOẠN 1 COMPLETE] Đã quét xong! Tìm thấy {len(videos)} video khớp từ khóa.", level="SUCCESS")
                    messagebox.showinfo("Giai đoạn 1", f"Đã tìm thấy {len(videos)} video. Vui lòng chọn các video cần bóc tách ở Giai đoạn 2!")

            self.root.after(0, _update_ui)

        except Exception as e:
            err_msg = str(e)
            self.log(f"[GIAI ĐOẠN 1 LỖI] {err_msg}", level="ERROR")
            def _error_reset(msg=err_msg):
                self.is_running = False
                self.progress.stop()
                self.btn_stage1.config(state="normal", bg=self.accent_indigo)
                self.btn_stage2.config(state="normal", bg=self.btn_green)
                self.btn_stop.config(state="disabled", bg="#475569")
                messagebox.showerror("Lỗi Giai đoạn 1", msg)
            self.root.after(0, _error_reset)

    def start_stage2_process(self):
        selected_vids = []
        video_dict = {v["video_id"]: v for v in self.stage1_results}

        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, "values")
            if vals and ("✅" in vals[0] or "CÓ" in vals[0] or vals[0] == "☑"):
                vid_obj = video_dict.get(item_id)
                if vid_obj:
                    selected_vids.append(vid_obj)

        if not selected_vids:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất 1 video từ danh sách Giai đoạn 1!")
            return

        kw_list = [k.strip() for k in self.keywords_var.get().split(",") if k.strip()]
        output_dir = self.output_dir_var.get().strip()

        try:
            buf_start = float(self.buf_start_var.get().strip())
            buf_end = float(self.buf_end_var.get().strip())
            max_gap = float(self.max_gap_var.get().strip())
        except ValueError:
            buf_start, buf_end, max_gap = 25.0, 35.0, 60.0

        self.is_running = True
        self.btn_stage1.config(state="disabled", bg="#475569")
        self.btn_stage2.config(state="disabled", bg="#475569")
        self.btn_stop.config(state="normal", bg=self.btn_red)
        self.progress.start(10)

        thread = threading.Thread(
            target=self._worker_stage2,
            args=(selected_vids, kw_list, output_dir, buf_start, buf_end, max_gap),
            daemon=True
        )
        thread.start()

    def stop_process(self):
        self.is_running = False
        if hasattr(self, "current_downloader") and self.current_downloader:
            try:
                self.current_downloader.abort()
            except Exception:
                pass
        self.log("Đã phát lệnh dừng quy trình từ người dùng...", level="WARNING")

    def _finish_stage2(self, msg: str):
        def _reset():
            self.is_running = False
            self.progress.stop()
            self.btn_stage1.config(state="normal", bg=self.accent_indigo)
            self.btn_stage2.config(state="normal", bg=self.btn_green)
            self.btn_stop.config(state="disabled", bg="#475569")
            self.log(msg, level="SUCCESS")
            messagebox.showinfo("Giai đoạn 2 Hoàn thành", msg)

        self.root.after(0, _reset)

    def _worker_stage2(
        self,
        videos: list,
        keywords: list,
        output_dir: str,
        buf_start: float,
        buf_end: float,
        max_gap: float
    ):
        try:
            self.log(f"[GIAI ĐOẠN 2 START] Bóc tách phụ đề/Whisper & Kết xuất video 9:16 cho {len(videos)} video đã chọn...", level="INFO")

            analyzer = TranscriptAnalyzer(
                keywords=keywords,
                buffer_start=buf_start,
                buffer_end=buf_end,
                max_gap=max_gap
            )
            downloader = VideoDownloader(output_dir=output_dir)
            self.current_downloader = downloader
            excel_path = os.path.join(output_dir, "Danh_Sach_Video_Thue.xlsx")
            logger = ExcelLogger(excel_path=excel_path)

            total_downloaded = 0
            used_filenames = set()

            for idx, vid in enumerate(videos, 1):
                if not self.is_running:
                    self.log("Người dùng đã hủy quy trình xử lý Giai đoạn 2.", level="WARNING")
                    break

                v_title = vid["title"]
                v_id = vid["video_id"]
                v_url = vid["url"]
                c_name = vid.get("channel_name", vid.get("channel_title", "VTV"))
                p_date = vid.get("published_at", "")
                v_desc = vid.get("description", "")
                overlay_text = vid.get("overlay_text", "")

                # Đặt tên file chính là nội dung ở Cột 5 (overlay_text) theo đúng yêu cầu người dùng
                col5_text = overlay_text or v_title
                clean_col5 = downloader.sanitize_filename(col5_text)
                base_clean = clean_col5
                filename = f"{base_clean}.mp4"

                # Tự động gắn hậu tố nếu có video khác trùng tên Cột 5 để không bao giờ bị ghi đè mất file
                counter = 1
                while filename.lower() in used_filenames:
                    counter += 1
                    filename = f"{base_clean}_{counter}.mp4"
                used_filenames.add(filename.lower())

                display_name = os.path.splitext(filename)[0]
                self.log(f"[{idx}/{len(videos)}] Bắt đầu xử lý video '{display_name}'...", level="INFO")

                # Lấy nội dung liên quan thuế (nếu có từ phụ đề hoặc mô tả) để ghi chú vào Excel
                tax_text = v_desc
                try:
                    tax_sections = analyzer.extract_tax_sections(
                        video_id=v_id,
                        video_title=v_title,
                        video_description=v_desc,
                        video_url=v_url
                    )
                    if tax_sections:
                        tax_text = "\n---\n".join([s.get("tax_text", "") for s in tax_sections if s.get("tax_text")])
                except Exception:
                    pass

                try:
                    res = downloader.download_video_section(
                        video_url=v_url,
                        start_seconds=0,
                        end_seconds=0,
                        output_filename=filename,
                        overlay_text=overlay_text,
                        progress_callback=lambda msg: self.log(msg, level="INFO")
                    )

                    goc_path = res.get("goc_path", "")
                    cut_path = res.get("cut_path", "")

                    goc_name = os.path.basename(goc_path)
                    cut_name = os.path.basename(cut_path)

                    self.log(f"-> [THÀNH CÔNG FILE GỐC] Đã lưu video nguyên bản từ YouTube: {goc_name}", level="SUCCESS")
                    self.log(f"-> [THÀNH CÔNG FILE 9:16] Đã dựng ghép _top2.png + Chữ Overlay + _Bottom_1.png: {cut_name}", level="SUCCESS")

                    # Ghi vào file Excel thông tin video
                    main_title = v_title.split("|")[0].split("-")[0].strip()
                    topic_str = f"Chủ đề Thuế: {main_title[:45]}"
                    dur_sec = downloader.get_video_duration(goc_path)
                    dur_str = f"{int(dur_sec//60):02d}:{int(dur_sec%60):02d}"

                    logger.append_log(
                        filename=cut_name,
                        topic=topic_str,
                        tax_content=tax_text,
                        original_link=v_url,
                        duration_str=dur_str
                    )

                    total_downloaded += 1
                except Exception as err:
                    self.log(f"-> Lỗi khi tải/dựng video '{clean_col5}': {err}", level="ERROR")

            self._finish_stage2(f"Giai đoạn 2 hoàn thành! Đã lưu thành công {total_downloaded} bộ video (_gốc.mp4 và _cut.mp4) tại {output_dir}")

        except Exception as e:
            self.log(f"[GIAI ĐOẠN 2 LỖI] {str(e)}", level="ERROR")
            self._finish_stage2(f"Quy trình bị gián đoạn do lỗi: {str(e)}")
