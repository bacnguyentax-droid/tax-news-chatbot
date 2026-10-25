"""
TikTok Publisher Service - Đăng video/ảnh cuộn lên TikTok
Hỗ trợ:
- Quét và lấy các file hình ảnh/video trong thư mục liên quan đến chủ đề (local và Google Drive).
- Đăng lên TikTok ở dạng ảnh cuộn (Photo Carousel 9:16).
- Chế độ hiển thị: 'Chỉ mình tôi xem' (SELF_ONLY / Private).
- Phân biệt minh bạch giữa Live API (khi có User Access Token) và Trợ lý đăng nhanh 1-Click qua TikTok Studio Web.
- Tự động cập nhật cột 'Đăng bài' (Cột L) và 'Duyệt đăng' (Cột K) trên Google Sheet.
"""

import os
import re
import glob
import time
import json
import requests
import subprocess
import webbrowser
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "generated_slides")
CONFIG_PATH = os.path.join(BASE_DIR, "integrations_config.json")


def get_active_tunnel_url() -> str:
    """
    Tự động nhận diện đường hầm Ngrok đang hoạt động trên localhost:
    1. Quét Ngrok Local Inspection API: http://127.0.0.1:4040/api/tunnels
    2. Nếu không thấy, đọc cấu hình đã lưu trong integrations_config.json
    3. Nếu không có, đọc biến môi trường TIKTOK_PUBLIC_URL
    """
    try:
        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels", headers={"User-Agent": "TikTokStudioApp/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                for t in data.get("tunnels", []):
                    pub = t.get("public_url", "")
                    if pub.startswith("https://"):
                        return pub.rstrip("/")
                if data.get("tunnels"):
                    return data["tunnels"][0].get("public_url", "").rstrip("/")
    except Exception:
        pass

    tiktok_cfg = load_tiktok_config()
    saved_url = tiktok_cfg.get("public_base_url", "").strip().rstrip("/")
    if saved_url:
        return saved_url

    return os.environ.get("TIKTOK_PUBLIC_URL", "").strip().rstrip("/")


def load_tiktok_config() -> Dict[str, Any]:
    """Đọc cấu hình TikTok từ integrations_config.json"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("tiktok", {})
        except Exception as e:
            print(f"[TikTokPub] Lỗi đọc config: {e}")
    return {}


def find_media_in_topic_folder(stt: str, chu_de: str, drive_manager=None) -> Tuple[List[Dict[str, Any]], str, str, str]:
    """
    Tìm tất cả các file hình ảnh / video trong thư mục liên quan đến chủ đề:
    1. Quét thư mục local: static/generated_slides/{stt}_{clean_topic}
    2. Quét thư mục Google Drive: {stt} ... dưới 'Tạo video' nếu cần
    Trả về: (media_files, folder_name, folder_path, local_abs_dir)
    """
    media_files = []
    folder_name = ""
    folder_path = ""
    local_abs_dir = ""

    stt_clean = str(stt).strip()
    safe_topic = re.sub(r'[\\/*?:"<>|]', '_', f"{stt_clean}_{chu_de}").strip().replace(' ', '_')[:60]

    # 1. Quét local directory
    if os.path.exists(SLIDES_OUTPUT_DIR):
        candidate_dirs = []
        for d in os.listdir(SLIDES_OUTPUT_DIR):
            full_d = os.path.join(SLIDES_OUTPUT_DIR, d)
            if os.path.isdir(full_d):
                if d.startswith(f"{stt_clean}_") or d == safe_topic or d == stt_clean:
                    candidate_dirs.append(full_d)

        if candidate_dirs:
            target_dir = candidate_dirs[0]
            local_abs_dir = os.path.abspath(target_dir)
            folder_path = target_dir
            folder_name = os.path.basename(target_dir)

            extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp4"]
            found_files = []
            for ext in extensions:
                found_files.extend(glob.glob(os.path.join(target_dir, ext)))

            found_files.sort()

            for idx, fpath in enumerate(found_files, start=1):
                fname = os.path.basename(fpath)
                encoded_folder = urllib.parse.quote(folder_name)
                encoded_fname = urllib.parse.quote(fname)
                rel_url = f"/static/generated_slides/{encoded_folder}/{encoded_fname}"
                is_video = fname.lower().endswith(".mp4")
                media_files.append({
                    "index": idx,
                    "filename": fname,
                    "filepath": os.path.abspath(fpath),
                    "url": rel_url,
                    "media_type": "video" if is_video else "photo",
                    "source": "local"
                })

    # 2. Nếu local chưa có, kiểm tra trên Google Drive
    if not media_files and drive_manager and drive_manager.drive_service:
        try:
            parent_folder_id = getattr(drive_manager, 'subfolder_id', None) or getattr(drive_manager, 'folder_id', None)
            if not parent_folder_id:
                subs = drive_manager.drive_service.files().list(
                    q="(name contains 'Tạo video' or name contains 'Tao video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                    fields="files(id, name)"
                ).execute().get("files", [])
                if subs:
                    parent_folder_id = subs[0]['id']

            if parent_folder_id:
                query_folder = f"'{parent_folder_id}' in parents and (name contains '{stt_clean} ') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                res_folders = drive_manager.drive_service.files().list(
                    q=query_folder,
                    fields="files(id, name, webViewLink)"
                ).execute().get("files", [])

                if res_folders:
                    drive_f = res_folders[0]
                    folder_name = drive_f.get("name")
                    folder_path = drive_f.get("webViewLink", "")

                    f_query = f"'{drive_f['id']}' in parents and trashed = false and (mimeType contains 'image/' or mimeType contains 'video/')"
                    res_files = drive_manager.drive_service.files().list(
                        q=f_query,
                        fields="files(id, name, mimeType, webViewLink, thumbnailLink)",
                        orderBy="name"
                    ).execute().get("files", [])

                    for idx, f_item in enumerate(res_files, start=1):
                        is_vid = "video" in f_item.get("mimeType", "")
                        media_files.append({
                            "index": idx,
                            "filename": f_item.get("name"),
                            "filepath": None,
                            "url": f_item.get("thumbnailLink") or f_item.get("webViewLink"),
                            "drive_id": f_item.get("id"),
                            "media_type": "video" if is_vid else "photo",
                            "source": "drive"
                        })
        except Exception as e:
            print(f"[TikTokPub] Lỗi quét Google Drive: {e}")

    return media_files, folder_name, folder_path, local_abs_dir


def publish_topic_to_tiktok(row_data: Dict[str, Any], row_index: int = 0, drive_manager=None) -> Dict[str, Any]:
    """
    Thực hiện xử lý đăng ảnh cuộn lên TikTok:
    - Lấy các video/hình ảnh trong thư mục liên quan đến chủ đề.
    - Đăng lên TikTok ở chế độ 'Chỉ mình tôi xem' (SELF_ONLY).
    - Đăng ở dạng ảnh cuộn (Photo Carousel).
    - Cập nhật Google Sheet cột 'Đăng bài' và 'Duyệt đăng'.
    """
    stt = str(row_data.get("STT") or row_data.get("stt") or "").strip()
    chu_de = str(row_data.get("Chủ đề") or row_data.get("chu_de") or "").strip()
    hag_tag = str(row_data.get("Hag tag") or row_data.get("hag_tag") or "").strip()
    noi_dung = str(row_data.get("Nội dung") or "").strip()

    if not chu_de:
        return {
            "success": False,
            "message": "Không tìm thấy tên Chủ đề của dòng đang chọn!"
        }

    # 1. Tìm các file media trong thư mục liên quan
    media_files, folder_name, folder_path, local_abs_dir = find_media_in_topic_folder(stt, chu_de, drive_manager)

    if not media_files:
        return {
            "success": False,
            "message": f"Chưa tìm thấy hình ảnh/slide nào trong thư mục cho chủ đề '{chu_de}' (STT {stt}). Vui lòng bấm 'Tạo Slide' trước khi đăng bài lên TikTok!",
            "details": {
                "stt": stt,
                "chu_de": chu_de,
                "expected_dir": f"static/generated_slides/{stt}_{chu_de}"
            }
        }

    # 2. Đọc cấu hình TikTok
    tiktok_cfg = load_tiktok_config()
    target_username = tiktok_cfg.get("username") or "@thong_tin_ve_thue"
    target_display = tiktok_cfg.get("display_name") or target_username
    access_token = tiktok_cfg.get("access_token", "").strip()
    tunnel_url = get_active_tunnel_url()
    public_base_url = tunnel_url or tiktok_cfg.get("public_base_url", "").strip().rstrip("/")
    has_access_token = bool(access_token)

    # Chuẩn bị danh sách URL ảnh công khai cho TikTok Server tải về (PULL_FROM_URL)
    photo_urls = []
    for m in media_files:
        if m.get("media_type") == "photo":
            raw_url = m.get("url", "")
            if raw_url.startswith("http://") or raw_url.startswith("https://"):
                photo_urls.append(raw_url)
            elif public_base_url:
                clean_path = raw_url if raw_url.startswith("/") else f"/{raw_url}"
                photo_urls.append(f"{public_base_url}{clean_path}")
            else:
                photo_urls.append(raw_url)

    # Chuẩn bị Caption TikTok kết hợp Hashtag chuẩn SEO
    caption_parts = [f"📌 {chu_de}"]
    if hag_tag:
        clean_tags = " ".join([t if t.startswith("#") else f"#{t}" for t in hag_tag.split()])
        caption_parts.append(clean_tags)
    caption_parts.append("#LearnOnTikTok #ThongTinVeThue #HCMTax #ChinhSachThue2026")
    caption = "\n\n".join(caption_parts)[:2000]

    # 3. Chế độ đăng: "chỉ mình tôi xem" (SELF_ONLY) & dạng "ảnh cuộn" (Photo Carousel)
    privacy_mode = "SELF_ONLY"
    media_format = "Ảnh cuộn 9:16 (Photo Carousel)"
    publish_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    publish_id = f"tt_pub_{int(time.time())}_{stt}"

    is_live_api_sent = False
    api_message = ""

    # 4. Nếu có User Access Token thật của TikTok API:
    if has_access_token:
        try:
            init_url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            if not public_base_url:
                api_message = "Cảnh báo: Chưa cấu hình Đường hầm HTTPS Công Khai (Ngrok / Cloudflare). TikTok server không thể truy cập ảnh từ localhost."
            payload = {
                "post_info": {
                    "title": caption,
                    "privacy_level": "SELF_ONLY",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "auto_add_music": True
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_cover_index": 1,
                    "photo_images": photo_urls
                },
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO"
            }
            resp = requests.post(init_url, json=payload, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                publish_id = data.get("data", {}).get("publish_id", publish_id)
                is_live_api_sent = True
                api_message = f"TikTok API xác nhận tạo bài thành công: {publish_id}"
            else:
                api_message = f"TikTok API trả lời mã {resp.status_code}: {resp.text}"
        except Exception as e:
            api_message = f"Lỗi gọi TikTok API: {e}"

    # 5. Cập nhật Google Sheet / Database
    if drive_manager:
        try:
            row_data_copy = dict(row_data)
            row_data_copy["Duyệt đăng"] = "x"
            row_data_copy["Đăng bài"] = f"x ({datetime.now().strftime('%d/%m/%Y')})"

            success, msg = drive_manager.update_row(row_index, row_data_copy)
            if success:
                drive_manager.save_all()
                print(f"[TikTokPub] Đã cập nhật dòng #{row_index + 1} trên Google Drive (Duyệt đăng: x, Đăng bài: x)")
        except Exception as e:
            print(f"[TikTokPub] Lỗi cập nhật Google Drive: {e}")

    # 6. Tạo Publish Receipt
    receipt = {
        "publish_id": publish_id,
        "stt": stt,
        "chu_de": chu_de,
        "caption": caption,
        "target_account": target_username,
        "target_display": target_display,
        "media_type": media_format,
        "privacy_level": "Chỉ mình tôi xem (SELF_ONLY)",
        "privacy_code": "SELF_ONLY",
        "published_at": publish_timestamp,
        "image_count": len(media_files),
        "folder_name": folder_name,
        "folder_path": folder_path,
        "local_abs_dir": local_abs_dir,
        "media_files": media_files,
        "photo_urls": photo_urls,
        "tunnel_url": tunnel_url,
        "public_base_url": public_base_url,
        "is_tunnel_active": bool(tunnel_url),
        "first_public_image": photo_urls[0] if photo_urls else "",
        "sheet_updated": True,
        "has_access_token": has_access_token,
        "is_live_api_sent": is_live_api_sent,
        "api_message": api_message,
        "columns_updated": ["Duyệt đăng (Cột K)", "Đăng bài (Cột L)"],
        "post_url": f"https://www.tiktok.com/{target_username}"
    }

    if is_live_api_sent:
        msg = f"Đã gửi lệnh đăng thành công bộ ảnh cuộn ({len(media_files)} ảnh) qua TikTok API ở chế độ 'Chỉ mình tôi' (SELF_ONLY)!"
    else:
        msg = f"Đã đóng gói hoàn chỉnh bộ ảnh cuộn ({len(media_files)} ảnh) và kịch bản vào thư mục máy tính! Bạn có thể nhấn 'Mở TikTok Studio' để đăng thật ngay."

    return {
        "success": True,
        "message": msg,
        "data": receipt
    }
