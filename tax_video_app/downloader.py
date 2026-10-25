import os
import re
import subprocess
import yt_dlp
from typing import Dict, Any

class VideoDownloader:
    def __init__(self, output_dir: str = r"D:\Data_Video"):
        self.output_dir = output_dir
        self.current_process = None
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def abort(self):
        """Dừng tiến trình FFmpeg đang chạy nếu người dùng bấm Hủy."""
        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass
            self.current_process = None

    @staticmethod
    def sanitize_filename(name: str, max_len: int = 150) -> str:
        """
        Làm sạch tên file, loại bỏ các ký tự đặc biệt không hợp lệ trên Windows (\\ / : * ? " < > |).
        Giữ nguyên khoảng trắng và ký tự tiếng Việt.
        """
        if not name or not name.strip():
            return "Video_Thue"
        clean_name = re.sub(r'[\\/*?:"<>|]', '', name.strip())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        if len(clean_name) > max_len:
            clean_name = clean_name[:max_len].strip()
        return clean_name or "Video_Thue"

    def generate_filename(
        self,
        channel_name: str,
        published_date: str,
        keywords: list,
        section_index: int = 1
    ) -> str:
        """
        Tạo tên file theo đúng yêu cầu: [Tên đài]_[Ngày]_[Từ khóa rút gọn].mp4
        Ví dụ: VTV_10102026_ThueDat.mp4
        """
        # Rút gọn tên đài (VD: "VTV24 Official" -> "VTV")
        dai = "DaiTruyenHinh"
        c_upper = channel_name.upper()
        if "VTV" in c_upper:
            dai = "VTV"
        elif "HTV" in c_upper:
            dai = "HTV"
        elif "HANOI" in c_upper or "HÀ NỘI" in c_upper:
            dai = "HanoiTV"
        elif "BÌNH DƯƠNG" in c_upper or "BTV" in c_upper:
            dai = "BTV"
        elif "THVL" in c_upper:
            dai = "THVL"
        else:
            dai = self.sanitize_filename(channel_name)

        # Đổi ngày định dạng ISO sang DDMMYYYY (VD: 2026-10-10T... -> 10102026)
        date_str = "NGAY"
        if published_date:
            try:
                # Nếu là định dạng ISO
                d_part = published_date.split("T")[0]
                parts = d_part.split("-")
                if len(parts) == 3:
                    date_str = f"{parts[2]}{parts[1]}{parts[0]}"
            except Exception:
                date_str = published_date.replace("/", "").replace("-", "")

        # Từ khóa rút gọn
        kw_str = "Thue"
        if keywords:
            # Chọn 1-2 từ khóa đầu tiên bỏ khoảng trắng
            raw_kw = "_".join(keywords[:2])
            kw_str = self.sanitize_filename(raw_kw).replace("_", "")

        filename = f"{dai}_{date_str}_{kw_str}_doan{section_index}.mp4"
        return filename

    @staticmethod
    def render_bottom_banner_with_text(
        bottom_banner_path: str,
        overlay_text: str,
        target_width: int = 1080,
        target_height: int = 1062
    ) -> str:
        """
        Vẽ nội dung chữ do người dùng nhập lên ảnh Banner _Bottom_1.png:
        - Vị trí: Đặt bên dưới chữ "THÔNG TIN VỀ THUẾ"
        - Lề trái: Cách ~5cm (~210px ở chiều rộng 1080px)
        - Lề phải: Cách ~7cm (~280px ở chiều rộng 1080px -> max text width = 590px)
        - Tự động xuống hàng nếu văn bản quá dài.
        """
        if not overlay_text or not overlay_text.strip():
            return bottom_banner_path

        # Tự động chuyển toàn bộ nội dung sang VIẾT HOA theo yêu cầu
        overlay_text_upper = overlay_text.strip().upper()

        try:
            from PIL import Image, ImageDraw, ImageFont
            with Image.open(bottom_banner_path) as base_img:
                img = base_img.convert("RGBA").resize((target_width, target_height), Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(img)

                # Chọn font BOLD Tiếng Việt chuẩn hệ thống Windows
                font_path = "arialbd.ttf"
                for f_candidate in ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "segoeui.ttf", "arial.ttf"]:
                    p = os.path.join(r"C:\Windows\Fonts", f_candidate)
                    if os.path.exists(p):
                        font_path = p
                        break

                # Kích cỡ chữ tối ưu cho Thumbnail TikTok / Màn hình điện thoại: 52pt BOLD
                font_size = 52
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except Exception:
                    font = ImageFont.load_default()

                x_left = 130  # Lề trái cách 3cm (~130px trên canvas 1080px)
                max_text_w = 800  # Lề phải cách ~150px
                y_start = 220  # Bên dưới ô kính THÔNG TIN VỀ THUẾ

                words = overlay_text_upper.split()
                lines = []
                cur_line = []

                for word in words:
                    test_line = " ".join(cur_line + [word])
                    try:
                        bbox = font.getbbox(test_line)
                        w_line = bbox[2] - bbox[0]
                    except Exception:
                        w_line = len(test_line) * (font_size * 0.55)

                    if w_line <= max_text_w:
                        cur_line.append(word)
                    else:
                        if cur_line:
                            lines.append(" ".join(cur_line))
                        cur_line = [word]
                if cur_line:
                    lines.append(" ".join(cur_line))

                cur_y = y_start
                line_spacing = font_size + 16

                for line in lines:
                    # Viền bóng đen đậm 3px làm nổi bật chữ trắng trên mọi tông nền đỏ
                    for dx in (-3, -2, 0, 2, 3):
                        for dy in (-3, -2, 0, 2, 3):
                            if dx != 0 or dy != 0:
                                draw.text((x_left + dx, cur_y + dy), line, font=font, fill=(0, 0, 0, 240))
                    # Chữ BOLD chính màu trắng sáng tinh khiết
                    draw.text((x_left, cur_y), line, font=font, fill=(255, 255, 255, 255))
                    cur_y += line_spacing

                temp_dir = os.path.join(os.path.dirname(bottom_banner_path), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                out_img_path = os.path.join(temp_dir, f"_bottom_overlay_{abs(hash(overlay_text))}.png")
                img.convert("RGB").save(out_img_path)
                return out_img_path

        except Exception as e:
            print(f"[CẢNH BÁO PIL OVERLAY] Lỗi vẽ chữ lên banner bottom: {e}")
            return bottom_banner_path

    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """
        Lấy độ dài thời gian chính xác của video (tính bằng giây) qua ffprobe.
        """
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return max(0.5, float(res.stdout.strip()))
        except Exception:
            return 0.0

    def create_916_vertical_video(
        self,
        raw_video_path: str,
        output_cut_path: str,
        top_banner_path: str = None,
        bottom_banner_path: str = None,
        overlay_text: str = "",
        progress_callback = None
    ) -> str:
        """
        Tạo video kết xuất 9:16 ghép 3 phần theo đúng cấu trúc file full.png:
        - Phía trên cùng: file _top2.png (Lặp lại chuẩn 100% theo thời lượng video)
        - Ở giữa: video cắt nội dung tin tức
        - Phía dưới cùng: file _Bottom_1.png (Lặp lại chuẩn 100% theo thời lượng video + chữ overlay)
        Sử dụng Popen đọc stream liên tục tránh deadlock tràn pipe buffer trên Windows, đồng thời báo cáo tiến độ thời gian thực.
        """
        from config import DEFAULT_TOP_BANNER_PATH, DEFAULT_BOTTOM_BANNER_PATH
        top_path = top_banner_path or DEFAULT_TOP_BANNER_PATH
        bottom_path_raw = bottom_banner_path or DEFAULT_BOTTOM_BANNER_PATH

        log_fn = progress_callback or print

        if not os.path.exists(top_path) or not os.path.exists(bottom_path_raw):
            log_fn("[CẢNH BÁO] Không tìm thấy file banner _top2.png hoặc _Bottom_1.png. Kết xuất video gốc.")
            return raw_video_path

        # Tự động xóa file 0 KB cũ nếu có để tránh lỗi file hỏng
        if os.path.exists(output_cut_path) and os.path.getsize(output_cut_path) == 0:
            try:
                os.remove(output_cut_path)
            except Exception:
                pass

        # Tự động vẽ chữ người dùng nhập lên banner _Bottom_1.png
        bottom_path = self.render_bottom_banner_with_text(
            bottom_banner_path=bottom_path_raw,
            overlay_text=overlay_text,
            target_width=1080,
            target_height=1062
        )

        top_h = 250
        try:
            from PIL import Image
            with Image.open(top_path) as img:
                w, h = img.size
                top_h = int(round(1080 * h / w))
        except Exception:
            top_h = 250

        video_h = 608
        bottom_h = max(200, 1920 - top_h - video_h)
        y_video = top_h
        y_bottom = top_h + video_h

        # Lấy độ dài thời gian chính xác của video cắt ra để lặp banner đủ thời gian
        video_dur = self.get_video_duration(raw_video_path)
        dur_str = f":d={video_dur:.2f}" if video_dur > 0 else ":d=1000"

        filter_str = (
            f"[0:v]scale=1080:{video_h}[vid]; "
            f"[1:v]scale=1080:{top_h}[top]; "
            f"[2:v]scale=1080:{bottom_h}[bottom]; "
            f"color=c=black:s=1080x1920{dur_str}[bg]; "
            f"[bg][top]overlay=0:0[tmp1]; "
            f"[tmp1][vid]overlay=0:{y_video}[tmp2]; "
            f"[tmp2][bottom]overlay=0:{y_bottom}[vout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", raw_video_path,
            "-loop", "1", "-i", top_path,
            "-loop", "1", "-i", bottom_path,
            "-filter_complex", filter_str,
            "-map", "[vout]",
            "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart"
        ]

        if video_dur > 0:
            cmd.extend(["-t", f"{video_dur:.2f}"])
        else:
            cmd.append("-shortest")

        cmd.append(output_cut_path)

        dur_fmt = f"{int(video_dur//3600):02d}:{int((video_dur%3600)//60):02d}:{int(video_dur%60):02d}" if video_dur > 0 else f"{video_dur:.1f}s"
        log_fn(f"[RENDER 9:16] Đang kết xuất video 9:16 ghép Banner Top & Bottom (Thời lượng: {dur_fmt}, Chữ overlay: '{overlay_text[:35]}...')...")

        try:
            # Dùng Popen và merge stderr vào stdout để đọc stream liên tục, tránh tuyệt đối lỗi pipe deadlock gây treo 0 KB
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace"
            )
            self.current_process = process

            import time
            last_report = time.time()
            time_regex = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d+)")

            for line in process.stdout:
                now = time.time()
                # Cập nhật tiến độ mỗi 4 giây 1 lần
                if now - last_report >= 4.0:
                    match = time_regex.search(line)
                    if match:
                        cur_time_str = match.group(1).split(".")[0]
                        pct_str = ""
                        try:
                            parts = cur_time_str.split(":")
                            cur_secs = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                            if video_dur > 0:
                                pct = min(100.0, (cur_secs / video_dur) * 100.0)
                                pct_str = f" ({pct:.1f}%)"
                        except Exception:
                            pass
                        log_fn(f"-> [TIẾN ĐỘ 9:16] Đang render: {cur_time_str} / {dur_fmt}{pct_str}...")
                        last_report = now

            process.wait()
            self.current_process = None

            if process.returncode == 0 and os.path.exists(output_cut_path) and os.path.getsize(output_cut_path) > 1000:
                mb_out = os.path.getsize(output_cut_path) / (1024 * 1024)
                log_fn(f"[THÀNH CÔNG 9:16] Đã tạo video 9:16 thành công ({mb_out:.1f} MB): {os.path.basename(output_cut_path)}")
                return output_cut_path
            else:
                log_fn(f"[CẢNH BÁO FFmpeg 9:16] Mã thoát: {process.returncode}")
                # Xóa file dở dang nếu FFmpeg bị ngắt hoặc lỗi để tránh tệp cụt
                if os.path.exists(output_cut_path):
                    try:
                        os.remove(output_cut_path)
                    except Exception:
                        pass
        except Exception as e:
            log_fn(f"[CẢNH BÁO FFmpeg 9:16 LỖI] {e}")
            if os.path.exists(output_cut_path):
                try:
                    os.remove(output_cut_path)
                except Exception:
                    pass
        finally:
            self.current_process = None

        return raw_video_path

    def download_video_section(
        self,
        video_url: str,
        start_seconds: float = 0,
        end_seconds: float = 0,
        output_filename: str = "",
        overlay_text: str = "",
        progress_callback = None
    ) -> Dict[str, str]:
        """
        Tải và kết xuất ra 2 file theo đúng yêu cầu:
        1. File video gốc: {filename_base}_gốc.mp4 (Requirement 5)
        2. File video 9:16 kết xuất: {filename_base}.mp4 kèm chữ overlay
        Có kiểm tra Cache file gốc để tránh tải lại video hàng trăm MB nhiều lần.
        """
        base_name, ext = os.path.splitext(output_filename)
        if not ext:
            ext = ".mp4"

        goc_filename = f"{base_name}_gốc{ext}"
        cut_filename = f"{base_name}{ext}"

        goc_filepath = os.path.join(self.output_dir, goc_filename)
        cut_filepath = os.path.join(self.output_dir, cut_filename)

        log_fn = progress_callback or print

        # KIỂM TRA CACHE VIDEO GỐC: Nếu file gốc đã tồn tại với dung lượng hợp lệ (> 500KB), bỏ qua tải lại từ YouTube
        downloaded_goc = False
        if os.path.exists(goc_filepath) and os.path.getsize(goc_filepath) > 500000:
            mb_size = os.path.getsize(goc_filepath) / (1024 * 1024)
            log_fn(f"[CACHE GỐC] Đã tìm thấy video gốc đã tải trước đó ({mb_size:.1f} MB): {goc_filename} (Bỏ qua tải lại)")
            downloaded_goc = True
        else:
            log_fn(f"[DOWNLOADING RAW] Đang tải video gốc từ YouTube ({video_url})...")

            # Tìm kiếm file cookies.txt nếu có
            cookie_file = None
            from config import DEFAULT_COOKIE_PATH, APP_DIR
            candidate_cookies = [
                DEFAULT_COOKIE_PATH,
                os.path.join(APP_DIR, "cookies.txt"),
                os.path.join(APP_DIR, "assets", "cookies.txt"),
                os.path.join(os.getcwd(), "cookies.txt"),
                os.path.join(os.getcwd(), "youtube_cookies.txt"),
                os.path.join(self.output_dir, "cookies.txt")
            ]
            for c in candidate_cookies:
                if os.path.exists(c) and os.path.getsize(c) > 0:
                    cookie_file = c
                    log_fn(f"[COOKIES] Phát hiện và sử dụng file cookies: {c}")
                    break

            client_candidates = [
                None,  # Ưu tiên default client của yt-dlp (ổn định nhất, không bị lỗi GVS PO Token của mweb/ios)
                ['web', 'mweb'],
                ['tv_embedded'],
                ['android']
            ]

            for clients in client_candidates:
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': goc_filepath,
                    'remote_components': {'ejs:github': {}},
                    'overwrites': True,
                    'quiet': True,
                    'no_warnings': True,
                }
                if clients:
                    ydl_opts['extractor_args'] = {'youtube': {'player_client': clients}}
                if cookie_file:
                    ydl_opts['cookiefile'] = cookie_file
                    ydl_opts['cookiefile'] = cookie_file

                for browser_name in ['chrome', 'edge', 'firefox']:
                    try:
                        ydl_opts_c = dict(ydl_opts)
                        ydl_opts_c['cookiesfrombrowser'] = (browser_name,)
                        with yt_dlp.YoutubeDL(ydl_opts_c) as ydl:
                            ydl.download([video_url])
                        if os.path.exists(goc_filepath) and os.path.getsize(goc_filepath) > 10000:
                            downloaded_goc = True
                            break
                    except Exception:
                        pass

                if downloaded_goc:
                    break

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    if os.path.exists(goc_filepath) and os.path.getsize(goc_filepath) > 10000:
                        downloaded_goc = True
                        break
                except Exception:
                    continue

            if not downloaded_goc:
                cmd = [
                    "yt-dlp",
                    "--remote-components", "ejs:github",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4",
                    "-o", goc_filepath
                ]
                if cookie_file:
                    cmd.extend(["--cookies", cookie_file])
                cmd.append(video_url)

                try:
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                    if os.path.exists(goc_filepath):
                        downloaded_goc = True
                except Exception as err:
                    raise RuntimeError(
                        f"Lỗi khi tải video từ YouTube: {err}\n"
                        f"⚠️ YouTube yêu cầu xác minh Bot (Sign in to confirm you're not a bot).\n"
                        f"💡 Hướng dẫn: Vui lòng nhấn nút '🍪 Nạp Cookies' trên giao diện hoặc đặt file 'cookies.txt' vào thư mục 'assets/' để ứng dụng tự động tải mượt mà!"
                    )

        final_cut_path = self.create_916_vertical_video(
            raw_video_path=goc_filepath,
            output_cut_path=cut_filepath,
            overlay_text=overlay_text,
            progress_callback=progress_callback
        )

        return {
            "goc_path": goc_filepath,
            "cut_path": final_cut_path
        }
