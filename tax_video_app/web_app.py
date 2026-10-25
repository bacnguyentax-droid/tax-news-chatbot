import os
import sys
import json
import time
import queue
import datetime
import threading
import webbrowser
import subprocess
import re
import requests
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_EXCEL_PATH,
    DEFAULT_CHANNELS,
    DEFAULT_TAX_KEYWORDS,
    DEFAULT_YOUTUBE_API_KEY,
    DEFAULT_COOKIE_PATH,
    APP_DIR
)
from youtube_searcher import YouTubeSearcher
from transcript_analyzer import TranscriptAnalyzer
from downloader import VideoDownloader
from excel_logger import ExcelLogger

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

TIKTOK_CONFIG_PATH = os.path.join(APP_DIR, "tiktok_config.json")
DEFAULT_TIKTOK_HASHTAGS = (
    "#Cucthue #ThueTPHCM #ruirothue #thanhtrathue #canhbaothue #phapluatthue #quanlyruiro "
    "#Thongtinvethue #ketoanthue #chudoanhnghiep #kinhdoanh #ketoan #quantridoanhnghiep "
    "#LearnOnTikTok #xuhuong #edutok #chiasekienthuc #viralvideotiktok #viraltiktok "
    "#TNCN #Thunhapcanhan #Giamkhautru #Nguoiphuthuoc #Giamtrugiacanh #Tienluongtiencong"
)

def load_tiktok_config():
    if os.path.exists(TIKTOK_CONFIG_PATH):
        try:
            with open(TIKTOK_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data.get("hashtags"):
                    data["hashtags"] = DEFAULT_TIKTOK_HASHTAGS
                return data
        except Exception:
            pass
    return {
        "hashtags": DEFAULT_TIKTOK_HASHTAGS,
        "tiktok_api": {
            "auth_method": "api",
            "client_key": "",
            "client_secret": "",
            "access_token": "",
            "session_id": "",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
            "auto_add_music": False
        }
    }

def save_tiktok_config(cfg):
    with open(TIKTOK_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# Global State
state = {
    "api_key": DEFAULT_YOUTUBE_API_KEY,
    "output_dir": DEFAULT_OUTPUT_DIR,
    "keywords": DEFAULT_TAX_KEYWORDS,
    "channels": DEFAULT_CHANNELS,
    "stage1_results": [],
    "is_processing_stage1": False,
    "is_processing_stage2": False,
    "current_downloader": None
}

log_queue = queue.Queue(maxsize=1000)

def push_log(message: str, level: str = "INFO"):
    """Đẩy nhật ký vào hàng đợi phục vụ Server-Sent Events (SSE) thời gian thực."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    item = {
        "time": timestamp,
        "level": level.upper(),
        "message": message
    }
    try:
        log_queue.put_nowait(item)
    except queue.Full:
        try:
            log_queue.get_nowait()
            log_queue.put_nowait(item)
        except Exception:
            pass

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/config", methods=["GET"])
def get_config():
    has_cookies = os.path.exists(DEFAULT_COOKIE_PATH) and os.path.getsize(DEFAULT_COOKIE_PATH) > 0
    return jsonify({
        "api_key": state["api_key"],
        "output_dir": state["output_dir"],
        "keywords": ", ".join(state["keywords"]),
        "channels": state["channels"],
        "has_cookies": has_cookies,
        "is_processing_stage1": state["is_processing_stage1"],
        "is_processing_stage2": state["is_processing_stage2"]
    })

@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.json or {}
    if "api_key" in data:
        state["api_key"] = data["api_key"].strip()
    if "output_dir" in data:
        out_dir = data["output_dir"].strip()
        state["output_dir"] = out_dir
        os.makedirs(out_dir, exist_ok=True)
    if "keywords" in data:
        kw_str = data["keywords"]
        state["keywords"] = [k.strip() for k in kw_str.split(",") if k.strip()]
    return jsonify({"status": "success", "message": "Đã cập nhật cấu hình."})

@app.route("/api/cookies/upload", methods=["POST"])
def upload_cookies():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Không tìm thấy file tải lên."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Chưa chọn file."}), 400
    try:
        os.makedirs(os.path.dirname(DEFAULT_COOKIE_PATH), exist_ok=True)
        file.save(DEFAULT_COOKIE_PATH)
        push_log(f"[COOKIES] Nạp thành công file cookies: '{file.filename}' -> Đã lưu vào {DEFAULT_COOKIE_PATH}!", level="SUCCESS")
        return jsonify({"status": "success", "message": "Đã nạp file cookies.txt thành công!"})
    except Exception as e:
        push_log(f"[LỖI NẠP COOKIES] {e}", level="ERROR")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/logs/stream")
def stream_logs():
    def event_stream():
        # Gửi log mở đầu
        init_data = json.dumps({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": "INFO",
            "message": "Đã kết nối luồng nhật ký thời gian thực (SSE)."
        })
        yield f"data: {init_data}\n\n"
        while True:
            try:
                item = log_queue.get(timeout=25.0)
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            except queue.Empty:
                # Keep-alive heartbeat ping
                yield ": ping\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/stage1/search", methods=["POST"])
def stage1_search():
    if state["is_processing_stage1"] or state["is_processing_stage2"]:
        return jsonify({"status": "error", "message": "Tiến trình khác đang chạy, vui lòng chờ."}), 400

    data = request.json or {}
    start_date = data.get("start_date", "").strip()
    end_date = data.get("end_date", "").strip()
    selected_channel_ids = data.get("channel_ids", [])
    custom_keywords = data.get("keywords", [])

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Vui lòng chọn từ ngày và đến ngày."}), 400

    channels = [c for c in state["channels"] if c["id"] in selected_channel_ids] if selected_channel_ids else state["channels"]
    keywords = custom_keywords if custom_keywords else state["keywords"]

    def _worker():
        state["is_processing_stage1"] = True
        try:
            ch_names = ", ".join([c["name"] for c in channels])
            push_log(f"[GIAI ĐOẠN 1 START] Quét {len(channels)} kênh [{ch_names}] từ {start_date} đến {end_date}...", level="INFO")
            searcher = YouTubeSearcher(api_key=state["api_key"])
            videos = searcher.search_multi_channels(
                start_date=start_date,
                end_date=end_date,
                channels=channels,
                tax_keywords=keywords,
                filter_by_metadata=True
            )
            # Chuẩn bị dữ liệu hiển thị
            for idx, vid in enumerate(videos, 1):
                clean_topic = vid["title"].split("|")[0].split("-")[0].strip()
                vid["overlay_text"] = clean_topic
                vid["selected"] = False
                vid["stt"] = idx

            state["stage1_results"] = videos
            if not videos:
                push_log("[GIAI ĐOẠN 1] Không tìm thấy video nào có Tiêu đề / Mô tả khớp từ khóa.", level="WARNING")
            else:
                push_log(f"[GIAI ĐOẠN 1 COMPLETE] Đã quét xong! Tìm thấy {len(videos)} video khớp từ khóa.", level="SUCCESS")
        except Exception as e:
            push_log(f"[GIAI ĐOẠN 1 LỖI] {e}", level="ERROR")
        finally:
            state["is_processing_stage1"] = False

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return jsonify({"status": "started", "message": "Đang quét tìm kiếm video..."})

@app.route("/api/stage1/results", methods=["GET"])
def stage1_results():
    return jsonify({
        "videos": state["stage1_results"],
        "is_searching": state["is_processing_stage1"]
    })

@app.route("/api/stage1/update-item", methods=["POST"])
def stage1_update_item():
    data = request.json or {}
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"status": "error", "message": "Thiếu video_id"}), 400

    for vid in state["stage1_results"]:
        if vid["video_id"] == video_id:
            if "selected" in data:
                vid["selected"] = bool(data["selected"])
            if "overlay_text" in data:
                vid["overlay_text"] = str(data["overlay_text"]).strip()
                push_log(f"Đã cập nhật chữ Overlay 9:16 cho video '{vid['title'][:30]}...': '{vid['overlay_text']}'", level="SUCCESS")
            return jsonify({"status": "success", "video": vid})

    return jsonify({"status": "error", "message": "Không tìm thấy video."}), 404

@app.route("/api/stage1/select-all", methods=["POST"])
def stage1_select_all():
    data = request.json or {}
    select_state = bool(data.get("selected", True))
    for vid in state["stage1_results"]:
        vid["selected"] = select_state
    return jsonify({"status": "success", "count": len(state["stage1_results"]), "selected": select_state})

@app.route("/api/stage2/process", methods=["POST"])
def stage2_process():
    if state["is_processing_stage2"]:
        return jsonify({"status": "error", "message": "Tiến trình Giai đoạn 2 đang chạy."}), 400

    data = request.json or {}
    selected_videos = data.get("videos")

    # Nếu không gửi danh sách, lấy từ state
    if not selected_videos:
        selected_videos = [v for v in state["stage1_results"] if v.get("selected")]

    if not selected_videos:
        return jsonify({"status": "error", "message": "Vui lòng chọn ít nhất 1 video để xử lý."}), 400

    output_dir = state["output_dir"]
    keywords = state["keywords"]

    def _worker():
        state["is_processing_stage2"] = True
        try:
            push_log(f"[GIAI ĐOẠN 2 START] Bóc tách phụ đề & kết xuất video 9:16 cho {len(selected_videos)} video đã chọn...", level="INFO")
            analyzer = TranscriptAnalyzer(keywords=keywords)
            downloader = VideoDownloader(output_dir=output_dir)
            state["current_downloader"] = downloader
            excel_path = os.path.join(output_dir, "Danh_Sach_Video_Thue.xlsx")
            logger = ExcelLogger(excel_path=excel_path)

            total_downloaded = 0
            used_filenames = set()

            for idx, vid in enumerate(selected_videos, 1):
                if not state["is_processing_stage2"]:
                    push_log("Người dùng đã hủy quy trình xử lý Giai đoạn 2.", level="WARNING")
                    break

                v_title = vid["title"]
                v_id = vid["video_id"]
                v_url = vid["url"]
                v_desc = vid.get("description", "")
                overlay_text = vid.get("overlay_text", "")

                # Đặt tên file chính là nội dung ở Cột 5 (overlay_text)
                col5_text = overlay_text or v_title
                clean_col5 = downloader.sanitize_filename(col5_text)
                base_clean = clean_col5
                filename = f"{base_clean}.mp4"

                # Tự động chống trùng tên ghi đè file
                counter = 1
                while filename.lower() in used_filenames:
                    counter += 1
                    filename = f"{base_clean}_{counter}.mp4"
                used_filenames.add(filename.lower())

                display_name = os.path.splitext(filename)[0]
                push_log(f"[{idx}/{len(selected_videos)}] Bắt đầu xử lý video '{display_name}'...", level="INFO")

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
                        progress_callback=lambda msg: push_log(msg, level="INFO")
                    )

                    goc_path = res.get("goc_path", "")
                    cut_path = res.get("cut_path", "")
                    goc_name = os.path.basename(goc_path)
                    cut_name = os.path.basename(cut_path)

                    push_log(f"-> [THÀNH CÔNG GỐC] Đã lưu video gốc: {goc_name}", level="SUCCESS")
                    push_log(f"-> [THÀNH CÔNG 9:16] Đã dựng ghép banner & chữ 52 BOLD: {cut_name}", level="SUCCESS")

                    # Ghi Excel log
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
                    push_log(f"-> Lỗi khi tải/dựng video '{display_name}': {err}", level="ERROR")

            push_log(f"[GIAI ĐOẠN 2 COMPLETE] Hoàn thành! Đã lưu thành công {total_downloaded} bộ video tại {output_dir}", level="SUCCESS")

        except Exception as e:
            push_log(f"[GIAI ĐOẠN 2 LỖI] {e}", level="ERROR")
        finally:
            state["is_processing_stage2"] = False
            state["current_downloader"] = None

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return jsonify({"status": "started", "message": f"Đã bắt đầu xử lý {len(selected_videos)} video."})

@app.route("/api/stage2/stop", methods=["POST"])
def stage2_stop():
    state["is_processing_stage2"] = False
    if state["current_downloader"]:
        try:
            state["current_downloader"].abort()
        except Exception:
            pass
    push_log("Đã phát lệnh dừng tiến trình xử lý từ giao diện Web...", level="WARNING")
    return jsonify({"status": "stopped", "message": "Đã gửi lệnh dừng tiến trình."})

@app.route("/api/files", methods=["GET"])
def list_output_files():
    out_dir = state["output_dir"]
    if not os.path.exists(out_dir):
        return jsonify({"files": [], "excel_exists": False})

    files = []
    excel_exists = False
    try:
        for entry in os.scandir(out_dir):
            if entry.is_file():
                name = entry.name
                if name.lower().endswith((".mp4", ".xlsx")):
                    stat = entry.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
                    is_excel = name.lower().endswith(".xlsx")
                    if is_excel:
                        excel_exists = True
                    is_goc = "_gốc.mp4" in name.lower()
                    files.append({
                        "name": name,
                        "size_mb": round(size_mb, 2),
                        "modified": mod_time,
                        "is_excel": is_excel,
                        "is_goc": is_goc,
                        "is_cut": (not is_excel and not is_goc),
                        "timestamp": stat.st_mtime
                    })
        files.sort(key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        push_log(f"[LỖI ĐỌC THƯ MỤC] {e}", level="ERROR")

    return jsonify({"files": files, "output_dir": out_dir, "excel_exists": excel_exists})

@app.route("/api/download/<path:filename>")
def download_file(filename):
    return send_from_directory(state["output_dir"], filename, as_attachment=True)

@app.route("/api/preview/<path:filename>")
def preview_file(filename):
    return send_from_directory(state["output_dir"], filename)

@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    out_dir = state["output_dir"]
    try:
        if sys.platform == "win32":
            os.startfile(out_dir)
        else:
            subprocess.run(["xdg-open", out_dir])
        return jsonify({"status": "success", "message": f"Đã mở thư mục {out_dir}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ----------------- TIKTOK & VIDEO EDITING APIs -----------------

@app.route("/api/tiktok/config", methods=["GET"])
def get_tiktok_config():
    cfg = load_tiktok_config()
    return jsonify(cfg)

@app.route("/api/tiktok/config", methods=["POST"])
def update_tiktok_config():
    data = request.json or {}
    cfg = load_tiktok_config()
    if "hashtags" in data:
        cfg["hashtags"] = data["hashtags"].strip()
    if "tiktok_api" in data and isinstance(data["tiktok_api"], dict):
        cfg["tiktok_api"].update(data["tiktok_api"])
    save_tiktok_config(cfg)
    push_log("Đã cập nhật & lưu cấu hình TikTok và Hashtag thành công!", level="SUCCESS")
    return jsonify({"status": "success", "message": "Đã lưu cấu hình TikTok & Hashtag."})

@app.route("/api/tiktok/test", methods=["POST"])
def test_tiktok_connection():
    cfg = load_tiktok_config()
    token = cfg.get("tiktok_api", {}).get("access_token", "").strip()
    if not token:
        return jsonify({"status": "error", "message": "Chưa nhập Access Token TikTok. Vui lòng nhập token trong Tab Cấu hình trước khi kiểm tra."}), 400
    try:
        url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, timeout=10)
        res_data = resp.json()
        if res_data.get("error", {}).get("code") == "ok":
            user_info = res_data.get("data", {}).get("user", {})
            d_name = user_info.get("display_name", "TikTok User")
            push_log(f"[TIKTOK TEST] Kết nối tài khoản thành công: {d_name}", level="SUCCESS")
            return jsonify({"status": "success", "message": f"Kết nối TikTok thành công! Tài khoản: {d_name}", "user": user_info})
        else:
            err_msg = res_data.get("error", {}).get("message", "Token không hợp lệ hoặc đã hết hạn.")
            push_log(f"[TIKTOK TEST LỖI] {err_msg}", level="ERROR")
            return jsonify({"status": "error", "message": f"Lỗi TikTok API: {err_msg}"}), 400
    except Exception as e:
        push_log(f"[TIKTOK TEST LỖI] {e}", level="ERROR")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/video/info", methods=["GET"])
def get_video_info():
    filename = request.args.get("filename", "").strip()
    if not filename:
        return jsonify({"status": "error", "message": "Thiếu filename"}), 400
    video_path = os.path.join(state["output_dir"], filename)
    if not os.path.exists(video_path):
        return jsonify({"status": "error", "message": "File không tồn tại"}), 404
    try:
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", video_path]
        res = subprocess.run(dur_cmd, capture_output=True, text=True, check=True)
        info = json.loads(res.stdout)
        duration = float(info.get("format", {}).get("duration", 0))
        size = int(info.get("format", {}).get("size", os.path.getsize(video_path)))
        return jsonify({
            "status": "success",
            "filename": filename,
            "duration": round(duration, 2),
            "size_mb": round(size / (1024 * 1024), 2)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/video/edit", methods=["POST"])
def edit_video():
    data = request.json or {}
    filename = data.get("filename", "").strip()
    try:
        start_time = float(data.get("start_time", 0))
    except (ValueError, TypeError):
        start_time = 0.0

    try:
        end_time = float(data.get("end_time", 0))
    except (ValueError, TypeError):
        end_time = 0.0

    try:
        volume_percent = int(data.get("volume_percent", 100))
    except (ValueError, TypeError):
        volume_percent = 100

    if not filename:
        return jsonify({"status": "error", "message": "Chưa chọn file video để chỉnh sửa."}), 400

    input_path = os.path.join(state["output_dir"], filename)
    if not os.path.exists(input_path):
        return jsonify({"status": "error", "message": f"Không tìm thấy file: {filename}"}), 404

    if end_time > 0 and end_time <= start_time:
        return jsonify({"status": "error", "message": "Thời gian kết thúc phải lớn hơn thời gian bắt đầu."}), 400

    if start_time < 0:
        start_time = 0.0

    base_name, ext = os.path.splitext(filename)
    clean_base = re.sub(r'_edited(_\d+)?$', '', base_name)
    timestamp_str = datetime.datetime.now().strftime("%H%M%S")
    out_filename = f"{clean_base}_edited_{timestamp_str}{ext}"
    output_path = os.path.join(state["output_dir"], out_filename)

    volume_factor = max(0.0, volume_percent / 100.0)
    push_log(f"[CHỈNH SỬA VIDEO] Bắt đầu cắt & chỉnh âm lượng cho '{filename}'...", level="INFO")
    cut_desc = f"Từ {start_time:.1f}s đến {'Hết video' if end_time <= 0 else f'{end_time:.1f}s'}"
    push_log(f"-> Mốc cắt: {cut_desc} | Âm lượng: {volume_percent}%", level="INFO")

    cmd = ["ffmpeg", "-y"]
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    if end_time > start_time:
        cmd.extend(["-to", str(end_time)])
    cmd.extend(["-i", input_path])
    cmd.extend(["-filter:a", f"volume={volume_factor}"])
    cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "aac", "-b:a", "192k", output_path])

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        new_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)
        push_log(f"-> [THÀNH CÔNG] Đã xuất video chỉnh sửa: '{out_filename}' ({new_size_mb} MB)!", level="SUCCESS")
        return jsonify({
            "status": "success",
            "message": "Đã cắt video và chỉnh âm lượng thành công!",
            "filename": out_filename,
            "size_mb": new_size_mb
        })
    except subprocess.CalledProcessError as err:
        push_log(f"[LỖI FFMPEG] {err.stderr[-300:]}", level="ERROR")
        return jsonify({"status": "error", "message": f"Lỗi FFmpeg: {err.stderr[-300:]}"}), 500
    except Exception as e:
        push_log(f"[LỖI XỬ LÝ VIDEO] {e}", level="ERROR")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tiktok/post", methods=["POST"])
def post_tiktok():
    data = request.json or {}
    filename = data.get("filename", "").strip()
    caption = data.get("caption", "").strip()
    hashtags = data.get("hashtags", "").strip()

    if not filename:
        return jsonify({"status": "error", "message": "Chưa chọn video để đăng."}), 400

    video_path = os.path.join(state["output_dir"], filename)
    if not os.path.exists(video_path):
        return jsonify({"status": "error", "message": f"Không tìm thấy file: {filename}"}), 404

    cfg = load_tiktok_config()
    tiktok_api = cfg.get("tiktok_api", {})
    token = tiktok_api.get("access_token", "").strip()
    privacy_level = tiktok_api.get("privacy_level", "PUBLIC_TO_EVERYONE")
    disable_duet = bool(tiktok_api.get("disable_duet", False))
    disable_stitch = bool(tiktok_api.get("disable_stitch", False))
    disable_comment = bool(tiktok_api.get("disable_comment", False))

    post_title = f"{caption}\n\n{hashtags}".strip()
    file_size = os.path.getsize(video_path)

    push_log(f"[TIKTOK] Bắt đầu đăng video '{filename}' lên TikTok...", level="INFO")
    push_log(f"-> Tiêu đề: {caption[:60]}...", level="INFO")
    push_log(f"-> Hashtags: {hashtags[:60]}...", level="INFO")

    if not token:
        msg = "Chưa cấu hình Access Token TikTok trong Tab Cấu Hình! Vui lòng mở Tab 'Cấu hình' để nhập Access Token từ TikTok Developer."
        push_log(f"[TIKTOK CHƯA CẤU HÌNH] {msg}", level="WARNING")
        return jsonify({
            "status": "warning",
            "message": msg,
            "requires_config": True
        }), 400

    try:
        # 1. Khởi tạo phiên tải lên với TikTok Content Posting API v2
        init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        init_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        init_payload = {
            "post_info": {
                "title": post_title[:2200],
                "privacy_level": privacy_level,
                "disable_duet": disable_duet,
                "disable_stitch": disable_stitch,
                "disable_comment": disable_comment,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
        push_log("[TIKTOK API] Đang gửi yêu cầu khởi tạo đăng video...", level="INFO")
        resp = requests.post(init_url, headers=init_headers, json=init_payload, timeout=20)
        res_data = resp.json()

        if res_data.get("error", {}).get("code") != "ok":
            err_msg = res_data.get("error", {}).get("message", "Lỗi khởi tạo đăng từ TikTok API.")
            push_log(f"[TIKTOK API LỖI] {err_msg}", level="ERROR")
            return jsonify({"status": "error", "message": f"TikTok API Error: {err_msg}"}), 400

        publish_id = res_data.get("data", {}).get("publish_id")
        upload_url = res_data.get("data", {}).get("upload_url")

        push_log(f"[TIKTOK API] Được cấp Publish ID: {publish_id}. Đang truyền tệp video ({round(file_size/(1024*1024), 2)} MB)...", level="INFO")

        # 2. Upload video binary lên upload_url
        with open(video_path, "rb") as vf:
            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
            }
            upload_resp = requests.put(upload_url, headers=upload_headers, data=vf, timeout=120)

        if upload_resp.status_code in (200, 201, 204):
            push_log(f"[TIKTOK THÀNH CÔNG] Đã đăng video '{filename}' lên TikTok thành công!", level="SUCCESS")
            push_log(f"-> Publish ID: {publish_id} (Trạng thái: Đang phát hành)", level="SUCCESS")
            return jsonify({
                "status": "success",
                "message": f"Đã đăng video '{filename}' lên TikTok thành công! Publish ID: {publish_id}",
                "publish_id": publish_id
            })
        else:
            push_log(f"[TIKTOK UPLOAD LỖI] Mã phản hồi: {upload_resp.status_code} - {upload_resp.text}", level="ERROR")
            return jsonify({"status": "error", "message": f"Lỗi upload video TikTok: {upload_resp.text}"}), 500

    except Exception as e:
        push_log(f"[TIKTOK LỖI ĐĂNG BÀI] {e}", level="ERROR")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = 5050
    print("=" * 60)
    print(" ỨNG DỤNG WEB: TỰ ĐỘNG TÌM KIẾM & KẾT XUẤT VIDEO THUẾ 9:16")
    print(f" Địa chỉ Web: http://localhost:{port}")
    print("=" * 60)
    # Tự động mở trình duyệt web sau 1.2 giây
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False)
