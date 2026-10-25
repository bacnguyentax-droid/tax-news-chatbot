import os
import sys
import json
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response
import io
import zipfile
from flask_cors import CORS

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(CURRENT_DIR, "templates"),
    static_folder=os.path.join(CURRENT_DIR, "static")
)
CORS(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True

import time
from drive_service import GoogleDriveManager, CREDENTIALS_FILE
from slide_generator_service import load_presets, save_presets, get_preset_by_id, generate_and_upload_slides
from tiktok_publisher_service import publish_topic_to_tiktok

drive_manager = GoogleDriveManager()


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['ngrok-skip-browser-warning'] = 'true'
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=86400'
    else:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response


@app.route("/<filename>")
def serve_root_tiktok_verification(filename):
    f_lower = filename.lower()
    if f_lower.startswith("tiktok") and f_lower.endswith(".txt"):
        verify_path = os.path.join(CURRENT_DIR, filename)
        if os.path.exists(verify_path):
            with open(verify_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        else:
            token = filename[6:-4]
            content = f"tiktok-developers-site-verification={token}"
        
        resp = Response(content, mimetype="text/plain; charset=utf-8")
        resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['ngrok-skip-browser-warning'] = 'true'
        return resp
    return "Not Found", 404


@app.route("/terms")
@app.route("/terms-of-service")
def terms_of_service():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Terms of Service - TikTok Automation Studio</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #111; border-bottom: 2px solid #eee; padding-bottom: 12px; }
        h2 { color: #222; margin-top: 28px; }
        p { color: #555; }
    </style>
</head>
<body>
    <h1>Terms of Service</h1>
    <p>Last updated: October 2026</p>
    <h2>1. Acceptance of Terms</h2>
    <p>By using TikTok Automation Studio ("the Application"), you agree to abide by these Terms of Service and comply with all applicable TikTok Developer Guidelines and Terms of Service.</p>
    <h2>2. Purpose of the Application</h2>
    <p>The Application is designed for content creators and educational tax policy publishers to create, draft, and schedule educational photo carousels and infographics on TikTok.</p>
    <h2>3. User Responsibilities</h2>
    <p>Users are responsible for ensuring that all content uploaded and published via the Application complies with TikTok's Community Guidelines. No spam, misleading, or unauthorized content may be published.</p>
    <h2>4. Intellectual Property</h2>
    <p>All content created by users remains their property. The Application does not claim ownership over any user-created materials.</p>
    <h2>5. Contact Us</h2>
    <p>If you have any questions regarding these Terms, please contact us at bacnguyentax@gmail.com.</p>
</body>
</html>'''


@app.route("/privacy")
@app.route("/privacy-policy")
def privacy_policy():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Privacy Policy - TikTok Automation Studio</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #111; border-bottom: 2px solid #eee; padding-bottom: 12px; }
        h2 { color: #222; margin-top: 28px; }
        p { color: #555; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p>Last updated: October 2026</p>
    <h2>1. Information We Collect</h2>
    <p>TikTok Automation Studio only collects the minimum data required to facilitate content publishing via TikTok Content Posting API. When authorized, we access your basic public profile (display name, username, avatar) to confirm the target channel.</p>
    <h2>2. How We Use Information</h2>
    <p>Information is used exclusively to display connected channel identity in the local dashboard and dispatch educational photo carousel posts to TikTok with your explicit consent.</p>
    <h2>3. Data Protection and Storage</h2>
    <p>Your authentication tokens are stored locally on your secure server and are never shared with or sold to third parties. We do not track or store your personal browsing activity.</p>
    <h2>4. Data Deletion</h2>
    <p>Users may revoke authorization at any time through their TikTok account settings or by disconnecting within the Application settings, which deletes all local access tokens immediately.</p>
    <h2>5. Contact Information</h2>
    <p>For any privacy inquiries or data requests, please contact us at bacnguyentax@gmail.com.</p>
</body>
</html>'''


@app.route("/")
def index():
    return render_template("index.html", version=int(time.time()))


@app.route("/api/status", methods=["GET"])
def get_status():
    status = drive_manager.get_status()
    return jsonify(status)


@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify({
        "success": True,
        "columns": drive_manager.columns,
        "rows": drive_manager.current_data,
        "total": len(drive_manager.current_data),
        "file_name": drive_manager.file_name,
        "file_type": drive_manager.file_type,
        "is_connected": drive_manager.is_connected,
        "message": drive_manager.connection_message
    })


@app.route("/api/row/update", methods=["POST"])
def update_row():
    data = request.json or {}
    row_index = data.get("index")
    updated_fields = data.get("fields", {})

    if row_index is None:
        return jsonify({"success": False, "message": "Thiếu số thứ tự dòng (index)"}), 400

    try:
        row_index = int(row_index)
        success, message = drive_manager.update_row(row_index, updated_fields)
        return jsonify({
            "success": success,
            "message": message,
            "row": drive_manager.current_data[row_index] if success else None
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi xử lý: {str(e)}"}), 500


@app.route("/api/row/add", methods=["POST"])
def add_row():
    data = request.json or {}
    new_fields = data.get("fields", {})
    try:
        success, message = drive_manager.add_row(new_fields)
        return jsonify({
            "success": success,
            "message": message,
            "total_rows": len(drive_manager.current_data)
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi: {str(e)}"}), 500


@app.route("/api/row/delete", methods=["POST"])
def delete_row():
    data = request.json or {}
    row_index = data.get("index")
    if row_index is None:
        return jsonify({"success": False, "message": "Thiếu index dòng cần xóa"}), 400
    try:
        success, message = drive_manager.delete_row(int(row_index))
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/credentials/upload", methods=["POST"])
def upload_credentials():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file tải lên"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "Chưa chọn file"}), 400

    try:
        file.save(CREDENTIALS_FILE)
        return jsonify({
            "success": True,
            "message": "Đã lưu file credentials.json thành công! Bây giờ bạn có thể bấm 'Đăng nhập Google Drive'."
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi lưu file: {str(e)}"}), 500


@app.route("/api/auth/start", methods=["POST"])
def start_auth():
    success, result = drive_manager.start_oauth_flow()
    if not success:
        return jsonify({
            "success": False,
            "message": result
        }), 400

    return jsonify({
        "success": True,
        "auth_url": result,
        "message": "Đang mở cửa sổ đăng nhập Google trên trình duyệt..."
    })


@app.route("/api/create_drive_structure", methods=["POST"])
def create_drive_structure():
    success, message = drive_manager.create_drive_structure()
    return jsonify({"success": success, "message": message})


@app.route("/api/reload", methods=["POST"])
def reload_drive():
    if drive_manager.is_connected:
        drive_manager.locate_file_and_load()
    else:
        drive_manager.init_connection()
    return jsonify({
        "success": True,
        "message": drive_manager.connection_message,
        "status": drive_manager.get_status()
    })


@app.route("/api/ai/config", methods=["GET"])
def get_ai_config():
    from gemini_content_service import get_gemini_config
    cfg = get_gemini_config()
    raw_key = cfg.get("api_key", "")
    masked_key = (raw_key[:4] + "..." + raw_key[-4:]) if len(raw_key) > 8 else ("Đã cấu hình" if raw_key else "Chưa cấu hình")
    return jsonify({
        "success": True,
        "config": cfg,
        "is_configured": bool(raw_key),
        "has_api_key": bool(raw_key),
        "masked_key": masked_key,
        "api_key_preview": masked_key,
        "api_key": raw_key,
        "model": cfg.get("model", "gemini-2.5-flash"),
        "notebooklm_name": cfg.get("notebooklm_name", "Tax_Nghiệp vụ thuế"),
        "enable_web_search": cfg.get("enable_web_search", True),
        "custom_tax_knowledge": cfg.get("custom_tax_knowledge", "")
    })


@app.route("/api/ai/config", methods=["POST"])
def update_ai_config():
    from gemini_content_service import save_gemini_config
    data = request.json or {}
    success, message = save_gemini_config(data)
    return jsonify({"success": success, "message": message})


@app.route("/api/integrations/status", methods=["GET"])
def get_all_integrations_status():
    from gemini_content_service import get_gemini_config
    from integrations_service import load_integrations_config, mask_key

    # 1. Google Drive
    drive_conn = drive_manager.is_connected
    drive_info = {
        "is_connected": drive_conn,
        "user_email": drive_manager.user_email or "",
        "folder_name": "_____Xây dựng video_____",
        "subfolder_name": "Tạo video",
        "file_name": drive_manager.file_name or "Thông tin",
        "has_credentials": os.path.exists(CREDENTIALS_FILE)
    }

    # 2. Gemini & NotebookLM
    gemini_cfg = get_gemini_config()
    gemini_key = gemini_cfg.get("api_key", "").strip()
    gemini_conn = bool(gemini_key)
    gemini_info = {
        "is_connected": gemini_conn,
        "api_key": gemini_key,
        "api_key_preview": mask_key(gemini_key),
        "model": gemini_cfg.get("model", "gemini-2.5-flash"),
        "notebooklm_name": gemini_cfg.get("notebooklm_name", "Tax_Nghiệp vụ thuế"),
        "enable_web_search": gemini_cfg.get("enable_web_search", True),
        "custom_tax_knowledge": gemini_cfg.get("custom_tax_knowledge", "")
    }

    # 3, 4, 5. Telegram, Heygen, Elevenlabs
    integ_cfg = load_integrations_config()

    tg_data = integ_cfg.get("telegram", {})
    tg_token = tg_data.get("bot_token", "").strip()
    tg_info = {
        "is_connected": bool(tg_data.get("is_connected") and tg_token),
        "bot_token": tg_token,
        "bot_token_preview": mask_key(tg_token),
        "chat_id": tg_data.get("chat_id", ""),
        "bot_name": tg_data.get("bot_name", ""),
        "last_tested": tg_data.get("last_tested")
    }

    heygen_data = integ_cfg.get("heygen", {})
    heygen_key = heygen_data.get("api_key", "").strip()
    heygen_info = {
        "is_connected": bool(heygen_data.get("is_connected") and heygen_key),
        "api_key": heygen_key,
        "api_key_preview": mask_key(heygen_key),
        "avatar_id": heygen_data.get("avatar_id", ""),
        "voice_id": heygen_data.get("voice_id", ""),
        "last_tested": heygen_data.get("last_tested")
    }

    eleven_data = integ_cfg.get("elevenlabs", {})
    eleven_key = eleven_data.get("api_key", "").strip()
    eleven_info = {
        "is_connected": bool(eleven_data.get("is_connected") and eleven_key),
        "api_key": eleven_key,
        "api_key_preview": mask_key(eleven_key),
        "voice_id": eleven_data.get("voice_id", ""),
        "model_id": eleven_data.get("model_id", "eleven_multilingual_v2"),
        "last_tested": eleven_data.get("last_tested")
    }

    tiktok_data = integ_cfg.get("tiktok", {})
    tiktok_token = tiktok_data.get("access_token", "").strip()
    tiktok_username = tiktok_data.get("username", "").strip()
    tiktok_info = {
        "is_connected": bool(tiktok_data.get("is_connected") and (tiktok_token or tiktok_username)),
        "access_token": tiktok_token,
        "access_token_preview": mask_key(tiktok_token),
        "username": tiktok_username,
        "client_key": tiktok_data.get("client_key", ""),
        "client_secret": tiktok_data.get("client_secret", ""),
        "public_base_url": tiktok_data.get("public_base_url", ""),
        "display_name": tiktok_data.get("display_name", ""),
        "privacy_level": tiktok_data.get("privacy_level", "PUBLIC_TO_EVERYONE"),
        "last_tested": tiktok_data.get("last_tested")
    }

    total_connected = sum([
        1 if drive_info["is_connected"] else 0,
        1 if gemini_info["is_connected"] else 0,
        1 if tg_info["is_connected"] else 0,
        1 if heygen_info["is_connected"] else 0,
        1 if eleven_info["is_connected"] else 0,
        1 if tiktok_info["is_connected"] else 0
    ])

    return jsonify({
        "success": True,
        "connected_count": total_connected,
        "total_count": 6,
        "integrations": {
            "google_drive": drive_info,
            "gemini": gemini_info,
            "telegram": tg_info,
            "heygen": heygen_info,
            "elevenlabs": eleven_info,
            "tiktok": tiktok_info
        }
    })


@app.route("/api/integrations/save", methods=["POST"])
def save_platform_integration():
    from integrations_service import save_integrations_config
    from gemini_content_service import save_gemini_config

    data = request.json or {}
    platform = data.get("platform", "")
    fields = data.get("fields", {})

    if platform == "gemini":
        success, msg = save_gemini_config(fields)
        return jsonify({"success": success, "message": msg})
    elif platform in ["telegram", "heygen", "elevenlabs", "tiktok"]:
        success, msg = save_integrations_config({platform: fields})
        return jsonify({"success": success, "message": msg})
    else:
        return jsonify({"success": False, "message": f"Nền tảng '{platform}' không hợp lệ."}), 400


@app.route("/api/integrations/test", methods=["POST"])
def test_platform_integration():
    from integrations_service import (
        test_telegram_connection,
        test_heygen_connection,
        test_elevenlabs_connection,
        test_gemini_connection,
        test_tiktok_connection
    )

    data = request.json or {}
    platform = data.get("platform", "")
    fields = data.get("fields") or {}

    # Nạp cấu hình đã lưu để fallback nếu client không truyền trường tương ứng
    from integrations_service import load_integrations_config
    saved_cfg = load_integrations_config().get(platform, {})

    if platform == "telegram":
        token = fields.get("bot_token") or saved_cfg.get("bot_token", "")
        chat_id = fields.get("chat_id") or saved_cfg.get("chat_id", "")
        success, msg, details = test_telegram_connection(token, chat_id)
        return jsonify({"success": success, "message": msg, "details": details})

    elif platform == "heygen":
        key = fields.get("api_key") or saved_cfg.get("api_key", "")
        avatar_id = fields.get("avatar_id") or saved_cfg.get("avatar_id", "")
        success, msg, details = test_heygen_connection(key, avatar_id)
        return jsonify({"success": success, "message": msg, "details": details})

    elif platform == "elevenlabs":
        key = fields.get("api_key") or saved_cfg.get("api_key", "")
        voice_id = fields.get("voice_id") or saved_cfg.get("voice_id", "")
        model_id = fields.get("model_id") or saved_cfg.get("model_id", "eleven_multilingual_v2")
        success, msg, details = test_elevenlabs_connection(key, voice_id, model_id)
        return jsonify({"success": success, "message": msg, "details": details})

    elif platform == "gemini":
        from gemini_content_service import get_gemini_config
        saved_gemini = get_gemini_config()
        key = fields.get("api_key") or saved_gemini.get("api_key", "")
        model = fields.get("model") or saved_gemini.get("model", "gemini-2.5-flash")
        success, msg, details = test_gemini_connection(key, model)
        return jsonify({"success": success, "message": msg, "details": details})

    elif platform == "tiktok":
        token = fields.get("access_token") or saved_cfg.get("access_token", "")
        username = fields.get("username") or saved_cfg.get("username", "")
        client_key = fields.get("client_key") or saved_cfg.get("client_key", "")
        client_secret = fields.get("client_secret") or saved_cfg.get("client_secret", "")
        privacy_level = fields.get("privacy_level") or saved_cfg.get("privacy_level", "PUBLIC_TO_EVERYONE")
        public_base_url = fields.get('public_base_url') or saved_cfg.get('public_base_url', '')
        success, msg, details = test_tiktok_connection(token, username, client_key, client_secret, privacy_level, public_base_url)
        return jsonify({"success": success, "message": msg, "details": details})

    elif platform == "google_drive":
        is_conn = drive_manager.is_connected
        if is_conn:
            return jsonify({"success": True, "message": f"Google Drive đã kết nối với tài khoản: {drive_manager.user_email}"})
        else:
            return jsonify({"success": False, "message": "Google Drive chưa được kết nối."})

    return jsonify({"success": False, "message": "Nền tảng không xác định."}), 400


@app.route("/api/telegram/detect_chat_id", methods=["POST"])
def telegram_detect_chat_id():
    from integrations_service import auto_detect_telegram_chat_id, load_integrations_config
    data = request.json or {}
    token = (data.get("bot_token") or "").strip()
    if not token:
        cfg = load_integrations_config()
        token = cfg.get("telegram", {}).get("bot_token", "")

    success, msg, details = auto_detect_telegram_chat_id(token)
    return jsonify({"success": success, "message": msg, "details": details})


@app.route("/api/telegram/send_question", methods=["POST"])
def telegram_send_question():
    from integrations_service import send_telegram_question, load_integrations_config
    data = request.json or {}
    cfg = load_integrations_config().get("telegram", {})
    token = (data.get("bot_token") or cfg.get("bot_token", "")).strip()
    chat_id = (data.get("chat_id") or cfg.get("chat_id", "")).strip()
    question = (data.get("question") or "bạn có đồng ý chỉnh sửa không?").strip()

    success, msg, details = send_telegram_question(token, chat_id, question)
    return jsonify({"success": success, "message": msg, "details": details})


@app.route("/api/telegram/poll_response", methods=["GET"])
def telegram_poll_response():
    from integrations_service import poll_telegram_response
    prompt_id = request.args.get("prompt_id", "").strip()
    if not prompt_id:
        return jsonify({"success": False, "message": "Thiếu prompt_id"}), 400
    res = poll_telegram_response(prompt_id)
    return jsonify(res)


@app.route("/api/ai/generate_content", methods=["POST"])
def generate_ai_content():
    from gemini_content_service import generate_tax_slide_content
    data = request.json or {}
    row_index = data.get("index")
    if row_index is None:
        return jsonify({"success": False, "message": "Vui lòng chọn dòng dữ liệu cần tạo nội dung!"}), 400

    try:
        row_index = int(row_index)
        if row_index < 0 or row_index >= len(drive_manager.current_data):
            return jsonify({"success": False, "message": "Chỉ số dòng không hợp lệ!"}), 400

        # Lấy dữ liệu dòng hiện tại (kèm giá trị gửi lên từ form nếu người dùng vừa gõ)
        row_data = drive_manager.current_data[row_index].copy()
        if "fields" in data and isinstance(data["fields"], dict):
            row_data.update(data["fields"])

        # Gọi engine tạo nội dung slide & tạo thư mục trên Google Drive
        result = generate_tax_slide_content(drive_manager, row_data)
        if not result.get("success"):
            return jsonify(result), 400

        # Cập nhật ngược lại Google Sheet: Đưa toàn bộ kịch bản nội dung chi tiết vào cột Nội dung
        slide_content = (result.get("slide_script") or result.get("summary") or "").strip()
        hashtags = (result.get("hashtags") or "").strip()
        updated_fields = {
            "Nội dung": slide_content,
            "Hag tag": hashtags,
            "Loại video": "Chính sách thuế",
            "Dạng video": "Ảnh cuộn"
        }
        drive_manager.update_row(row_index, updated_fields)

        result["row"] = drive_manager.current_data[row_index]
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tạo nội dung AI: {str(e)}"}), 500




# ==========================================
# CẤU HÌNH THÔNG SỐ ẢNH CUỘN (CAROUSEL PRESETS)
# ==========================================
@app.route("/api/carousel-presets", methods=["GET"])
def get_carousel_presets():
    try:
        presets = load_presets()
        return jsonify({"success": True, "presets": presets})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/carousel-presets", methods=["POST"])
def save_carousel_preset():
    try:
        data = request.json or {}
        p_id = data.get("id")
        name = data.get("name", "").strip()
        desc = data.get("description", "").strip()
        instruction = data.get("instruction", "").strip()
        image_url = data.get("image_url", "").strip()
        category = data.get("category", "").strip() or "Khác"
        is_default = bool(data.get("is_default", False))

        if not name:
            return jsonify({"success": False, "message": "Vui lòng nhập tên thông số ảnh cuộn"}), 400

        presets = load_presets()
        
        # Nếu đặt là default thì bỏ default các preset khác
        if is_default:
            for p in presets:
                p["is_default"] = False

        if p_id:
            # Update existing
            found = False
            for p in presets:
                if p.get("id") == p_id:
                    p["name"] = name
                    p["category"] = category
                    p["description"] = desc
                    p["instruction"] = instruction
                    if image_url:
                        p["image_url"] = image_url
                    p["is_default"] = is_default
                    p["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    found = True
                    break
            if not found:
                p_id = f"preset_{int(time.time())}"
                presets.append({
                    "id": p_id,
                    "name": name,
                    "category": category,
                    "description": desc,
                    "instruction": instruction,
                    "image_url": image_url or "/static/images/presets/preset_mark_dao_infographic.jpg",
                    "is_default": is_default,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
        else:
            # Create new
            p_id = f"preset_{int(time.time())}"
            presets.append({
                "id": p_id,
                "name": name,
                "category": category,
                "description": desc,
                "instruction": instruction,
                "image_url": image_url or "/static/images/presets/preset_mark_dao_infographic.jpg",
                "is_default": is_default,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

        save_presets(presets)
        return jsonify({"success": True, "message": "Đã lưu thông số ảnh cuộn thành công!", "preset_id": p_id, "presets": presets})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi lưu preset: {str(e)}"}), 500



@app.route("/api/carousel-presets/upload-image", methods=["POST"])
def upload_preset_image():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Không tìm thấy file ảnh tải lên."}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "Chưa chọn file ảnh."}), 400

        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        filename = f"preset_custom_{int(time.time())}{ext}"
        dest_dir = os.path.join(CURRENT_DIR, "static", "images", "presets")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        file.save(dest_path)

        return jsonify({
            "success": True,
            "image_url": f"/static/images/presets/{filename}",
            "message": "Đã tải ảnh minh họa lên thành công!"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tải ảnh: {str(e)}"}), 500


@app.route("/api/carousel-presets/generate-prompt", methods=["POST"])
def generate_carousel_preset_ai_prompt():
    """Dựa vào Mô tả phong cách ảnh cuộn (và Tên thông số ảnh cuộn) để AI tạo ra Chỉ dẫn AI tạo ảnh (Design Instruction)."""
    try:
        from gemini_content_service import get_gemini_config, call_gemini_generate
        data = request.json or {}
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()

        if not description and not name:
            return jsonify({
                "success": False,
                "message": "Vui lòng nhập 'Mô tả phong cách ảnh cuộn' trước khi bấm AI Prompt!"
            }), 400

        prompt = f"""Bạn là Giám đốc Sáng tạo & Chuyên gia Thiết kế Đồ họa Slide Ảnh Cuộn TikTok (Carousel 4:5 - 1080x1350px) chuyên nghiệp.
Dựa trên thông tin mô tả phong cách ảnh cuộn dưới đây, hãy viết một bản "Chỉ dẫn AI tạo ảnh (AI Prompt / Design Instruction)" thật chi tiết, rõ ràng, chuyên nghiệp để làm cơ sở cho AI sinh hình ảnh các slide ảnh cuộn TikTok.

- Tên thông số / phong cách: {name or 'Ảnh cuộn TikTok chuyên nghiệp'}
- Mô tả phong cách ảnh cuộn: {description or name}

Yêu cầu nội dung Chỉ dẫn AI tạo ảnh (viết bằng tiếng Việt, súc tích, cấu trúc rõ ràng từ 6-10 dòng):
1. Tỷ lệ khung hình & Bố cục (Layout): Tỷ lệ dọc 4:5 chuẩn tối ưu cho ảnh cuộn TikTok (kích thước 1080x1350px), vùng an toàn (Safe Zone) tránh bị che bởi các icon điều hướng.
2. Bảng màu chủ đạo (Color Palette): Màu nền, màu thẻ (card), màu nhấn (accent color), độ tương phản cao rõ ràng.
3. Nghệ thuật chữ (Typography & Hierarchy): Phân cấp tiêu đề chính (Hook/Headline) to rõ, tiêu đề phụ, nội dung bullet ngắn gọn dễ đọc trên điện thoại.
4. Phong cách đồ họa & Minh họa (Visual Elements): Các icon 2D/3D, biểu đồ, nhân vật, đường nét, đổ bóng, hiệu ứng thị giác phù hợp với mô tả "{description or name}".
5. Quy tắc đồng nhất giữa các Slide (Consistency): Giữ nhận diện xuyên suốt từ Slide 1 (Bìa thu hút) đến các Slide nội dung và Slide cuối (CTA).

Chỉ trả về trực tiếp nội dung Chỉ dẫn AI tạo ảnh, không thêm lời chào hay giải thích thừa."""

        cfg = get_gemini_config()
        cfg_no_search = dict(cfg)
        cfg_no_search["enable_web_search"] = False
        ok, result_text, _ = call_gemini_generate(prompt, cfg_no_search)

        if ok and result_text:
            cleaned = result_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 2:
                    cleaned = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]).strip()
            return jsonify({
                "success": True,
                "instruction": cleaned,
                "message": "Đã tạo Chỉ dẫn AI tạo ảnh từ mô tả phong cách thành công!"
            })

        # Fallback thông minh nếu API Gemini đang bận hoặc hết quota
        style_desc = description or name
        fallback_instruction = (
            f"Thiết kế bộ slide ảnh cuộn TikTok (tỷ lệ dọc 4:5, độ phân giải 1080x1350px) theo phong cách: {style_desc}.\n"
            f"- Bố cục & Vùng an toàn (Safe Zone): Căn lề an toàn tối thiểu 60px hai bên và 120px phía dưới; sắp xếp nội dung dạng thẻ (Card/Bento Grid) trực quan, thoáng đãng.\n"
            f"- Bảng màu & Ánh sáng: Phối màu hài hòa bám sát đặc trưng '{style_desc}', đảm bảo độ tương phản cao giữa nền và chữ để đọc lướt nhanh trên di động.\n"
            f"- Phân cấp chữ (Typography): Tiêu đề chính (Headline) sử dụng font Sans-serif đậm, kích thước lớn nổi bật ở 1/3 trên của slide; nội dung chính cô đọng thành các ý ngắn kèm badge đánh số thứ tự.\n"
            f"- Đồ họa & Minh họa: Kết hợp icon vector/3D hiện đại, biểu tượng chuyên ngành tài chính - thuế - kinh doanh sắc nét, đồng bộ xuyên suốt từ Slide bìa (Hook) đến Slide kêu gọi hành động (CTA)."
        )
        return jsonify({
            "success": True,
            "instruction": fallback_instruction,
            "message": "Đã tạo Chỉ dẫn AI tạo ảnh theo mô tả phong cách!"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tạo AI Prompt: {str(e)}"}), 500


@app.route("/api/carousel-presets/<preset_id>", methods=["DELETE"])
def delete_carousel_preset(preset_id):
    try:
        presets = load_presets()
        presets = [p for p in presets if p.get("id") != preset_id]
        save_presets(presets)
        return jsonify({"success": True, "message": "Đã xóa thông số ảnh cuộn", "presets": presets})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/carousel-presets/<preset_id>/default", methods=["POST"])
def set_default_carousel_preset(preset_id):
    try:
        presets = load_presets()
        for p in presets:
            p["is_default"] = (p.get("id") == preset_id)
        save_presets(presets)
        return jsonify({"success": True, "message": "Đã đặt làm mẫu mặc định", "presets": presets})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# TẠO SLIDE HÌNH ẢNH (AI SLIDE GENERATOR)
# ==========================================
@app.route("/api/ai/generate_slides", methods=["POST"])
def generate_slides():
    try:
        data = request.json or {}
        row_index = data.get("index")
        fields = data.get("fields", {})
        preset_id = data.get("preset_id")

        if row_index is None:
            return jsonify({"success": False, "message": "Thiếu thông tin dòng dữ liệu."}), 400

        row_index = int(row_index)
        if row_index < 0 or row_index >= len(drive_manager.current_data):
            return jsonify({"success": False, "message": "Chỉ số dòng không hợp lệ."}), 400

        # Lấy dữ liệu dòng kết hợp fields mới nhất
        row = drive_manager.current_data[row_index].copy()
        row.update(fields)

        # Điều kiện tiên quyết: duyệt CĐ và HT phải được checked
        duyet_cd_ht = str(row.get("duyệt CĐ và HT", "")).strip().lower()
        if duyet_cd_ht != "x":
            return jsonify({
                "success": False,
                "message": "Vui lòng duyệt CĐ và HT (tích chọn 'duyệt CĐ và HT' ở Cột H) trước khi thực hiện Tạo Slide hình ảnh!"
            }), 400

        # Tạo slide hình ảnh và upload lên Google Drive
        result = generate_and_upload_slides(
            row_data=row,
            row_index=row_index,
            preset_id=preset_id,
            drive_manager=drive_manager
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tạo slide: {str(e)}"}), 500




# ==========================================
# TIKTOK PUBLISHING API (PHOTO CAROUSEL & SELF_ONLY)
# ==========================================
@app.route("/api/tiktok/publish-carousel", methods=["POST"])
def publish_carousel_tiktok():
    try:
        data = request.json or {}
        row_index = int(data.get("row_index", 0))
        fields = data.get("fields", {})

        if not drive_manager.current_data or row_index >= len(drive_manager.current_data):
            drive_manager.locate_file_and_load()

        row = {}
        if drive_manager.current_data and row_index < len(drive_manager.current_data):
            row = drive_manager.current_data[row_index].copy()
        row.update(fields)

        result = publish_topic_to_tiktok(
            row_data=row,
            row_index=row_index,
            drive_manager=drive_manager
        )
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Lỗi xuất bản TikTok: {str(e)}"}), 500


@app.route("/api/tiktok/download-slides-zip", methods=["GET"])
def download_slides_zip():
    try:
        stt = str(request.args.get("stt", "1")).strip()
        chu_de = str(request.args.get("chu_de", "")).strip()

        slides_dir = os.path.join(CURRENT_DIR, "static", "generated_slides")
        target_folder = None
        if os.path.exists(slides_dir):
            for d in os.listdir(slides_dir):
                full_d = os.path.join(slides_dir, d)
                if os.path.isdir(full_d):
                    if d.startswith(f"{stt}_") or d == stt or (chu_de and chu_de in d):
                        target_folder = full_d
                        break

        if not target_folder or not os.path.exists(target_folder):
            target_folder = slides_dir

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(target_folder):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.mp4')):
                        file_path = os.path.join(root, file)
                        zf.write(file_path, arcname=file)

        memory_file.seek(0)
        zip_name = f"Slide_TikTok_{stt}.zip"
        return send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zip_name
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tiktok/open-studio-assistant", methods=["POST"])
def open_tiktok_studio_assistant():
    try:
        data = request.json or {}
        stt = str(data.get("stt", "1")).strip()
        chu_de = str(data.get("chu_de", "")).strip()

        # 1. Tìm thư mục ảnh tương ứng với chủ đề / STT
        target_folder = None
        slides_dir = os.path.join(CURRENT_DIR, "static", "generated_slides")
        if os.path.exists(slides_dir):
            for d in os.listdir(slides_dir):
                full_d = os.path.join(slides_dir, d)
                if os.path.isdir(full_d):
                    if d.startswith(f"{stt}_") or d == stt or (chu_de and chu_de in d):
                        target_folder = full_d
                        break

        abs_path = os.path.abspath(target_folder) if target_folder else os.path.abspath(slides_dir)

        # 2. Cập nhật file Mo_Thu_Muc_Anh.bat ở thư mục gốc
        try:
            root_dir = os.path.dirname(CURRENT_DIR)
            bat_path = os.path.join(root_dir, "Mo_Thu_Muc_Anh.bat")
            with open(bat_path, "w", encoding="utf-8") as bf:
                bf.write(f'@echo off\nchcp 65001 >nul\nexplorer.exe "{abs_path}"\n')
        except Exception:
            pass

        # 3. Mở Windows Explorer bằng nhiều phương thức
        if os.path.exists(abs_path):
            try:
                subprocess.Popen(["explorer.exe", abs_path])
            except Exception:
                pass
            try:
                subprocess.Popen(["rundll32.exe", "url.dll,FileProtocolHandler", abs_path])
            except Exception:
                pass

        return jsonify({
            "success": True,
            "folder_path": abs_path,
            "message": f"Đã gửi lệnh mở thư mục ảnh! Nếu chưa thấy, bạn có thể click đúp file Mo_Thu_Muc_Anh.bat hoặc dán đường dẫn: {abs_path}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi mở trợ lý TikTok: {str(e)}"}), 500


@app.route("/api/tiktok/tunnel-status", methods=["GET"])
def get_tiktok_tunnel_status():
    try:
        import urllib.request
        import subprocess
        from tiktok_publisher_service import get_active_tunnel_url, load_tiktok_config
        live_tunnel = get_active_tunnel_url()
        cfg = load_tiktok_config()
        saved_url = cfg.get("public_base_url", "").strip().rstrip("/")
        
        is_ngrok_running = False
        try:
            req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels", headers={"User-Agent": "TikTokStudio/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    is_ngrok_running = True
        except Exception:
            pass

        is_cf_running = False
        try:
            res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq cloudflared.exe"], capture_output=True, text=True, timeout=2)
            is_cf_running = "cloudflared.exe" in res.stdout
        except Exception:
            pass

        tunnel_type = "none"
        if live_tunnel:
            if "trycloudflare" in live_tunnel:
                tunnel_type = "cloudflare"
            elif "ngrok" in live_tunnel:
                tunnel_type = "ngrok"
            else:
                tunnel_type = "custom"

        return jsonify({
            "success": True,
            "is_active": bool(live_tunnel),
            "tunnel_type": tunnel_type,
            "is_ngrok_running": is_ngrok_running,
            "is_cloudflare_running": is_cf_running,
            "tunnel_url": live_tunnel,
            "saved_url": saved_url,
            "web_url": f"{live_tunnel}/" if live_tunnel else "",
            "terms_url": f"{live_tunnel}/terms" if live_tunnel else "",
            "privacy_url": f"{live_tunnel}/privacy" if live_tunnel else "",
            "redirect_uri": f"{live_tunnel}/api/tiktok/oauth-callback" if live_tunnel else ""
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tiktok/apply-tunnel-url", methods=["POST"])
def apply_tiktok_tunnel_url():
    try:
        from tiktok_publisher_service import get_active_tunnel_url
        from integrations_service import save_integrations_config, load_integrations_config

        body = request.get_json(silent=True) or {}
        custom_url = body.get("tunnel_url", "").strip()

        tunnel = custom_url or get_active_tunnel_url()
        if not tunnel:
            return jsonify({"success": False, "message": "Chưa phát hiện đường hầm Ngrok hoặc Cloudflare đang hoạt động trên máy tính!"}), 400

        tunnel = tunnel.rstrip("/")
        integ = load_integrations_config()
        tt_cfg = integ.get("tiktok", {})
        tt_cfg["public_base_url"] = tunnel
        save_integrations_config({"tiktok": tt_cfg})

        tunnel_type = "Cloudflare Tunnel" if "trycloudflare" in tunnel else ("Ngrok Tunnel" if "ngrok" in tunnel else "HTTPS Tunnel")
        return jsonify({
            "success": True,
            "tunnel_url": tunnel,
            "tunnel_type": tunnel_type,
            "web_url": f"{tunnel}/",
            "terms_url": f"{tunnel}/terms",
            "privacy_url": f"{tunnel}/privacy",
            "redirect_uri": f"{tunnel}/api/tiktok/oauth-callback",
            "message": f"Đã liên kết {tunnel_type}: {tunnel}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tiktok/oauth-url", methods=["GET"])
def get_tiktok_oauth_url():
    try:
        from tiktok_publisher_service import get_active_tunnel_url, load_tiktok_config
        import urllib.parse
        cfg = load_tiktok_config()
        client_key = cfg.get("client_key", "awg8wrdqd51lrcfx")
        tunnel = get_active_tunnel_url() or "http://127.0.0.1:5150"
        redirect_uri = f"{tunnel}/api/tiktok/oauth-callback"
        scopes = "user.info.basic,video.publish,video.upload"
        state = f"tt_state_{int(time.time())}"
        
        auth_url = (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={client_key}"
            f"&scope={urllib.parse.quote(scopes)}"
            f"&response_type=code"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&state={state}"
        )
        return jsonify({
            "success": True,
            "auth_url": auth_url,
            "redirect_uri": redirect_uri
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/tiktok/oauth-callback", methods=["GET"])
def tiktok_oauth_callback():
    code = request.args.get("code")
    err = request.args.get("error")
    err_desc = request.args.get("error_description", "")
    if err:
        return f"<div style='font-family:sans-serif;padding:30px;color:#b91c1c;'><h3>Ủy quyền TikTok thất bại</h3><p>{err}: {err_desc}</p><a href='/'>Quay lại ứng dụng</a></div>", 400

    if not code:
        return "<div style='font-family:sans-serif;padding:30px;color:#b91c1c;'><h3>Không nhận được mã xác thực (Code) từ TikTok</h3><a href='/'>Quay lại</a></div>", 400

    from tiktok_publisher_service import get_active_tunnel_url, load_tiktok_config
    from integrations_service import save_integrations_config, load_integrations_config
    import requests
    
    cfg = load_tiktok_config()
    client_key = cfg.get("client_key", "awg8wrdqd51lrcfx")
    client_secret = cfg.get("client_secret", "aujSZ5kwoO3SoFWkDLAQur4e0HBfylwP")
    tunnel = get_active_tunnel_url() or "http://127.0.0.1:5150"
    redirect_uri = f"{tunnel}/api/tiktok/oauth-callback"

    try:
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        data = {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(token_url, data=data, headers=headers, timeout=15)
        res_data = resp.json()
        
        access_token = res_data.get("access_token")
        if access_token:
            tt_cfg = load_integrations_config().get("tiktok", {})
            tt_cfg["access_token"] = access_token
            tt_cfg["open_id"] = res_data.get("open_id", "")
            tt_cfg["is_connected"] = True
            save_integrations_config({"tiktok": tt_cfg})
            return f"<script>alert('Ủy quyền TikTok thành công! Đã lưu Access Token.'); window.location.href='/';</script>"
        else:
            return f"<div style='font-family:sans-serif;padding:30px;'><h3>Lỗi đổi token:</h3><pre>{resp.text}</pre><a href='/'>Quay lại</a></div>", 400
    except Exception as e:
        return f"<div style='font-family:sans-serif;padding:30px;'><h3>Lỗi kết nối:</h3><p>{str(e)}</p><a href='/'>Quay lại</a></div>", 500


def open_browser(port):
    import time
    import urllib.request
    url = f"http://127.0.0.1:{port}"
    # Đợi máy chủ khởi động hoàn tất và phản hồi trước khi mở trình duyệt
    for _ in range(40):
        time.sleep(0.3)
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass
    webbrowser.open(url)


if __name__ == "__main__":
    PORT = int(os.environ.get("TIKTOK_APP_PORT", 5150))
    print("=" * 75)
    print("🚀 TIKTOK AUTOMATION STUDIO - GIAI ĐOẠN 1: QUẢN LÝ DỮ LIỆU GOOGLE DRIVE")
    print(f"🌐 Đang khởi động máy chủ tại: http://127.0.0.1:{PORT}")
    print("=" * 75)

    if not os.environ.get("NO_OPEN_BROWSER"):
        threading.Thread(target=open_browser, args=(PORT,), daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)
