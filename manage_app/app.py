import os
import sys
import threading
# Cho phép oauthlib chấp nhận thay đổi/mở rộng Scope linh hoạt từ Google OAuth 2.0 (tránh lỗi ScopeChangeError)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" 
import io
import json
import zipfile
import datetime
import traceback
import hashlib
from typing import Dict, Any, List
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
try:
    import mammoth
except ImportError:
    mammoth = None
try:
    import openpyxl
except ImportError:
    openpyxl = None
# Đảm bảo đường dẫn import
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
from assistant_service import assistant_service
from config_manager import ConfigManager
from drive_service import drive_service
from google_auth_service import GoogleAuthService
from scanner_service import scanner_service
from pdf_generator import PDFGenerator
from attachment_downloader import AttachmentDownloader
from notebooklm_service import notebooklm_service
from notebooklm_auto import NotebookLMAutoService
from admin_doc_service import admin_doc_service
from secretary_service import SecretaryService, REPORTS_DIR
from chief_secretary_service import ChiefSecretaryService
try:
    from telegram_service import TelegramService
    if TelegramService:
        TelegramService.start_polling()
except Exception as _ex_tg:
    print(f"[App] Import TelegramService error: {_ex_tg}")
    TelegramService = None
app = Flask(
    __name__,
    template_folder=os.path.join(CURRENT_DIR, "templates"),
    static_folder=os.path.join(CURRENT_DIR, "static")
)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
CORS(app)
# Tự động nạp cấu hình Google Drive khi app khởi động
try:
    drive_service.test_connection()
except Exception as e:
    print(f"[App] Khởi tạo kết nối Drive: {e}")
UPLOAD_DIR = os.path.join(CURRENT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx'}
def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
def get_file_mimetype(ext: str) -> str:
    ext = ext.lower()
    if ext == '.pdf':
        return 'application/pdf'
    elif ext == '.docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif ext == '.doc':
        return 'application/msword'
    elif ext == '.xlsx':
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif ext == '.xls':
        return 'application/vnd.ms-excel'
    return 'application/octet-stream'
def get_file_type_label(ext: str) -> str:
    ext = ext.lower()
    if ext == '.pdf':
        return 'PDF'
    elif ext in ('.docx', '.doc'):
        return f'Word ({ext.replace(".", "").upper()})'
    elif ext in ('.xlsx', '.xls'):
        return f'Excel ({ext.replace(".", "").upper()})'
    return 'Văn bản'
@app.route("/")
def index():
    """Giao diện chính dạng Tabs của Manage App"""
    return render_template("index.html")
# ==================== CONFIG APIS ====================
@app.route("/api/config", methods=["GET"])
def get_config():
    """Lấy toàn bộ cấu hình hệ thống bao gồm lĩnh vực lưu gần nhất và trạng thái Drive"""
    config = ConfigManager.load_config()
    is_connected = drive_service.is_connected
    user_info = drive_service.user_info if is_connected else None
    sources = ConfigManager.get_sources()
    
    return jsonify({
        "success": True,
        "last_fields": ConfigManager.get_last_fields(),
        "date_filter": config.get("date_filter", {}),
        "drive_connected": is_connected,
        "drive_user": user_info,
        "default_folder_id": config.get("google_drive", {}).get("default_folder_id", "root"),
        "default_folder_name": config.get("google_drive", {}).get("default_folder_name", "📁 My Drive (Thư mục gốc)"),
        "client_id": config.get("google_drive", {}).get("client_id", ""),
        "sources": sources,
        "notebooks": ConfigManager.get_notebooks(),
        "default_notebook_id": ConfigManager.get_default_notebook_id(),
        "notebooklm_storage_dir": ConfigManager.get_notebooklm_storage_dir()
    })
@app.route("/api/config/save-fields", methods=["POST"])
def save_fields():
    """Tự động lưu lại giá trị lĩnh vực nhập sau cùng để duy trì trạng thái khi mở lại"""
    data = request.json or {}
    fields = data.get("fields", "").strip()
    if fields:
        ConfigManager.update_last_fields(fields)
        return jsonify({"success": True, "message": "Đã tự động lưu lĩnh vực gần nhất", "fields": fields})
    return jsonify({"success": False, "message": "Dữ liệu rỗng"}), 400
@app.route("/api/config/set-default-folder", methods=["POST"])
def set_default_folder():
    """Đặt thư mục lưu trữ mặc định trên Google Drive"""
    data = request.json or {}
    folder_id = data.get("folder_id", "root")
    folder_name = data.get("folder_name", "📁 My Drive (Thư mục gốc)")
    
    ConfigManager.update_drive_config({
        "default_folder_id": folder_id,
        "default_folder_name": folder_name
    })
    return jsonify({"success": True, "message": f"Đã đặt thư mục mặc định: {folder_name}"})
# ==================== GOOGLE DRIVE APIS ====================
@app.route("/api/drive/status", methods=["GET"])
def get_drive_status():
    """Kiểm tra trạng thái kết nối Google Drive hiện tại"""
    return jsonify({
        "connected": drive_service.is_connected,
        "user": drive_service.user_info
    })
@app.route("/api/drive/test-connection", methods=["POST"])
def test_drive_connection():
    """Kiểm tra kết nối và lấy danh sách thư mục Google Drive phục vụ Tab 1 & Tab 2"""
    result = drive_service.test_connection()
    return jsonify(result)
@app.route("/api/drive/folders", methods=["GET"])
def get_drive_folders():
    """Lấy danh sách các thư mục có trên Google Drive"""
    folders = drive_service.list_folders()
    return jsonify({"success": True, "folders": folders})
@app.route("/api/drive/create-folder", methods=["POST"])
def create_drive_folder():
    """Tạo thư mục mới trực tiếp trên Google Drive"""
    data = request.json or {}
    folder_name = data.get("folder_name", "").strip()
    parent_id = data.get("parent_id", "root")
    
    if not folder_name:
        return jsonify({"success": False, "message": "Tên thư mục không được để trống."}), 400
    res = drive_service.create_folder(folder_name, parent_id)
    return jsonify(res)
@app.route("/api/drive/save-credentials", methods=["POST"])
def save_drive_credentials():
    """Lưu thông tin Client ID, Client Secret, Refresh Token"""
    data = request.json or {}
    client_id = data.get("client_id", "").strip()
    client_secret = data.get("client_secret", "").strip()
    refresh_token = data.get("refresh_token", "").strip()
    if not client_id or not client_secret:
        return jsonify({"success": False, "message": "Vui lòng nhập Client ID và Client Secret."}), 400
    result = drive_service.save_oauth_credentials(client_id, client_secret, refresh_token)
    return jsonify(result)
@app.route("/api/drive/import-local", methods=["POST"])
def import_local_credentials():
    """Tự động phát hiện và nạp credentials/token có sẵn trên máy tính"""
    res = drive_service.import_local_credentials()
    return jsonify(res)
# ==================== GOOGLE TEXT-TO-SPEECH (TIẾNG VIỆT GIỌNG NỮ MIỀN NAM) ====================
@app.route("/api/chief-secretary/tts", methods=["GET"])
def get_chief_secretary_tts_audio():
    """Tạo stream audio giọng nữ tiếng Việt chuẩn cho Thư ký Cô Tấm"""
    text_content = request.args.get("text", "").strip()
    if not text_content:
        return "Thiếu nội dung text", 400
    try:
        import urllib.request
        import urllib.parse
        import re
        # Tách câu nhỏ hơn 180 ký tự để Google Translate TTS phát âm mượt mà nhất
        sentences = re.split(r'([.?!;\n]+)', text_content)
        chunks = []
        curr = ''
        for s in sentences:
            if len(curr) + len(s) < 180:
                curr += s
            else:
                if curr.strip():
                    chunks.append(curr.strip())
                curr = s
        if curr.strip():
            chunks.append(curr.strip())
        combined_mp3 = bytearray()
        for chunk in chunks:
            c = chunk.strip()
            if not c:
                continue
            params = {
                'ie': 'UTF-8',
                'tl': 'vi',
                'client': 'tw-ob',
                'q': c
            }
            url = f"https://translate.google.com/translate_tts?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                combined_mp3.extend(resp.read())
        return send_file(
            io.BytesIO(combined_mp3),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="cotam_speech.mp3"
        )
    except Exception as e:
        print(f"[TTS Error] Lỗi tạo audio tiếng Việt: {e}")
        return jsonify({"error": str(e)}), 500
# ==================== GOOGLE OAUTH 2.0 APIS (CALENDAR, TASKS, DRIVE, SHEETS) ====================
@app.route("/api/oauth/google/status", methods=["GET"])
def get_google_oauth_status_api():
    """Kiểm tra chi tiết trạng thái Google OAuth 2.0 đa dịch vụ"""
    status = GoogleAuthService.get_auth_status()
    return jsonify(status)
@app.route("/api/oauth/google/auth-url", methods=["GET"])
def get_google_oauth_auth_url_api():
    """Tạo URL đăng nhập Google OAuth 2.0 đầy đủ 4 Scopes (Calendar, Tasks, Drive, Sheets)"""
    redirect_uri = request.args.get("redirect_uri")
    if not redirect_uri:
        redirect_uri = f"{request.host_url.rstrip('/')}/oauth2callback"
    res = GoogleAuthService.generate_auth_url(redirect_uri=redirect_uri)
    return jsonify(res)
@app.route("/api/oauth/google/exchange-code", methods=["POST"])
def exchange_google_oauth_code_api():
    """Đổi mã Authorization Code lấy token"""
    data = request.json or {}
    code = data.get("code", "").strip()
    redirect_uri = data.get("redirect_uri")
    if not redirect_uri:
        redirect_uri = f"{request.host_url.rstrip('/')}/oauth2callback"
    if not code:
        return jsonify({"success": False, "message": "Mã xác thực Code không được để trống."}), 400
    res = GoogleAuthService.exchange_code(code, redirect_uri=redirect_uri)
    return jsonify(res)
@app.route("/api/oauth/google/save-token", methods=["POST"])
def save_google_oauth_manual_token_api():
    """Lưu Refresh Token nhập thủ công"""
    data = request.json or {}
    refresh_token = data.get("refresh_token", "").strip()
    res = GoogleAuthService.save_manual_refresh_token(refresh_token)
    return jsonify(res)
@app.route("/oauth2callback", methods=["GET"])
def oauth2_callback():
    """Trang xử lý callback từ Google OAuth 2.0 khi người dùng bấm đồng ý"""
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Lỗi xác thực Google</title>
        <style>body{{font-family:sans-serif;padding:40px;background:#fff5f5;color:#991b1b;text-align:center;}}
        .card{{max-width:550px;margin:0 auto;background:#fff;padding:30px;border-radius:12px;border:1px solid #fecaca;box-shadow:0 4px 12px rgba(0,0,0,0.05);}}
        h2{{margin-top:0;}} a{{display:inline-block;margin-top:20px;padding:10px 20px;background:#b91c1c;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;}}</style>
        </head><body><div class='card'><h2>❌ Xác thực Google thất bại</h2>
        <p>Google từ chối hoặc người dùng hủy ủy quyền: <b>{error}</b></p>
        <a href='/'>Quay lại ứng dụng</a></div></body></html>"""
    if not code:
        return "<p>Thiếu tham số mã code từ Google.</p>", 400
    redirect_uri = f"{request.host_url.rstrip('/')}/oauth2callback"
    res = GoogleAuthService.exchange_code(code, redirect_uri=redirect_uri)
    
    if res.get("success"):
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Xác thực Google Thành Công</title>
        <style>body{{font-family:system-ui,-apple-system,sans-serif;padding:50px 20px;background:#f0fdf4;color:#166534;text-align:center;}}
        .card{{max-width:580px;margin:0 auto;background:#fff;padding:36px;border-radius:16px;border:1px solid #bbf7d0;box-shadow:0 10px 25px -5px rgba(0,0,0,0.08);}}
        .badge{{background:#dcfce7;color:#15803d;padding:6px 14px;border-radius:9999px;font-weight:bold;font-size:14px;display:inline-block;margin-bottom:16px;}}
        h2{{margin-top:0;color:#15803d;font-size:24px;}} p{{color:#374151;line-height:1.6;font-size:15px;}}
        .btn{{display:inline-block;margin-top:24px;padding:12px 28px;background:#004b93;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;font-size:14px;transition:0.2s;}}
        .btn:hover{{background:#003366;}}</style></head>
        <body><div class='card'>
        <div class='badge'>🎉 KẾT NỐI GOOGLE OAUTH 2.0 THÀNH CÔNG</div>
        <h2>Đã cấp quyền tài khoản bacnguyentax@gmail.com</h2>
        <p>Hệ thống đã nhận token xác thực mới với đầy đủ 4 quyền:</p>
        <p><b>📅 Google Calendar &bull; ✅ Google Tasks &bull; 📁 Google Drive &bull; 🧠 Google NotebookLM</b></p>
        <p>Thư ký nhắc việc Cô Tấm và toàn bộ dịch vụ đã sẵn sàng hoạt động thời gian thực.</p>
        <a href='/' class='btn'>👉 Quay lại Trang Quản Trị Hệ Thống</a>
        </div></body></html>"""
    else:
        err_msg = res.get("message", "Lỗi không xác định")
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Lỗi đổi mã Token</title>
        <style>body{{font-family:sans-serif;padding:40px;background:#fff5f5;color:#991b1b;text-align:center;}}
        .card{{max-width:550px;margin:0 auto;background:#fff;padding:30px;border-radius:12px;border:1px solid #fecaca;box-shadow:0 4px 12px rgba(0,0,0,0.05);}}
        h2{{margin-top:0;}} a{{display:inline-block;margin-top:20px;padding:10px 20px;background:#b91c1c;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;}}</style>
        </head><body><div class='card'><h2>❌ Lỗi đổi mã Token Google</h2>
        <p>{err_msg}</p><a href='/'>Quay lại</a></div></body></html>"""
# ==================== TAB 1: SCANNER & DOWNLOADER APIS ====================
@app.route("/api/scan", methods=["POST"])
def scan_documents():
    """
    Thực hiện quét văn bản mới trên internet theo đúng lĩnh vực và khoảng thời gian.
    Tự động lưu lại giá trị lĩnh vực nhập sau cùng.
    """
    data = request.json or {}
    fields = data.get("fields", "").strip()
    from_date = data.get("from_date", "").strip()
    to_date = data.get("to_date", "").strip()
    doc_types = data.get("doc_types", None)
    # Tự động lưu lĩnh vực nhập sau cùng
    if fields:
        ConfigManager.update_last_fields(fields)
    # Tiến hành dò quét
    scan_result = scanner_service.scan_documents(
        fields=fields,
        from_date_str=from_date,
        to_date_str=to_date,
        doc_types=doc_types
    )
    # Gán thư mục mặc định cho từng văn bản nếu chưa gán
    config = ConfigManager.load_config()
    default_fid = config.get("google_drive", {}).get("default_folder_id", "root")
    for doc in scan_result.get("documents", []):
        doc["selected_folder_id"] = default_fid
    return jsonify(scan_result)
@app.route("/api/documents/upload-drive", methods=["POST"])
def upload_documents_to_drive():
    """
    Tải file văn bản về máy chủ và tự động đẩy (upload) các file đó lên đúng thư mục Google Drive đã chọn.
    """
    if not drive_service.is_connected:
        return jsonify({
            "success": False,
            "message": "Chưa kết nối Google Drive! Vui lòng vào Tab 'Thiết lập cấu hình' để kiểm tra kết nối."
        }), 400
    data = request.json or {}
    documents = data.get("documents", [])
    if not documents:
        return jsonify({"success": False, "message": "Chưa có văn bản nào được chọn để tải về."}), 400
    upload_results = []
    success_count = 0
    fail_count = 0
    for doc in documents:
        doc_id = doc.get("id")
        doc_number = doc.get("doc_number", "VB")
        target_folder = doc.get("selected_folder_id", "root")
        field = doc.get("field", "Chung")
        try:
            # 1. Tải file nội dung đính kèm thực tế từ website nguồn (PDF/DOC/DOCX)
            file_bytes, filename, mimetype = AttachmentDownloader.get_document_payload(doc)
            # 2. Tải trực tiếp lên Google Drive vào thư mục đã chọn
            upload_res = drive_service.upload_file(
                file_content=file_bytes,
                filename=filename,
                folder_id=target_folder,
                mimetype=mimetype
            )
            if upload_res.get("success"):
                success_count += 1
                drive_link = upload_res.get("webViewLink", "")
                
                # Đồng bộ kèm vào kho nguồn NotebookLM (cập nhật manifest & thư mục chuyên đề)
                nb_name = "Tax_Nghiệp vụ thuế"
                nb_url = "https://notebooklm.google.com/"
                target_nb_id = doc.get("selected_notebook_id") or ConfigManager.get_default_notebook_id()
                try:
                    doc_for_nb = doc.copy()
                    doc_for_nb["drive_link"] = drive_link
                    doc_for_nb["selected_folder_id"] = target_folder
                    nb_res = notebooklm_service.save_scanned_document(doc_for_nb, notebook_id=target_nb_id)
                    nb_name = nb_res.get("notebook_name", nb_name)
                    nb_url = nb_res.get("notebook_url", nb_url)
                except Exception as ex_nb:
                    print(f"[App] Lỗi đồng bộ NotebookLM kèm theo: {ex_nb}")
                upload_results.append({
                    "id": doc_id,
                    "doc_number": doc_number,
                    "status": "success",
                    "file_name": filename,
                    "drive_file_id": upload_res.get("id"),
                    "drive_link": drive_link,
                    "notebook_name": nb_name,
                    "notebook_url": nb_url,
                    "message": f"Đã lưu thành công lên Drive: {filename}"
                })
            else:
                fail_count += 1
                upload_results.append({
                    "id": doc_id,
                    "doc_number": doc_number,
                    "status": "error",
                    "message": upload_res.get("message", "Lỗi không xác định khi upload")
                })
        except Exception as e:
            fail_count += 1
            print(f"[App] Lỗi tải & upload doc {doc_number}: {e}")
            upload_results.append({
                "id": doc_id,
                "doc_number": doc_number,
                "status": "error",
                "message": str(e)
            })
    return jsonify({
        "success": success_count > 0,
        "total": len(documents),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": upload_results,
        "message": f"Hoàn tất: Đã tải & lưu thành công {success_count}/{len(documents)} văn bản lên Google Drive!"
    })
# ==================== NOTEBOOKLM APIS ====================
@app.route("/api/notebooklm/list", methods=["GET"])
def get_notebooklm_list():
    """Lấy danh sách các notebook trong NotebookLM, gắn cờ is_tax cho từng notebook"""
    notebooks = ConfigManager.get_notebooks()
    for nb in notebooks:
        nb["is_tax"] = "tax" in nb.get("name", "").lower()
    
    # Sắp xếp ưu tiên các notebook Tax lên trước
    sorted_notebooks = sorted(notebooks, key=lambda x: (not x["is_tax"], x.get("name", "").lower()))
    default_id = ConfigManager.get_default_notebook_id()
    storage_dir = ConfigManager.get_notebooklm_storage_dir()
    return jsonify({
        "success": True,
        "notebooks": sorted_notebooks,
        "default_notebook_id": default_id,
        "storage_dir": storage_dir
    })
@app.route("/api/notebooklm/save", methods=["POST"])
def save_notebooklm_item():
    """Thêm mới hoặc cập nhật một notebook"""
    data = request.json or {}
    notebook_id = data.get("id")
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    folder_name = data.get("folder_name", "").strip()
    description = data.get("description", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Tên notebook không được để trống."}), 400
    if notebook_id:
        res = ConfigManager.update_notebook(notebook_id, name, url, folder_name, description)
    else:
        res = ConfigManager.add_notebook(name, url, folder_name, description)
    if res.get("success"):
        all_nbs = ConfigManager.get_notebooks()
        tax_nbs = [nb for nb in all_nbs if "tax" in nb.get("name", "").lower()]
        return jsonify({
            **res,
            "notebooks": tax_nbs,
            "default_notebook_id": ConfigManager.get_default_notebook_id()
        })
    return jsonify(res), 400
@app.route("/api/notebooklm/delete", methods=["POST"])
def delete_notebooklm_item():
    """Xóa notebook khỏi danh mục"""
    data = request.json or {}
    notebook_id = data.get("id")
    if not notebook_id:
        return jsonify({"success": False, "message": "Thiếu notebook_id cần xóa."}), 400
    res = ConfigManager.delete_notebook(notebook_id)
    if res.get("success"):
        all_nbs = ConfigManager.get_notebooks()
        tax_nbs = [nb for nb in all_nbs if "tax" in nb.get("name", "").lower()]
        return jsonify({
            **res,
            "notebooks": tax_nbs,
            "default_notebook_id": ConfigManager.get_default_notebook_id()
        })
    return jsonify(res), 400
@app.route("/api/notebooklm/set-default", methods=["POST"])
def set_default_notebooklm_item():
    """Đặt notebook làm mặc định"""
    data = request.json or {}
    notebook_id = data.get("id")
    if not notebook_id:
        return jsonify({"success": False, "message": "Thiếu notebook_id."}), 400
    res = ConfigManager.set_default_notebook(notebook_id)
    if res.get("success"):
        all_nbs = ConfigManager.get_notebooks()
        tax_nbs = [nb for nb in all_nbs if "tax" in nb.get("name", "").lower()]
        return jsonify({
            **res,
            "notebooks": tax_nbs,
            "default_notebook_id": ConfigManager.get_default_notebook_id()
        })
    return jsonify(res), 400
@app.route("/api/notebooklm/open-storage-folder", methods=["POST"])
def open_notebooklm_storage_folder():
    """Mở thư mục nguồn NotebookLM trong Windows File Explorer"""
    data = request.json or {}
    folder_path = data.get("folder_path")
    success = notebooklm_service.open_storage_folder(folder_path)
    return jsonify({
        "success": success,
        "message": "Đã mở thư mục nguồn NotebookLM." if success else "Không thể mở thư mục."
    })
@app.route("/api/notebooklm/reset-defaults", methods=["POST"])
def reset_notebooklm_defaults():
    """Khôi phục danh sách chuẩn các notebook Tax từ Google NotebookLM của người dùng"""
    all_notebooks = ConfigManager.reset_default_notebooks()
    tax_notebooks = [nb for nb in all_notebooks if "tax" in nb.get("name", "").lower()]
    default_id = ConfigManager.get_default_notebook_id()
    return jsonify({
        "success": True,
        "message": f"Đã khôi phục thành công danh mục {len(tax_notebooks)} notebook Tax từ Google NotebookLM!",
        "notebooks": tax_notebooks,
        "default_notebook_id": default_id
    })
# ==================== NOTEBOOKLM AUTOMATION (100% TỰ ĐỘNG QUA NOTEBOOKLM-PY) ====================
@app.route("/api/notebooklm/auto/status", methods=["GET"])
def get_notebooklm_auto_status():
    """Kiểm tra trạng thái xác thực tự động với Google NotebookLM"""
    status = NotebookLMAutoService.check_status()
    return jsonify(status)
@app.route("/api/notebooklm/auto/login", methods=["POST"])
def trigger_notebooklm_auto_login():
    """Mở cửa sổ trình duyệt đăng nhập Google một lần duy nhất trên máy"""
    data = request.json or {}
    browser = data.get("browser", "chromium")
    result = NotebookLMAutoService.start_login_browser(browser=browser)
    return jsonify(result)
@app.route("/api/notebooklm/auto/sync-notebooks", methods=["POST"])
def sync_notebooklm_auto_notebooks():
    """Đồng bộ danh sách sổ ghi chú thật từ Google NotebookLM"""
    result = NotebookLMAutoService.sync_notebooks()
    return jsonify(result)
@app.route("/api/documents/upload-notebooklm", methods=["POST"])
def upload_documents_to_notebooklm():
    """
    Lưu danh sách văn bản quét từ web (Tab 1) vào NotebookLM:
    - Lưu file vào thư mục chuyên đề NotebookLM
    - Tự động đồng bộ lên Google Drive nếu kết nối
    - Cập nhật chỉ mục văn bản nguồn _NotebookLM_Sources_Index.txt
    """
    data = request.json or {}
    documents = data.get("documents", [])
    if not documents:
        return jsonify({"success": False, "message": "Chưa có văn bản nào được chọn để lưu vào NotebookLM."}), 400
    results = []
    success_count = 0
    fail_count = 0
    for doc in documents:
        notebook_id = doc.get("selected_notebook_id") or data.get("selected_notebook_id")
        res = notebooklm_service.save_scanned_document(doc, notebook_id=notebook_id)
        results.append(res)
        if res.get("success"):
            success_count += 1
        else:
            fail_count += 1
    return jsonify({
        "success": success_count > 0,
        "total": len(documents),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
        "message": f"Hoàn tất: Đã đồng bộ thành công {success_count}/{len(documents)} văn bản vào nguồn NotebookLM (sẵn sàng trên Google Drive & Máy tính)!"
    })
# ==================== TAB 3: UPLOAD & LƯU VĂN BẢN (PDF, WORD, EXCEL) ====================
@app.route("/api/upload-local-files", methods=["POST"])
def upload_local_files():
    """
    Nhận nhiều tệp tin tải lên từ máy tính cá nhân (PDF, Word, Excel),
    lưu tạm vào thư mục uploads/ để chuẩn bị đẩy lên Google Drive.
    """
    if "files" not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy tệp tin được gửi lên."}), 400
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        return jsonify({"success": False, "message": "Danh sách tệp tin tải lên rỗng."}), 400
    config = ConfigManager.load_config()
    default_fid = config.get("google_drive", {}).get("default_folder_id", "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK")
    processed = []
    for f in uploaded_files:
        if not f or not f.filename:
            continue
        orig_name = f.filename
        _, ext = os.path.splitext(orig_name)
        ext = ext.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        raw_key = f"{orig_name}_{datetime.datetime.now().isoformat()}_{os.urandom(4).hex()}"
        file_id = hashlib.md5(raw_key.encode('utf-8')).hexdigest()[:12]
        saved_filename = f"{file_id}_{orig_name}"
        save_path = os.path.join(UPLOAD_DIR, saved_filename)
        f.save(save_path)
        file_size = os.path.getsize(save_path)
        processed.append({
            "id": file_id,
            "filename": orig_name,
            "saved_filename": saved_filename,
            "size": file_size,
            "size_str": format_file_size(file_size),
            "ext": ext,
            "file_type": get_file_type_label(ext),
            "mimetype": get_file_mimetype(ext),
            "selected_folder_id": default_fid,
            "upload_status": "pending",
            "drive_link": "",
            "drive_file_id": "",
            "message": "Sẵn sàng lưu lên Google Drive"
        })
    return jsonify({
        "success": True,
        "files": processed,
        "count": len(processed),
        "message": f"Đã thêm thành công {len(processed)} tệp văn bản từ máy tính!"
    })
@app.route("/api/upload-local-files-to-drive", methods=["POST"])
def upload_local_files_to_drive():
    """
    Đẩy danh sách các tệp tin cục bộ đã chọn (PDF, Word, Excel) lên đúng thư mục Google Drive đã chọn.
    """
    if not drive_service.is_connected:
        return jsonify({
            "success": False,
            "message": "Chưa kết nối Google Drive! Vui lòng kiểm tra lại cấu hình tài khoản tại Tab 2."
        }), 400
    data = request.json or {}
    files_to_upload = data.get("files", [])
    if not files_to_upload:
        return jsonify({"success": False, "message": "Chưa có tệp tin nào được chọn để lưu."}), 400
    upload_results = []
    success_count = 0
    fail_count = 0
    for item in files_to_upload:
        file_id = item.get("id")
        orig_filename = item.get("filename", "tailieu")
        saved_filename = item.get("saved_filename") or f"{file_id}_{orig_filename}"
        target_folder = item.get("selected_folder_id", "root")
        mimetype = item.get("mimetype") or get_file_mimetype(os.path.splitext(orig_filename)[1])
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        if not os.path.exists(file_path):
            fail_count += 1
            upload_results.append({
                "id": file_id,
                "filename": orig_filename,
                "status": "error",
                "message": "Không tìm thấy tệp nguồn trên máy chủ tạm."
            })
            continue
        try:
            with open(file_path, "rb") as f:
                content_bytes = f.read()
            upload_res = drive_service.upload_file(
                file_content=content_bytes,
                filename=orig_filename,
                folder_id=target_folder,
                mimetype=mimetype
            )
            if upload_res.get("success"):
                success_count += 1
                upload_results.append({
                    "id": file_id,
                    "filename": orig_filename,
                    "status": "success",
                    "drive_file_id": upload_res.get("id"),
                    "drive_link": upload_res.get("webViewLink"),
                    "message": f"Đã lưu thành công lên Google Drive: {orig_filename}"
                })
            else:
                fail_count += 1
                upload_results.append({
                    "id": file_id,
                    "filename": orig_filename,
                    "status": "error",
                    "message": upload_res.get("message", "Lỗi upload lên Drive")
                })
        except Exception as e:
            fail_count += 1
            upload_results.append({
                "id": file_id,
                "filename": orig_filename,
                "status": "error",
                "message": str(e)
            })
    return jsonify({
        "success": success_count > 0,
        "total": len(files_to_upload),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": upload_results,
        "message": f"Hoàn tất: Đã lưu thành công {success_count}/{len(files_to_upload)} văn bản lên Google Drive!"
    })
@app.route("/api/upload-local-files-to-notebooklm", methods=["POST"])
def upload_local_files_to_notebooklm():
    """
    Lưu danh sách các tệp tin cục bộ đã chọn (Tab 3: PDF, Word, Excel) vào NotebookLM:
    - Sao chép vào thư mục chuyên đề NotebookLM
    - Đồng bộ lên Google Drive nếu kết nối
    - Cập nhật manifest và index
    """
    data = request.json or {}
    files_to_upload = data.get("files", [])
    batch_notebook_id = data.get("selected_notebook_id")
    if not files_to_upload:
        return jsonify({"success": False, "message": "Chưa có tệp tin nào được chọn để lưu vào NotebookLM."}), 400
    results = []
    success_count = 0
    fail_count = 0
    for item in files_to_upload:
        file_id = item.get("id")
        orig_filename = item.get("filename") or item.get("original_name", "tailieu")
        saved_filename = item.get("saved_filename") or f"{file_id}_{orig_filename}"
        target_notebook = item.get("selected_notebook_id") or batch_notebook_id
        target_folder = item.get("selected_folder_id", "root")
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        file_record = {
            "id": file_id,
            "original_name": orig_filename,
            "server_path": file_path,
            "selected_notebook_id": target_notebook,
            "selected_folder_id": target_folder,
            "mimetype": item.get("mimetype") or get_file_mimetype(os.path.splitext(orig_filename)[1])
        }
        res = notebooklm_service.save_local_uploaded_file(file_record, notebook_id=target_notebook)
        results.append(res)
        if res.get("success"):
            success_count += 1
        else:
            fail_count += 1
    return jsonify({
        "success": success_count > 0,
        "total": len(files_to_upload),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
        "message": f"Hoàn tất: Đã lưu thành công {success_count}/{len(files_to_upload)} tệp vào nguồn NotebookLM!"
    })
@app.route("/view-local/<file_id>")
def view_local_file_page(file_id):
    """Trang xem trực tiếp tệp tin nội bộ (Word, Excel, PDF) mượt mà trên trình duyệt mà không bao giờ bị ép tải về"""
    target_fname = None
    target_path = None
    orig_name = None
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(f"{file_id}_") and not fname.endswith("_preview.html"):
            target_fname = fname
            target_path = os.path.join(UPLOAD_DIR, fname)
            orig_name = fname[len(file_id) + 1:]
            break
    if not target_path or not os.path.exists(target_path):
        return render_template(
            "local_file_view.html",
            filename="Tệp không tồn tại",
            file_id=file_id,
            file_ext="",
            file_size_formatted="0 B",
            view_mode="text",
            html_content="",
            excel_sheets={},
            text_content="Không tìm thấy tệp tin trong hệ thống."
        )
    _, ext = os.path.splitext(orig_name)
    ext_low = ext.lower()
    file_size = os.path.getsize(target_path)
    file_size_str = format_file_size(file_size)
    view_mode = "text"
    html_content = ""
    excel_sheets = {}
    text_content = ""
    if ext_low == ".pdf":
        view_mode = "pdf"
    elif ext_low in [".docx", ".doc"]:
        view_mode = "word"
        cache_html_path = os.path.join(UPLOAD_DIR, f"{file_id}_preview.html")
        if os.path.exists(cache_html_path):
            try:
                with open(cache_html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            except Exception:
                html_content = ""
        if not html_content and mammoth and ext_low == ".docx":
            try:
                with open(target_path, "rb") as docx_file:
                    conversion_result = mammoth.convert_to_html(docx_file)
                    html_content = conversion_result.value
                    if html_content:
                        try:
                            with open(cache_html_path, "w", encoding="utf-8") as f:
                                f.write(html_content)
                        except Exception:
                            pass
            except Exception as e:
                print(f"[App] Lỗi chuyển đổi Word docx sang HTML: {e}")
        if not html_content:
            html_content = f"""<div class='text-center p-6'>
                <h3 class='font-bold text-lg text-[#002e5b] mb-2'>{orig_name}</h3>
                <p class='text-sm text-slate-600 mb-4'>Tệp văn bản Word ({file_size_str})</p>
                <div class='p-4 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900'>
                    Tệp tin đã sẵn sàng lưu lên Google Drive hoặc NotebookLM. Bạn có thể bấm nút 'Tải tệp gốc' ở góc trên để mở trực tiếp trong Microsoft Word.
                </div>
            </div>"""
    elif ext_low in [".xlsx", ".xls"]:
        view_mode = "excel"
        if openpyxl and ext_low == ".xlsx":
            try:
                wb = openpyxl.load_workbook(target_path, data_only=True, read_only=True)
                for sname in wb.sheetnames:
                    sheet = wb[sname]
                    s_rows = []
                    for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                        if r_idx >= 500:
                            s_rows.append([f"... Hiển thị tối đa 500 dòng đầu ..."])
                            break
                        if not any(row):
                            continue
                        s_rows.append([str(c) if c is not None else "" for c in row])
                    if s_rows:
                        excel_sheets[sname] = s_rows
            except Exception as e:
                print(f"[App] Lỗi đọc bảng tính Excel: {e}")
    elif ext_low in [".png", ".jpg", ".jpeg", ".webp"]:
        view_mode = "image"
    else:
        view_mode = "text"
        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read(50000)
        except Exception:
            text_content = f"Không thể hiển thị nội dung tệp dạng {ext}."
    return render_template(
        "local_file_view.html",
        file_id=file_id,
        filename=orig_name,
        file_ext=ext_low,
        file_size_formatted=file_size_str,
        view_mode=view_mode,
        html_content=html_content,
        excel_sheets=excel_sheets,
        text_content=text_content
    )
@app.route("/api/raw-local-file/<file_id>", methods=["GET"])
def raw_local_file(file_id):
    """Trả về tệp tin thô (cho iframe PDF hoặc tải file gốc)"""
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(f"{file_id}_") and not fname.endswith("_preview.html"):
            filepath = os.path.join(UPLOAD_DIR, fname)
            orig_name = fname[len(file_id) + 1:]
            _, ext = os.path.splitext(orig_name)
            is_download = request.args.get("download") == "1"
            return send_file(
                filepath,
                mimetype=get_file_mimetype(ext),
                as_attachment=is_download,
                download_name=orig_name
            )
    return "Không tìm thấy tệp tin.", 404
@app.route("/api/preview-local-file/<file_id>", methods=["GET"])
def preview_local_file(file_id):
    """Mở xem trực tiếp tệp tin - chuyển hướng sang trang viewer trực quan để không bị ép tải về"""
    if request.args.get("raw") == "1":
        return raw_local_file(file_id)
    return redirect(f"/view-local/{file_id}")
@app.route("/api/delete-local-file/<file_id>", methods=["POST"])
def delete_local_file(file_id):
    """Xóa tệp tin khỏi bộ nhớ tạm"""
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(f"{file_id}_"):
            try:
                os.remove(os.path.join(UPLOAD_DIR, fname))
            except Exception:
                pass
    return jsonify({"success": True})
# ==================== SOURCE WEBSITES CRUD APIS ====================
@app.route("/api/sources", methods=["GET"])
def get_sources_api():
    """Lấy danh mục các website nguồn dò quét"""
    sources = ConfigManager.get_sources()
    return jsonify({"success": True, "sources": sources})
@app.route("/api/sources", methods=["POST"])
def add_source_api():
    """Thêm website nguồn mới vào danh mục"""
    data = request.json or {}
    domain = data.get("domain", "")
    name = data.get("name", "")
    if not domain:
        return jsonify({"success": False, "message": "Tên miền website không được để trống."}), 400
    res = ConfigManager.add_source(domain, name)
    return jsonify(res)
@app.route("/api/sources/<source_id>", methods=["PUT"])
def update_source_api(source_id):
    """Cập nhật thông tin website nguồn"""
    data = request.json or {}
    domain = data.get("domain", "")
    name = data.get("name", "")
    if not domain:
        return jsonify({"success": False, "message": "Tên miền website không được để trống."}), 400
    res = ConfigManager.update_source(source_id, domain, name)
    return jsonify(res)
@app.route("/api/sources/<source_id>", methods=["DELETE"])
def delete_source_api(source_id):
    """Xóa website nguồn khỏi danh mục"""
    res = ConfigManager.delete_source(source_id)
    return jsonify(res)
@app.route("/api/sources/toggle", methods=["POST"])
def toggle_source_api():
    """Bật/tắt trạng thái website nguồn"""
    data = request.json or {}
    source_id = data.get("source_id", "")
    res = ConfigManager.toggle_source(source_id)
    return jsonify(res)
@app.route("/api/sources/reset", methods=["POST"])
def reset_sources_api():
    """Khôi phục lại danh sách 5 website nguồn mặc định"""
    res = ConfigManager.reset_sources()
    return jsonify({"success": True, "message": "Đã khôi phục danh mục website mặc định.", "sources": res})
@app.route("/api/sources/enable-all", methods=["POST"])
def enable_all_sources_api():
    """Bật tất cả website nguồn cùng lúc"""
    res = ConfigManager.enable_all_sources()
    return jsonify({"success": True, "message": "Đã bật tất cả 5 website nguồn.", "sources": res})
# ==================== BATCH DOWNLOAD ZIP API ====================
@app.route("/api/documents/download-batch-zip", methods=["POST"])
def download_batch_zip():
    """
    Tải về máy toàn bộ các văn bản được tick chọn dưới dạng 1 file ZIP nén duy nhất.
    Mỗi văn bản được đóng gói thành file PDF chuẩn thể thức hành chính Việt Nam.
    """
    data = request.json or {}
    documents = data.get("documents", [])
    if not documents:
        return jsonify({"success": False, "message": "Chưa chọn văn bản nào để tải về."}), 400
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documents:
                # Tải file nội dung đính kèm thực tế
                file_bytes, filename, _ = AttachmentDownloader.get_document_payload(doc)
                zip_file.writestr(filename, file_bytes)
        zip_buffer.seek(0)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"VanBan_PhapLuat_{timestamp}.zip"
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tạo file nén ZIP: {str(e)}"}), 500
@app.route("/view/<doc_id>")
def view_doc_page(doc_id):
    """Trang xem trực tiếp văn bản và file PDF chính thức nguyên gốc"""
    doc = None
    for d in scanner_service.cached_documents:
        if d.get("id") == doc_id:
            doc = d
            break
            
    if not doc:
        catalog = scanner_service._load_initial_catalog()
        for d in catalog:
            if d.get("id") == doc_id:
                doc = d
                break
    if not doc:
        return "Không tìm thấy văn bản trong hệ thống", 404
    # Tạo bản đọc văn bản HTML trực tiếp (từ file Word docx bằng mammoth hoặc format chuẩn hành chính)
    word_html = AttachmentDownloader.get_word_html_preview(doc)
    return render_template("doc_view.html", doc=doc, word_html=word_html)
@app.route("/api/documents/pdf/<doc_id>", methods=["GET"])
def view_doc_pdf(doc_id):
    """Mở và xem trực tiếp file PDF chính thức nguyên gốc trên tab trình duyệt (luôn trả về định dạng application/pdf)"""
    doc = None
    for d in scanner_service.cached_documents:
        if d.get("id") == doc_id:
            doc = d
            break
            
    if not doc:
        catalog = scanner_service._load_initial_catalog()
        for d in catalog:
            if d.get("id") == doc_id:
                doc = d
                break
    if not doc:
        return "Không tìm thấy văn bản trong hệ thống", 404
    try:
        file_bytes, filename, mimetype = AttachmentDownloader.get_document_payload(doc, prefer_ext="pdf")
        return send_file(
            io.BytesIO(file_bytes),
            mimetype="application/pdf",
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        return f"Lỗi tải file PDF: {str(e)}", 500
@app.route("/api/documents/word/<doc_id>", methods=["GET"])
def view_doc_word(doc_id):
    """Tải trực tiếp file Word (.docx / .doc) nguyên gốc về máy tính"""
    doc = None
    for d in scanner_service.cached_documents:
        if d.get("id") == doc_id:
            doc = d
            break
            
    if not doc:
        catalog = scanner_service._load_initial_catalog()
        for d in catalog:
            if d.get("id") == doc_id:
                doc = d
                break
    if not doc:
        return "Không tìm thấy văn bản trong hệ thống", 404
    try:
        file_bytes, filename, mimetype = AttachmentDownloader.get_document_payload(doc, prefer_ext="docx")
        return send_file(
            io.BytesIO(file_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return f"Lỗi tải file Word: {str(e)}", 500
@app.route("/api/documents/download-local/<doc_id>", methods=["POST"])
def download_local_doc(doc_id):
    """Tải trực tiếp file văn bản đính kèm thực tế về máy tính cá nhân"""
    data = request.json or {}
    doc = data.get("document")
    fmt = data.get("format", "pdf")
    if not doc:
        return jsonify({"success": False, "message": "Không có thông tin văn bản"}), 400
    try:
        file_bytes, filename, mimetype = AttachmentDownloader.get_document_payload(doc, prefer_ext=fmt)
        return send_file(
            io.BytesIO(file_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
# ==================== PHÂN HỆ VĂN BẢN HÀNH CHÍNH (NGHỊ ĐỊNH 30/2020/NĐ-CP) ====================
@app.route("/api/config/gemini", methods=["GET"])
def get_gemini_config_api():
    """Lấy cấu hình Gemini AI"""
    return jsonify(ConfigManager.get_gemini_config())
@app.route("/api/config/gemini", methods=["POST"])
def save_gemini_config_api():
    """Lưu cấu hình Gemini AI"""
    data = request.json or {}
    res = ConfigManager.save_gemini_config(data)
    return jsonify(res)
@app.route("/api/gemini/test-connection", methods=["POST"])
def test_gemini_conn():
    """Kiểm tra kết nối Gemini API"""
    data = request.json or {}
    api_key = data.get("api_key")
    model = data.get('model')
    res = admin_doc_service.test_connection(api_key=api_key, model=model)
    return jsonify(res)
@app.route("/api/admin-doc/check", methods=["POST"])
def check_admin_doc():
    """Kiểm tra thể thức, căn lề, font chữ, chính tả theo NĐ 30/2020/NĐ-CP"""
    try:
        raw_text = ""
        meta = {}
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                file_bytes = file.read()
                raw_text, meta = admin_doc_service.extract_text_from_upload(file_bytes, file.filename)
        else:
            data = request.json or {}
            raw_text = data.get("text", "")
            meta = {"filename": "Văn bản nhập trực tiếp", "ext": ".txt"}
        if not raw_text.strip():
            return jsonify({"success": False, "message": "Nội dung văn bản trống hoặc không thể trích xuất text."}), 400
        result = admin_doc_service.check_nd30_format(raw_text, meta)
        result["extracted_text"] = raw_text
        result["extracted_html"] = meta.get("extracted_html", "")
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/ai-fix", methods=["POST"])
def ai_fix_admin_doc():
    """Tự động sửa toàn bộ lỗi và chuẩn hóa thể thức theo NĐ 30 bằng Gemini API"""
    try:
        data = request.json or {}
        text = data.get("text", "")
        issues = data.get("issues", [])
        if not text.strip():
            return jsonify({"success": False, "message": "Văn bản gốc không được để trống."}), 400
        res = admin_doc_service.ai_fix_nd30(text, issues)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/ai-generate", methods=["POST"])
def ai_generate_admin_doc():
    """Soạn thảo văn bản hành chính AI 3 bước chuẩn hanhchanh.ai.vn (hỗ trợ ảnh đính kèm)"""
    try:
        data = request.json or {}
        wizard_data = data.get("wizard_data", {})
        images = data.get("images", [])
        
        if not wizard_data.get("purpose", "").strip() and not wizard_data.get("subject", "").strip() and not images:
            return jsonify({"success": False, "message": "Vui lòng nhập mục đích hoặc tải lên tài liệu/hình ảnh tham khảo."}), 400
        res = admin_doc_service.ai_generate_admin_doc(wizard_data, images=images)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/ai-refine", methods=["POST"])
def ai_refine_admin_doc():
    """Tinh chỉnh văn bản hành chính hiện tại bằng Gemini API"""
    try:
        data = request.json or {}
        current_doc = data.get("current_doc", {})
        refine_prompt = data.get("prompt", "").strip()
        if not refine_prompt:
            return jsonify({"success": False, "message": "Vui lòng nhập nội dung yêu cầu tinh chỉnh."}), 400
        res = admin_doc_service.ai_refine_admin_doc(current_doc, refine_prompt)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/export-word", methods=["POST"])
def export_admin_doc_word():
    """Xuất văn bản hành chính sang file Word (.docx) chuẩn Nghị định 30"""
    try:
        data = request.json or {}
        doc_data = data.get("doc_data", {})
        if not doc_data:
            return jsonify({"success": False, "message": "Dữ liệu văn bản trống."}), 400
        doc_type = doc_data.get("doc_type", "VAN_BAN").replace(" ", "_")
        doc_num = doc_data.get("doc_number", "01").replace("/", "_").replace(" ", "_").replace(":", "")
        filename = f"{doc_type}_{doc_num}.docx"
        stream = admin_doc_service.export_word(doc_data)
        return send_file(
            stream,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/export-pdf", methods=["POST"])
def export_admin_doc_pdf():
    """Xuất văn bản hành chính sang file PDF chuẩn Nghị định 30"""
    try:
        data = request.json or {}
        doc_data = data.get("doc_data", {})
        if not doc_data:
            return jsonify({"success": False, "message": "Dữ liệu văn bản trống."}), 400
        doc_type = doc_data.get("doc_type", "VAN_BAN").replace(" ", "_")
        doc_num = doc_data.get("doc_number", "01").replace("/", "_").replace(" ", "_").replace(":", "")
        filename = f"{doc_type}_{doc_num}.pdf"
        stream = admin_doc_service.export_pdf(doc_data)
        return send_file(
            stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
@app.route("/api/admin-doc/save-drive", methods=["POST"])
def save_admin_doc_to_drive():
    """Lưu văn bản hành chính trực tiếp vào thư mục ____Automation Video____\\Văn thư (cả máy tính và Google Drive)"""
    try:
        data = request.json or {}
        doc_data = data.get("doc_data", {})
        folder_id = data.get("folder_id")
        export_formats = data.get("formats", ["pdf", "docx"])
        
        if not doc_data:
            return jsonify({"success": False, "message": "Dữ liệu văn bản trống."}), 400
        if not drive_service.is_connected:
            return jsonify({"success": False, "message": "Google Drive chưa được kết nối."}), 400

        cfg = ConfigManager.get_gemini_config()
        admin_cfg = ConfigManager.get_admin_doc_config()
        full_cfg = ConfigManager.load_config()
        gdrive_cfg = full_cfg.get("google_drive", {})

        AUTOMATION_VIDEO_VAN_THU_ID = "16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr"
        AUTOMATION_VIDEO_VAN_THU_NAME = "____Automation Video____\\Văn thư"

        folder_ids = data.get("folder_ids")
        if not folder_ids:
            target_folder = folder_id or cfg.get("admin_doc_drive_folder_id") or admin_cfg.get("reference_folder_id") or AUTOMATION_VIDEO_VAN_THU_ID
            folder_ids = [target_folder]

        def resolve_drive_folder_info(fid):
            if fid == AUTOMATION_VIDEO_VAN_THU_ID or fid == "16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr":
                return {"id": fid, "name": AUTOMATION_VIDEO_VAN_THU_NAME, "url": f"https://drive.google.com/drive/folders/{fid}"}
            if not fid or fid == "root":
                return {"id": "root", "name": "Google Drive (My Drive)", "url": "https://drive.google.com/drive/my-drive"}
            if fid == admin_cfg.get("reference_folder_id"):
                name = admin_cfg.get("reference_folder_name") or AUTOMATION_VIDEO_VAN_THU_NAME
                return {"id": fid, "name": name, "url": f"https://drive.google.com/drive/folders/{fid}"}
            if fid == gdrive_cfg.get("default_folder_id"):
                name = gdrive_cfg.get("default_folder_name") or "Tax_Nghiệp vụ thuế"
                return {"id": fid, "name": name, "url": f"https://drive.google.com/drive/folders/{fid}"}
            if fid == cfg.get("admin_doc_drive_folder_id"):
                name = admin_cfg.get("reference_folder_name") or AUTOMATION_VIDEO_VAN_THU_NAME
                return {"id": fid, "name": name, "url": f"https://drive.google.com/drive/folders/{fid}"}
            try:
                if drive_service.service:
                    meta = drive_service.service.files().get(fileId=fid, fields="id, name, webViewLink").execute()
                    name = meta.get("name", fid)
                    url = meta.get("webViewLink", f"https://drive.google.com/drive/folders/{fid}")
                    return {"id": fid, "name": name, "url": url}
            except Exception:
                pass
            return {"id": fid, "name": f"Thư mục Drive ({fid})", "url": f"https://drive.google.com/drive/folders/{fid}"}

        # Chuẩn bị thư mục lưu trên máy tính (local): ____Automation Video____\Văn thư
        local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "____Automation Video____", "Văn thư"))
        os.makedirs(local_dir, exist_ok=True)
        local_saved_files = []

        doc_type = doc_data.get("doc_type", "VAN_BAN").replace(" ", "_")
        doc_num = doc_data.get("doc_number", "01").replace("/", "_").replace(" ", "_").replace(":", "")
        results = []
        for target_folder in folder_ids:
            f_info = resolve_drive_folder_info(target_folder)
            if "docx" in export_formats or "both" in export_formats:
                docx_filename = f"{doc_type}_{doc_num}.docx"
                docx_stream = admin_doc_service.export_word(doc_data)
                docx_bytes = docx_stream.getvalue()

                # Ghi bản Word ra máy tính
                local_docx_path = os.path.join(local_dir, docx_filename)
                try:
                    with open(local_docx_path, "wb") as f_out:
                        f_out.write(docx_bytes)
                    local_saved_files.append({"format": "docx", "filename": docx_filename, "path": local_docx_path})
                except Exception as err:
                    print(f"[SaveAdminDoc] Lỗi ghi file docx local: {err}")

                # Đẩy bản Word lên Google Drive
                docx_res = drive_service.upload_file(
                    docx_bytes, 
                    docx_filename, 
                    folder_id=target_folder,
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                docx_id = docx_res.get("id") if isinstance(docx_res, dict) else None
                docx_view = docx_res.get("webViewLink") if isinstance(docx_res, dict) else None
                if not docx_view and docx_id:
                    docx_view = f"https://drive.google.com/file/d/{docx_id}/view"
                results.append({
                    "format": "docx",
                    "filename": docx_filename,
                    "folder_id": target_folder,
                    "folder_name": f_info["name"],
                    "folder_url": f_info["url"],
                    "drive_result": docx_res,
                    "file_id": docx_id,
                    "view_link": docx_view
                })
            if "pdf" in export_formats or "both" in export_formats:
                pdf_filename = f"{doc_type}_{doc_num}.pdf"
                pdf_stream = admin_doc_service.export_pdf(doc_data)
                pdf_bytes = pdf_stream.getvalue()

                # Ghi bản PDF ra máy tính
                local_pdf_path = os.path.join(local_dir, pdf_filename)
                try:
                    with open(local_pdf_path, "wb") as f_out:
                        f_out.write(pdf_bytes)
                    local_saved_files.append({"format": "pdf", "filename": pdf_filename, "path": local_pdf_path})
                except Exception as err:
                    print(f"[SaveAdminDoc] Lỗi ghi file pdf local: {err}")

                # Đẩy bản PDF lên Google Drive
                pdf_res = drive_service.upload_file(
                    pdf_bytes, 
                    pdf_filename, 
                    folder_id=target_folder,
                    mimetype="application/pdf"
                )
                pdf_id = pdf_res.get("id") if isinstance(pdf_res, dict) else None
                pdf_view = pdf_res.get("webViewLink") if isinstance(pdf_res, dict) else None
                if not pdf_view and pdf_id:
                    pdf_view = f"https://drive.google.com/file/d/{pdf_id}/view"
                results.append({
                    "format": "pdf",
                    "filename": pdf_filename,
                    "folder_id": target_folder,
                    "folder_name": f_info["name"],
                    "folder_url": f_info["url"],
                    "drive_result": pdf_res,
                    "file_id": pdf_id,
                    "view_link": pdf_view
                })

        primary_f_info = resolve_drive_folder_info(folder_ids[0] if folder_ids else "root")
        return jsonify({
            "success": True, 
            "message": f"Đã lưu văn bản hành chính vào thư mục '{primary_f_info['name']}' thành công!",
            "folder_id": primary_f_info["id"],
            "folder_name": primary_f_info["name"],
            "folder_url": primary_f_info["url"],
            "local_folder": local_dir,
            "local_files": local_saved_files,
            "results": results
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
# ==================== DRAFTED DOCUMENTS CRUD APIS ====================
@app.route("/api/admin-doc/drafts", methods=["GET"])
def get_admin_doc_drafts():
    """Lấy danh sách các văn bản đã soạn thảo"""
    drafts = ConfigManager.get_drafted_documents()
    return jsonify({"success": True, "drafts": drafts})
@app.route("/api/admin-doc/drafts", methods=["POST"])
def save_admin_doc_draft():
    """Lưu mới hoặc cập nhật văn bản vào danh sách văn bản đã soạn"""
    data = request.json or {}
    res = ConfigManager.save_drafted_document(data)
    return jsonify(res)
@app.route("/api/admin-doc/drafts/<draft_id>", methods=["DELETE"])
def delete_admin_doc_draft(draft_id):
    """Xóa văn bản khỏi danh sách văn bản đã soạn"""
    res = ConfigManager.delete_drafted_document(draft_id)
    return jsonify(res)

# ==================== LƯU THAM SỐ MẶC ĐỊNH SOẠN THẢO VĂN BẢN (BƯỚC 1 & BƯỚC 2) ====================
@app.route("/api/admin-doc/default-params", methods=["GET"])
def get_composer_default_params_api():
    """Lấy bộ tham số mặc định cho Bước 1 & Bước 2 của chức năng Soạn thảo văn bản"""
    params = ConfigManager.get_composer_default_params()
    return jsonify({"success": True, "params": params})

@app.route("/api/admin-doc/default-params", methods=["POST"])
def save_composer_default_params_api():
    """Lưu toàn bộ thiết lập ở Bước 1 (Thiết lập ban đầu) và Bước 2 (Nội dung AI) thành mặc định"""
    data = request.json or {}
    params = data.get("params", data)
    res = ConfigManager.save_composer_default_params(params)
    return jsonify(res)

# ==================== CẤU HÌNH VĂN BẢN HÀNH CHÍNH (THƯ MỤC DRIVE & ĐỒNG BỘ NOTEBOOKLM + CACHE TOKEN) ====================
@app.route("/api/admin-doc/config", methods=["GET"])
def get_admin_doc_config_api():
    """Lấy cấu hình thư mục Google Drive tham chiếu và NotebookLM tương ứng của Văn bản hành chính"""
    cfg = ConfigManager.get_admin_doc_config()
    return jsonify({"success": True, "config": cfg})

@app.route("/api/admin-doc/config", methods=["POST"])
def save_admin_doc_config_api():
    """Lưu cấu hình thư mục Google Drive tham chiếu của Văn bản hành chính"""
    data = request.json or {}
    res = ConfigManager.save_admin_doc_config(data)
    return jsonify(res)

@app.route("/api/admin-doc/config/files", methods=["GET"])
def list_admin_doc_config_files_api():
    """Liệt kê các file nằm trong thư mục Google Drive được chọn kèm trạng thái Cache tiết kiệm Token"""
    folder_id = request.args.get("folder_id")
    folder_name = request.args.get("folder_name")
    res = admin_doc_service.list_reference_folder_files(folder_id=folder_id, folder_name=folder_name)
    return jsonify(res)

@app.route("/api/admin-doc/config/upload-pdf", methods=["POST"])
def upload_admin_doc_reference_pdf_api():
    """
    Tải bổ sung file PDF lên thư mục quy định:
    1. Mặc định đồng bộ về thư mục đang chọn trong Google Drive.
    2. Mặc định đồng bộ về Notebook có tên trùng với thư mục được chọn trong Google Drive.
    3. Xử lý trích xuất quy định và lưu vào bộ nhớ đệm (Cache) để tiết kiệm Token cho các lần sinh văn bản sau.
    """
    try:
        uploaded_files = request.files.getlist("files")
        if not uploaded_files and "file" in request.files:
            uploaded_files = [request.files["file"]]
        if not uploaded_files:
            return jsonify({"success": False, "message": "Vui lòng chọn ít nhất một tệp PDF để tải lên."}), 400

        admin_cfg = ConfigManager.get_admin_doc_config()
        folder_id = (request.form.get("folder_id") or admin_cfg.get("reference_folder_id") or "").strip()
        raw_folder_name = (request.form.get("folder_name") or admin_cfg.get("reference_folder_name") or "Tax_Nghiệp vụ thuế").strip()
        clean_folder_name = ConfigManager.clean_drive_folder_name(raw_folder_name)

        # Lưu lại cấu hình nếu người dùng đang chọn thư mục mới
        if folder_id:
            ConfigManager.save_admin_doc_config({
                "reference_folder_id": folder_id,
                "reference_folder_name": clean_folder_name,
                "enable_reference_on_generate": admin_cfg.get("enable_reference_on_generate", True),
                "auto_sync_notebooklm": True
            })

        # Đảm bảo Notebook có tên trùng với thư mục được chọn trong Google Drive
        matched_nb = ConfigManager.ensure_notebook_for_folder(clean_folder_name, folder_id)
        nb_folder_path = notebooklm_service.get_notebook_folder(matched_nb)

        if not drive_service.is_connected:
            drive_service.test_connection()

        results = []
        success_count = 0

        for f in uploaded_files:
            if not f or not f.filename:
                continue
            orig_name = f.filename
            ext = os.path.splitext(orig_name)[1].lower()
            if ext not in (".pdf", ".docx", ".doc"):
                continue

            file_bytes = f.read()
            mimetype = get_file_mimetype(ext)

            # 1. Đồng bộ lên thư mục đã chọn trong Google Drive
            drive_file_id = ""
            drive_link = ""
            drive_uploaded = False
            if drive_service.is_connected and folder_id:
                try:
                    up_res = drive_service.upload_file(
                        file_content=file_bytes,
                        filename=orig_name,
                        folder_id=folder_id,
                        mimetype=mimetype
                    )
                    if up_res.get("success"):
                        drive_uploaded = True
                        drive_file_id = up_res.get("id", "")
                        drive_link = up_res.get("webViewLink", "")
                except Exception as ex_drv:
                    print(f"[AdminDocConfig] Lỗi upload lên Drive: {ex_drv}")

            # 2. Đồng bộ về Notebook có tên trùng với thư mục được chọn trong Google Drive
            local_nb_file_path = os.path.join(nb_folder_path, orig_name)
            with open(local_nb_file_path, "wb") as nf:
                nf.write(file_bytes)

            doc_record = {
                "id": drive_file_id or f"local_{orig_name}",
                "doc_number": orig_name,
                "title": orig_name,
                "file_name": orig_name,
                "local_path": local_nb_file_path,
                "drive_link": drive_link,
                "notebook_id": matched_nb["id"],
                "notebook_name": matched_nb["name"]
            }
            notebooklm_service.update_notebook_index(nb_folder_path, matched_nb["name"], doc_record)

            auto_nb_synced = False
            try:
                if NotebookLMAutoService.is_storage_present():
                    auto_status = NotebookLMAutoService.check_status()
                    if auto_status.get("connected"):
                        auto_res = NotebookLMAutoService.upload_file(
                            notebook_name=matched_nb["name"],
                            notebook_id=matched_nb.get("google_notebook_id"),
                            file_path=local_nb_file_path,
                            title=orig_name
                        )
                        if auto_res.get("success"):
                            auto_nb_synced = True
            except Exception as ex_nb_auto:
                print(f"[AdminDocConfig] Auto sync NotebookLM: {ex_nb_auto}")

            # 3. Xử lý AI & Lưu trữ vào bộ nhớ đệm (Cache) ngay để không tốn Token ở các lần sinh văn bản sau
            cache_res = admin_doc_service.process_and_cache_file(
                file_id=drive_file_id or f"local_{orig_name}",
                file_name=orig_name,
                folder_id=folder_id,
                modified_time=datetime.datetime.now().strftime("%Y-%m-%d"),
                file_size=len(file_bytes),
                web_view_link=drive_link,
                file_bytes=file_bytes,
                force=True
            )

            success_count += 1
            results.append({
                "file_name": orig_name,
                "drive_uploaded": drive_uploaded,
                "drive_file_id": drive_file_id,
                "drive_link": drive_link,
                "notebook_name": matched_nb["name"],
                "notebook_synced": True,
                "auto_nb_synced": auto_nb_synced,
                "is_cached": cache_res.get("success", False)
            })

        listing = admin_doc_service.list_reference_folder_files(folder_id=folder_id, folder_name=clean_folder_name)
        return jsonify({
            "success": success_count > 0,
            "uploaded_count": success_count,
            "folder_name": clean_folder_name,
            "notebook_name": matched_nb["name"],
            "results": results,
            "files": listing.get("files", []),
            "total_files": listing.get("total_files", 0),
            "cached_files": listing.get("cached_files", 0),
            "message": f"Đã tải lên {success_count} tệp, đồng bộ vào thư mục Google Drive '{clean_folder_name}', Notebook '{matched_nb['name']}' và lưu bộ nhớ đệm AI (tiết kiệm Token)!"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Lỗi tải tệp quy định: {str(e)}"}), 500

@app.route("/api/admin-doc/config/cache-files", methods=["POST"])
def cache_admin_doc_reference_files_api():
    """
    Xử lý và lưu bộ nhớ đệm (Cache) cho 1 file hoặc toàn bộ các file chưa xử lý trong thư mục Google Drive được chọn
    để các lần sinh văn bản sau không tốn Token đọc lại.
    """
    try:
        data = request.json or {}
        admin_cfg = ConfigManager.get_admin_doc_config()
        folder_id = data.get("folder_id") or admin_cfg.get("reference_folder_id") or ""
        folder_name = ConfigManager.clean_drive_folder_name(data.get("folder_name") or admin_cfg.get("reference_folder_name") or "")
        target_file_id = data.get("file_id")
        force = bool(data.get("force", False))

        listing = admin_doc_service.list_reference_folder_files(folder_id=folder_id, folder_name=folder_name)
        files = listing.get("files", [])

        processed_count = 0
        skipped_cached = 0
        for f_item in files:
            fid = f_item.get("id", "")
            fname = f_item.get("name", "")
            if target_file_id and fid != target_file_id:
                continue
            if f_item.get("is_cached") and not force and not target_file_id:
                skipped_cached += 1
                continue
            res = admin_doc_service.process_and_cache_file(
                file_id=fid,
                file_name=fname,
                folder_id=folder_id,
                modified_time=f_item.get("raw_modified_time", ""),
                file_size=f_item.get("size", 0),
                web_view_link=f_item.get("webViewLink", ""),
                force=force
            )
            if res.get("success"):
                processed_count += 1

        updated_listing = admin_doc_service.list_reference_folder_files(folder_id=folder_id, folder_name=folder_name)
        return jsonify({
            "success": True,
            "processed_count": processed_count,
            "skipped_cached": skipped_cached,
            "files": updated_listing.get("files", []),
            "total_files": updated_listing.get("total_files", 0),
            "cached_files": updated_listing.get("cached_files", 0),
            "message": f"Đã xử lý & lưu Cache thêm {processed_count} tệp (Bỏ qua {skipped_cached} tệp đã có trong Cache để tiết kiệm Token)."
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/drive/selected-folders", methods=["GET"])
def get_selected_drive_folders_api():
    """Lấy danh sách các ID thư mục Google Drive cấp 1 được chọn"""
    ids = ConfigManager.get_selected_drive_folders()
    return jsonify({"success": True, "selected_folder_ids": ids})
@app.route("/api/drive/selected-folders", methods=["POST"])
def save_selected_drive_folders_api():
    """Lưu danh sách các ID thư mục Google Drive cấp 1 được chọn"""
    data = request.json or {}
    ids = data.get("selected_folder_ids", [])
    res = ConfigManager.save_selected_drive_folders(ids)
    return jsonify(res)
# ==================== TRỢ LÝ AI (AI ASSISTANTS) APIS ====================
@app.route("/api/assistants", methods=["GET"])
def get_ai_assistants():
    """Lấy danh sách tất cả các trợ lý AI"""
    assistants = ConfigManager.get_assistants()
    return jsonify({"status": "success", "success": True, "total": len(assistants), "assistants": assistants})
@app.route("/api/assistants", methods=["POST"])
def save_ai_assistant():
    """Lưu mới hoặc cập nhật thông tin trợ lý AI"""
    data = request.json or {}
    res = ConfigManager.save_assistant(data)
    return jsonify(res)
@app.route("/api/assistants/<asst_id>", methods=["DELETE"])
def delete_ai_assistant(asst_id):
    """Xóa một trợ lý AI"""
    res = ConfigManager.delete_assistant(asst_id)
    return jsonify(res)
@app.route("/api/assistants/drive-folders", methods=["GET"])
def get_assistants_drive_folders():
    """Lấy danh sách thư mục cấp 1 trên Google Drive cho Trợ lý AI."""
    if not drive_service.is_connected:
        drive_service.check_connection()
    if not drive_service.is_connected:
        return jsonify({"success": False, "status": "error", "message": "Chưa kết nối Google Drive.", "folders": []})
    tax_only = request.args.get("tax_only", "false").lower() == "true"
    folders = drive_service.list_folders()
    result_folders = []
    for f in folders:
        raw_name = f.get("raw_name") or f.get("name", "").replace("📁 ", "").replace(" ⭐ [Mặc định]", "").strip()
        is_tax = f.get("is_tax", False) or "tax" in raw_name.lower() or "thuế" in raw_name.lower()
        if not tax_only or is_tax:
            result_folders.append({
                "id": f.get("id"),
                "name": raw_name,
                "display_name": f.get("name", raw_name),
                "has_tax": is_tax
            })
    return jsonify({
        "status": "success",
        "success": True,
        "total": len(result_folders),
        "folders": result_folders
    })
@app.route("/api/assistants/<asst_id>/chat", methods=["POST"])
def chat_with_assistant_api(asst_id):
    """
    Gửi câu hỏi và tương tác cùng Trợ lý AI.
    Hỗ trợ:
    - Text câu hỏi
    - Ảnh từ Clipboard (dán Ctrl+V) hoặc đính kèm
    - Đính kèm file PDF, Word (.docx), Excel (.xlsx)
    - Tham chiếu tự động tài liệu Google Drive (Vertex AI Search logic)
    - Thu thập thêm dữ liệu từ Internet (Google Search Grounding)
    """
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "error": "Vui lòng nhập nội dung câu hỏi."}), 400
    conversation_history = data.get("conversation_history", [])
    images = data.get("images", [])
    attachments = data.get("attachments", [])
    enable_web_search = data.get("enable_web_search") # True, False or None
    model_override = data.get("model")
    temperature_override = data.get("temperature")
    drive_folder_ids = data.get("drive_folder_ids")
    filter_tax_only = data.get("filter_tax_only")
    res = assistant_service.chat_with_assistant(
        assistant_id=asst_id,
        message=message,
        conversation_history=conversation_history,
        images=images,
        attachments=attachments,
        enable_web_search_override=enable_web_search,
        model_override=model_override,
        temperature_override=temperature_override,
        drive_folder_ids_override=drive_folder_ids,
        filter_tax_only_override=filter_tax_only
    )
    return jsonify(res)
@app.route("/api/assistants/vertex-search/config", methods=["GET"])
def get_vertex_search_config_api():
    """Lấy cấu hình Vertex AI Search"""
    cfg = ConfigManager.get_vertex_search_config()
    return jsonify({"success": True, "config": cfg})
@app.route("/api/assistants/vertex-search/config", methods=["POST"])
def save_vertex_search_config_api():
    """Lưu cấu hình Vertex AI Search"""
    data = request.json or {}
    res = ConfigManager.save_vertex_search_config(data)
    return jsonify(res)
# ==================== THƯ KÝ AI TIN TỨC (NEWS SECRETARIES) APIS ====================
@app.route("/api/secretaries", methods=["GET"])
def get_secretaries_api():
    """Lấy danh sách tất cả các Thư ký AI tin tức"""
    secretaries = ConfigManager.get_secretaries()
    return jsonify({"status": "success", "success": True, "total": len(secretaries), "secretaries": secretaries})
@app.route("/api/secretaries", methods=["POST"])
def save_secretary_api():
    """Lưu mới hoặc cập nhật Thư ký AI tin tức"""
    data = request.json or {}
    res = ConfigManager.save_secretary(data)
    return jsonify(res)
@app.route("/api/secretaries/<sec_id>", methods=["DELETE"])
def delete_secretary_api(sec_id):
    """Xóa một Thư ký AI tin tức"""
    res = ConfigManager.delete_secretary(sec_id)
    return jsonify(res)
@app.route("/api/secretaries/fairy-tale-characters", methods=["GET"])
def get_fairy_tale_characters_api():
    """Lấy danh sách 10 nhân vật truyện cổ tích Việt Nam"""
    chars = SecretaryService.get_characters()
    return jsonify({"status": "success", "success": True, "characters": chars})

@app.route("/api/secretaries/generate-prompt", methods=["POST"])
def generate_secretary_prompt_api():
    """Dựa vào nội dung Vai trò của thư ký để Gemini tạo ra Nội dung huấn luyện thư ký"""
    data = request.json or {}
    role = data.get("role", "")
    name = data.get("name", "")
    character = data.get("character", "")
    res = SecretaryService.generate_training_instruction(role=role, name=name, character=character)
    return jsonify(res)
@app.route("/api/secretaries/<sec_id>/generate-report", methods=["POST"])
def generate_secretary_report_api(sec_id):
    """Yêu cầu thư ký AI tìm kiếm tin tức trên Internet qua Gemini và lập báo cáo file Word"""
    res = SecretaryService.generate_report(sec_id)
    return jsonify(res)
@app.route("/api/secretaries/<sec_id>/latest-report", methods=["GET"])
def get_secretary_latest_report_api(sec_id):
    """Lấy nội dung file Word báo cáo sau cùng của thư ký"""
    latest = SecretaryService.get_latest_report(sec_id)
    if not latest:
        return jsonify({"success": False, "message": "Chưa có báo cáo nào được tạo."})
    return jsonify({"success": True, "report": latest})
@app.route("/api/secretaries/<sec_id>/reports", methods=["GET"])
def get_secretary_reports_api(sec_id):
    """Lấy danh sách tất cả các báo cáo của thư ký"""
    reports = SecretaryService.list_reports(sec_id)
    return jsonify({"success": True, "total": len(reports), "reports": reports})
@app.route("/api/secretaries/<sec_id>/reports/<path:filename>", methods=["GET"])
def get_secretary_report_api(sec_id, filename):
    """Lấy nội dung chi tiết của một báo cáo lịch sử cụ thể"""
    report = SecretaryService.get_report(sec_id, filename)
    if not report:
        return jsonify({"success": False, "message": "Không tìm thấy báo cáo."}), 404
    return jsonify({"success": True, "report": report})
@app.route("/api/secretaries/<sec_id>/reports/<path:filename>", methods=["DELETE"])
def delete_secretary_report_api(sec_id, filename):
    """Xóa báo cáo đã chọn và đồng thời xóa trên Google Drive"""
    res = SecretaryService.delete_report(sec_id, filename)
    return jsonify(res)
@app.route("/api/secretaries/<sec_id>/download-report/<path:filename>", methods=["GET"])
def download_secretary_report_api(sec_id, filename):
    """Tải tệp Word (.docx) báo cáo của thư ký về máy tính"""
    clean_fn = os.path.basename(filename)
    file_path = os.path.join(REPORTS_DIR, clean_fn)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Tệp báo cáo không tồn tại."}), 404
    
    # Tên tải về hiển thị thân thiện (bỏ prefix nếu có)
    display_name = clean_fn
    if "__" in clean_fn:
        display_name = clean_fn.split("__", 1)[1]
    return send_file(
        file_path,
        as_attachment=True,
        download_name=display_name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
# ==================== BÀI HÁT & VIDEO YOUTUBE GIẢI TRÍ APIS ====================
@app.route("/api/songs", methods=["GET"])
def get_songs_api():
    """Lấy danh sách bài hát giải trí"""
    songs = ConfigManager.get_songs()
    return jsonify({"status": "success", "success": True, "songs": songs})
@app.route("/api/songs", methods=["POST"])
def save_song_api():
    """Thêm mới hoặc cập nhật bài hát giải trí"""
    data = request.json or {}
    res = ConfigManager.save_song(data)
    return jsonify(res)
@app.route("/api/songs/<song_id>", methods=["DELETE"])
def delete_song_api(song_id):
    """Xóa bài hát giải trí"""
    res = ConfigManager.delete_song(song_id)
    return jsonify(res)

# ==================== TỔNG THƯ KÝ & THƯ KÝ NHẮC VIỆC APIS ====================
@app.route("/api/chief-secretary/config", methods=["GET"])
def get_chief_secretary_config_api():
    """Lấy cấu hình Tổng Thư Ký & Thư ký nhắc việc"""
    cfg = ChiefSecretaryService.get_config()
    return jsonify({"status": "success", "success": True, "config": cfg})
@app.route("/api/chief-secretary/config", methods=["POST"])
def save_chief_secretary_config_api():
    """Lưu cấu hình Tổng Thư Ký & Thư ký nhắc việc"""
    data = request.json or {}
    res = ChiefSecretaryService.save_config(data)
    return jsonify(res)
@app.route("/api/chief-secretary/calendar", methods=["GET"])
def get_chief_calendar_api():
    """Lấy danh sách lịch làm việc Google Calendar (Trong ngày / Trong tuần)"""
    filter_range = request.args.get("range", "all")
    res = ChiefSecretaryService.get_calendar_events(filter_range=filter_range)
    return jsonify({
        "status": "success",
        "success": True,
        "events": res["events"],
        "today_events": res["today_events"],
        "week_events": res["week_events"],
        "stats": res["stats"],
        "filter_range": res["filter_range"],
        "source": res["source"],
        "today_date": res.get("today_date"),
        "week_range": res["week_range"]
    })
@app.route("/api/chief-secretary/calendar", methods=["POST"])
def add_chief_calendar_api():
    """Thêm lịch làm việc mới"""
    data = request.json or {}
    res = ChiefSecretaryService.add_calendar_event(data)
    return jsonify(res)
@app.route("/api/chief-secretary/calendar/<event_id>", methods=["DELETE"])
def delete_chief_calendar_api(event_id):
    """Xóa lịch làm việc"""
    res = ChiefSecretaryService.delete_calendar_event(event_id)
    return jsonify(res)
@app.route("/api/chief-secretary/tasks", methods=["GET"])
def get_chief_tasks_api():
    """Lấy danh sách công việc Google Tasks (Trong ngày / Trong tuần)"""
    filter_range = request.args.get("range", "all")
    res = ChiefSecretaryService.get_tasks(filter_range=filter_range)
    return jsonify({
        "status": "success",
        "success": True,
        "tasks": res["tasks"],
        "today_tasks": res["today_tasks"],
        "week_tasks": res["week_tasks"],
        "completed_tasks": res.get("completed_tasks", []),
        "stats": res["stats"],
        "filter_range": res["filter_range"],
        "source": res["source"],
        "today_date": res.get("today_date"),
        "week_range": res["week_range"]
    })
@app.route("/api/chief-secretary/tasks", methods=["POST"])
def add_chief_task_api():
    """Thêm công việc mới"""
    data = request.json or {}
    res = ChiefSecretaryService.add_task(data)
    return jsonify(res)
@app.route("/api/chief-secretary/tasks/<task_id>", methods=["DELETE"])
def delete_chief_task_api(task_id):
    """Xóa công việc"""
    res = ChiefSecretaryService.delete_task(task_id)
    return jsonify(res)
@app.route("/api/chief-secretary/tasks/<task_id>/toggle", methods=["POST"])
def toggle_chief_task_api(task_id):
    """Bật/tắt trạng thái hoàn thành công việc"""
    res = ChiefSecretaryService.toggle_task(task_id)
    return jsonify(res)
@app.route("/api/chief-secretary/sync-google", methods=["POST"])
def sync_chief_google_api():
    """Đồng bộ thời gian thực với Google Calendar và Google Tasks"""
    res = ChiefSecretaryService.sync_google()
    return jsonify(res)
@app.route("/api/chief-secretary/notifications", methods=["GET"])
def get_chief_notifications_api():
    """Lấy danh sách thông báo quả chuông notify"""
    notifs = ChiefSecretaryService.get_notifications()
    unread_count = sum(1 for n in notifs if not n.get("is_read"))
    return jsonify({"status": "success", "success": True, "notifications": notifs, "unread_count": unread_count})
@app.route("/api/chief-secretary/notifications/<notif_id>/read", methods=["POST"])
def mark_chief_notification_read_api(notif_id):
    """Đánh dấu thông báo đã xem (hiển thị nhạt hơn)"""
    res = ChiefSecretaryService.mark_notification_as_read(notif_id)
    return jsonify(res)
@app.route("/api/chief-secretary/notifications/read-all", methods=["POST"])
def mark_all_chief_notifications_read_api():
    """Đánh dấu tất cả thông báo là đã xem"""
    res = ChiefSecretaryService.mark_all_notifications_as_read()
    return jsonify(res)
@app.route("/api/chief-secretary/notifications/<notif_id>/dismiss", methods=["POST"])
def dismiss_chief_notification_api(notif_id):
    """Bỏ qua / Xóa thông báo khỏi quả chuông"""
    res = ChiefSecretaryService.dismiss_notification(notif_id)
    return jsonify(res)
@app.route("/api/chief-secretary/briefing", methods=["GET"])
def get_chief_briefing_api():
    """Tạo câu nói báo cáo của Cô Tấm theo cú pháp quy định và đồng thời gửi tin nhắn thông báo Telegram"""
    b_type = request.args.get("type", "all")
    cal_range = request.args.get("cal_range")
    task_range = request.args.get("task_range")
    briefing = ChiefSecretaryService.generate_briefing(b_type, cal_range=cal_range, task_range=task_range)
    
    # Theo yêu cầu của Sếp Bắc: Đồng thời thực hiện nhắn tin lịch làm việc và công việc đến người dùng qua Telegram
    if TelegramService:
        def _async_send_tg():
            try:
                TelegramService.send_chief_briefing(b_type, cal_range=cal_range, task_range=task_range)
            except Exception as _ex:
                print(f"[Telegram] Lỗi gửi tin nhắn đồng thời: {_ex}")
        threading.Thread(target=_async_send_tg, daemon=True).start()
    return jsonify({"status": "success", "success": True, "briefing": briefing})
@app.route("/api/chief-secretary/kpi", methods=["GET"])
def get_chief_kpi_api():
    """Đánh giá KPI lũy kế từ ngày đến ngày của toàn bộ Thư ký và Trợ lý"""
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    kpi_data = ChiefSecretaryService.evaluate_kpi(date_from, date_to)
    return jsonify({"status": "success", "success": True, "data": kpi_data})
# ==================== TELEGRAM BOT APIS (@BotFather) ====================
@app.route("/api/telegram/config", methods=["GET"])
def get_telegram_config_api():
    """Lấy thông tin cấu hình Telegram Bot"""
    if not TelegramService:
        return jsonify({"success": False, "message": "TelegramService chưa sẵn sàng"})
    return jsonify({"success": True, "status": "success", "config": TelegramService.get_config()})
@app.route("/api/telegram/config", methods=["POST"])
def save_telegram_config_api():
    """Lưu thông tin cấu hình Telegram Bot"""
    if not TelegramService:
        return jsonify({"success": False, "message": "TelegramService chưa sẵn sàng"})
    data = request.get_json() or {}
    bot_token = data.get("bot_token", "")
    chat_id = data.get("chat_id", "")
    enabled = data.get("enabled", True)
    bot_username = data.get("bot_username", "")
    bot_name = data.get("bot_name", "")
    res = TelegramService.save_config(bot_token, chat_id, enabled, bot_username, bot_name)
    return jsonify(res)
@app.route("/api/telegram/test", methods=["POST"])
def test_telegram_connection_api():
    """Kiểm tra kết nối và gửi tin nhắn mẫu đến Telegram"""
    if not TelegramService:
        return jsonify({"success": False, "message": "TelegramService chưa sẵn sàng"})
    data = request.get_json() or {}
    bot_token = data.get("bot_token")
    chat_id = data.get("chat_id")
    res = TelegramService.test_connection(bot_token, chat_id)
    return jsonify(res)
@app.route("/api/telegram/send-briefing", methods=["POST"])
def send_telegram_briefing_api():
    """Gửi báo cáo công việc của Cô Tấm đến Telegram"""
    if not TelegramService:
        return jsonify({"success": False, "message": "TelegramService chưa sẵn sàng"})
    data = request.get_json() or {}
    briefing_type = data.get("type", "all")
    cal_range = data.get("cal_range")
    task_range = data.get("task_range")
    res = TelegramService.send_chief_briefing(briefing_type, cal_range=cal_range, task_range=task_range)
    return jsonify(res)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"\n=========================================================")
    print(f"🚀 MANAGE APP - HỆ THỐNG QUÉT & TẢI VĂN BẢN GOOGLE DRIVE")
    print(f"🌐 Truy cập ứng dụng tại: http://localhost:{port}")
    print(f"=========================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
