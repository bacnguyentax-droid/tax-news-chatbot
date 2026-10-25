import sys
import os
import argparse
import tkinter as tk

# Đảm bảo tương thích khi đóng gói PyInstaller chạy ở chế độ no-console (--windowed)
if sys.stdout is None:
    class DummyWriter:
        def write(self, s): pass
        def flush(self): pass
    sys.stdout = DummyWriter()
if sys.stderr is None:
    class DummyWriter:
        def write(self, s): pass
        def flush(self): pass
    sys.stderr = DummyWriter()
from app_gui import AppGUI
from youtube_searcher import YouTubeSearcher
from transcript_analyzer import TranscriptAnalyzer
from downloader import VideoDownloader
from excel_logger import ExcelLogger
from config import DEFAULT_CHANNELS, DEFAULT_OUTPUT_DIR, DEFAULT_TAX_KEYWORDS, DEFAULT_YOUTUBE_API_KEY

def run_cli(api_key: str, start_date: str, end_date: str, output_dir: str):
    print("=" * 60)
    print(" ỨNG DỤNG TỰ ĐỘNG TÌM KẾM & CẮT VIDEO THUẾ (CLI MODE)")
    print("=" * 60)
    print(f"- Khoảng thời gian: {start_date} -> {end_date}")
    print(f"- Thư mục xuất file: {output_dir}")

    searcher = YouTubeSearcher(api_key=api_key)
    videos = searcher.search_multi_channels(
        start_date=start_date,
        end_date=end_date,
        channels=DEFAULT_CHANNELS,
        tax_keywords=DEFAULT_TAX_KEYWORDS
    )


    if not videos:
        print("[THÔNG BÁO] Không tìm thấy video nào.")
        return

    print(f"[TÌM THẤY] Tổng cộng {len(videos)} video.")

    analyzer = TranscriptAnalyzer(keywords=DEFAULT_TAX_KEYWORDS)
    downloader = VideoDownloader(output_dir=output_dir)
    excel_path = os.path.join(output_dir, "Danh_Sach_Video_Thue.xlsx")
    logger = ExcelLogger(excel_path=excel_path)

    total_count = 0
    for idx, vid in enumerate(videos, 1):
        v_title = vid["title"]
        v_id = vid["video_id"]
        v_url = vid["url"]
        c_name = vid.get("channel_name", vid.get("channel_title", "VTV"))
        p_date = vid.get("published_at", "")

        v_desc = vid.get("description", "")
        print(f"\n[{idx}/{len(videos)}] Phân tích: {v_title} ({v_id})")
        tax_sections = analyzer.extract_tax_sections(
            video_id=v_id,
            video_title=v_title,
            video_description=v_desc,
            video_url=v_url
        )

        if not tax_sections:
            print("  -> Bỏ qua (không có thông tin thuế).")
            continue

        for sec_idx, sec in enumerate(tax_sections, 1):
            filename = downloader.generate_filename(
                channel_name=c_name,
                published_date=p_date,
                keywords=sec["matched_keywords"],
                section_index=sec_idx
            )
            print(f"  -> Cắt đoạn {sec_idx}: {sec['start_str']} - {sec['end_str']} ({sec['duration_str']})")

            try:
                downloader.download_video_section(
                    video_url=v_url,
                    start_seconds=sec["start_seconds"],
                    end_seconds=sec["end_seconds"],
                    output_filename=filename
                )
                main_title = v_title.split("|")[0].split("-")[0].strip()
                kw_prefix = ", ".join([k.capitalize() for k in sec["matched_keywords"][:2]]) if sec["matched_keywords"] else "Thuế"
                topic_str = f"Chủ đề {kw_prefix}: {main_title[:45]}"

                logger.append_log(
                    filename=filename,
                    topic=topic_str,
                    tax_content=sec["tax_text"],
                    original_link=v_url,
                    duration_str=sec["duration_str"]
                )

                total_count += 1
            except Exception as e:
                print(f"  -> Lỗi: {e}")

    print("=" * 60)
    print(f"HOÀN THÀNH! Đã lưu {total_count} video cắt vào {output_dir}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="YouTube Tax Video Downloader & Trimmer")
    parser.add_argument("--cli", action="store_true", help="Chạy ở chế độ giao diện dòng lệnh CLI")
    parser.add_argument("--api-key", type=str, default=DEFAULT_YOUTUBE_API_KEY, help="YouTube Data API Key v3")
    parser.add_argument("--start-date", type=str, help="Từ ngày (DD/MM/YYYY)")
    parser.add_argument("--end-date", type=str, help="Đến ngày (DD/MM/YYYY)")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Thư mục lưu trữ")


    args = parser.parse_args()

    if args.cli or (args.api_key and args.start_date and args.end_date):
        if not args.api_key or not args.start_date or not args.end_date:
            print("LỖI: Chế độ CLI yêu cầu đủ tham số --api-key, --start-date và --end-date.")
            sys.exit(1)
        run_cli(
            api_key=args.api_key,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir
        )
    else:
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                DESKTOP_ALL = 0x01FF
                h_default = user32.OpenDesktopW("Default", 0, False, DESKTOP_ALL)
                if h_default:
                    user32.SetThreadDesktop(h_default)
            except Exception:
                pass
        root = tk.Tk()
        app = AppGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
