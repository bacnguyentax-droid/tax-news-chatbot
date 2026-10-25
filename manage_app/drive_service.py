import os
import sys
import io
import re
import json
from typing import Dict, Any, List, Optional, Tuple

def is_valid_drive_folder(name: str) -> bool:
    """Lọc bỏ các thư mục rác, file ẩn, mã hash, ký tự đặc biệt #, 00, %, thư mục giải trí..."""
    if not name:
        return False
    s = name.strip()
    if s.startswith('.'):
        return False
    # Cho phép các thư mục đặc biệt của hệ thống
    s_lower = s.lower()
    if 'automation video' in s_lower or 'văn thư' in s_lower or 'van thu' in s_lower:
        return True
    if s in ('#', '%', '+', '_', '-', '~', '!', '@', '$', '^', '&', '*', '..', '...', '0', '00'):
        return False
    # Loại bỏ các thư mục chỉ có 1-2 chữ số
    if re.match(r'^\d{1,2}$', s):
        return False
    # Loại bỏ các ký tự ngắn vô nghĩa như %c, +5, %d
    if re.match(r'^[#%+\-_]\w{0,2}$', s):
        return False
    # Loại bỏ chuỗi mã hóa rác như %cI+q6EHQEOGN0Pu6f0ctw, +5yUT564...
    if re.match(r'^[+%][A-Za-z0-9+/=_%-]{4,}$', s):
        return False
    # Loại bỏ các thư mục backup hệ thống, video giải trí hoặc file response
    if s_lower.startswith('takeout') or 'file responses' in s_lower:
        return False
    if 'red rose' in s_lower or 'video bg' in s_lower or 'dựng film' in s_lower:
        return False
    return True

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư viện Google API
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from config_manager import ConfigManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

class DriveService:
    def __init__(self):
        self.service = None
        self.is_connected = False
        self.user_info = {}
        self.folders_cache = []
        self._init_connection()

    def _init_connection(self) -> bool:
        """Tự động kiểm tra và khởi tạo kết nối Google Drive từ file cấu hình sẵn có"""
        if not GOOGLE_API_AVAILABLE:
            print("[DriveService] Thư viện Google API chưa được cài đặt.")
            return False

        creds = None

        # 1. Kiểm tra Service Account
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE, scopes=SCOPES
                )
                self.user_info = {
                    "email": "service-account@gserviceaccount.com",
                    "name": "Google Service Account",
                    "type": "service_account"
                }
            except Exception as e:
                print(f"[DriveService] Lỗi Service Account: {e}")

        # 2. Kiểm tra token.json cục bộ
        if not creds and os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE)
            except Exception as e:
                print(f"[DriveService] Lỗi đọc token.json: {e}")
                creds = None

        # 3. Thử tìm kiếm token từ thư mục liên quan trong workspace nếu chưa có
        if not creds:
            parent_dir = os.path.dirname(BASE_DIR)
            alt_token = os.path.join(parent_dir, "tiktok_pipeline_app", "token.json")
            if os.path.exists(alt_token):
                try:
                    creds = Credentials.from_authorized_user_file(alt_token)
                    # Lưu lại bản sao vào manage_app
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                    print("[DriveService] Đã tự động kế thừa token từ tiktok_pipeline_app!")
                except Exception as e:
                    print(f"[DriveService] Lỗi kế thừa token: {e}")

        # 4. Refresh token nếu hết hạn
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                    f.write(creds.to_json())
                print("[DriveService] Đã tự động làm mới (refresh) Google Drive token.")
            except Exception as e:
                print(f"[DriveService] Lỗi refresh token: {e}")
                creds = None

        # 5. Nếu xác thực hợp lệ
        if creds and creds.valid:
            try:
                self.service = build('drive', 'v3', credentials=creds)
                # Lấy thông tin user
                try:
                    about = self.service.about().get(fields="user(displayName,emailAddress,photoLink),storageQuota").execute()
                    u = about.get('user', {})
                    quota = about.get('storageQuota', {})
                    self.user_info = {
                        "name": u.get("displayName", "Google User"),
                        "email": u.get("emailAddress", ""),
                        "photo": u.get("photoLink", ""),
                        "limit": int(quota.get("limit", 0)),
                        "usage": int(quota.get("usage", 0)),
                        "type": "oauth2"
                    }
                except Exception as e:
                    self.user_info = {"name": "Google Drive User", "email": "Đã kết nối", "type": "oauth2"}

                self.is_connected = True
                print(f"[DriveService] Đã kết nối thành công tài khoản: {self.user_info.get('email')}")
                return True
            except Exception as e:
                print(f"[DriveService] Lỗi tạo client Drive: {e}")

        self.is_connected = False
        return False

    def test_connection(self) -> Dict[str, Any]:
        """Kiểm tra kết nối tới Google Drive và lấy danh sách thư mục"""
        # Thử kết nối lại nếu chưa có
        if not self.service or not self.is_connected:
            self._init_connection()

        if not self.is_connected or not self.service:
            return {
                "success": False,
                "message": "Chưa kết nối được với Google Drive. Vui lòng kiểm tra lại Client ID / Token hoặc nạp file xác thực.",
                "user": None,
                "folders": []
            }

        try:
            # Lấy thông tin tài khoản & hạn mức
            about = self.service.about().get(fields="user(displayName,emailAddress,photoLink),storageQuota").execute()
            user = about.get('user', {})
            quota = about.get('storageQuota', {})

            usage_bytes = int(quota.get('usage', 0))
            limit_bytes = int(quota.get('limit', 0))
            usage_gb = round(usage_bytes / (1024**3), 2)
            limit_gb = round(limit_bytes / (1024**3), 2) if limit_bytes > 0 else 0

            self.user_info = {
                "name": user.get('displayName', 'Google Drive User'),
                "email": user.get('emailAddress', ''),
                "photo": user.get('photoLink', ''),
                "usage_gb": usage_gb,
                "limit_gb": limit_gb,
                "usage_percent": round((usage_bytes / limit_bytes * 100), 1) if limit_bytes > 0 else 0
            }

            # Lấy danh sách thư mục
            folders = self.list_folders()

            # Lưu lại email vào config
            ConfigManager.update_drive_config({
                "user_email": self.user_info["email"],
                "user_name": self.user_info["name"]
            })

            return {
                "success": True,
                "message": f"Kết nối Google Drive thành công! Tài khoản: {self.user_info['name']} ({self.user_info['email']})",
                "user": self.user_info,
                "folders": folders
            }
        except Exception as e:
            self.is_connected = False
            return {
                "success": False,
                "message": f"Lỗi khi kiểm tra kết nối Google Drive: {str(e)}",
                "user": None,
                "folders": []
            }

    def list_folders(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các thư mục phù hợp trên Google Drive, CHỈ hiển thị các thư mục có chứa ký tự 'Tax' trong tên"""
        if not self.service:
            if not self._init_connection():
                return [{
                    "id": "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK",
                    "name": "📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]",
                    "raw_name": "Tax_Nghiệp vụ thuế"
                }]

        try:
            # Query lấy các thư mục gốc trong My Drive với phân trang đầy đủ
            query = "'root' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            root_folders = []
            page_token = None

            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,
                    fields="nextPageToken, files(id, name, webViewLink)",
                    pageToken=page_token
                ).execute()

                root_folders.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            tax_primary = None
            tax_folders = []
            other_folders = []

            for f in root_folders:
                raw_name = f.get("name", "").strip()
                if not is_valid_drive_folder(raw_name):
                    continue

                folder_id = f.get("id")
                web_link = f.get("webViewLink", f"https://drive.google.com/drive/folders/{folder_id}")
                clean_name = raw_name.lstrip('-_ ')
                is_tax = "tax" in raw_name.lower()

                item = {
                    "id": folder_id,
                    "name": f"📁 {raw_name}",
                    "raw_name": raw_name,
                    "clean_name": clean_name,
                    "webViewLink": web_link,
                    "is_tax": is_tax
                }

                # Nhận diện thư mục mặc định: Tax_Nghiệp vụ thuế
                if "nghiệp vụ thuế" in raw_name.lower() or raw_name.lower() == "tax_nghiệp vụ thuế":
                    item["name"] = f"📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]"
                    item["is_tax"] = True
                    tax_primary = item
                elif is_tax:
                    tax_folders.append(item)
                else:
                    other_folders.append(item)

            # Sắp xếp theo tên
            tax_folders.sort(key=lambda x: x["clean_name"].lower())
            other_folders.sort(key=lambda x: x["clean_name"].lower())

            # Xây dựng danh sách hiển thị chuẩn: ưu tiên các thư mục Tax lên đầu, tiếp theo là các thư mục khác
            formatted_folders = []
            if tax_primary:
                formatted_folders.append(tax_primary)
                try:
                    ConfigManager.update_drive_config({
                        "default_folder_id": tax_primary["id"],
                        "default_folder_name": "📁 Tax_Nghiệp vụ thuế"
                    })
                except Exception:
                    pass

            formatted_folders.extend(tax_folders)
            formatted_folders.extend(other_folders)

            # Đảm bảo thư mục "____Automation Video____\Văn thư" luôn có sẵn trong danh sách
            van_thu_id = "16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr"
            if not any(f.get("id") == van_thu_id for f in formatted_folders):
                formatted_folders.insert(1 if len(formatted_folders) > 1 else 0, {
                    "id": van_thu_id,
                    "name": "📁 ____Automation Video____\\Văn thư",
                    "raw_name": "____Automation Video____\\Văn thư",
                    "clean_name": "Automation Video Văn thư",
                    "webViewLink": "https://drive.google.com/drive/folders/16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr",
                    "is_tax": True
                })

            # Dự phòng nếu không có thư mục nào
            if not formatted_folders:
                formatted_folders = [{
                    "id": "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK",
                    "name": "📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]",
                    "raw_name": "Tax_Nghiệp vụ thuế",
                    "is_tax": True
                }]

            self.folders_cache = formatted_folders
            return formatted_folders
        except Exception as e:
            print(f"[DriveService] Lỗi nạp danh sách thư mục: {e}")
            return [{
                "id": "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK",
                "name": "📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]",
                "raw_name": "Tax_Nghiệp vụ thuế"
            }]

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Tạo thư mục mới trên Google Drive"""
        if not self.service and not self._init_connection():
            return {"success": False, "message": "Chưa kết nối Google Drive."}

        try:
            folder_metadata = {
                'name': folder_name.strip(),
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id and parent_id != "root":
                folder_metadata['parents'] = [parent_id]

            created = self.service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()

            # Refresh cache
            self.list_folders()

            return {
                "success": True,
                "message": f"Đã tạo thư mục thành công: '{folder_name}'",
                "folder": {
                    "id": created.get("id"),
                    "name": f"📁 {created.get('name')}",
                    "raw_name": created.get("name"),
                    "webViewLink": created.get("webViewLink")
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Lỗi tạo thư mục: {str(e)}"}

    def upload_file(self, file_content: bytes, filename: str, folder_id: str = "root", mimetype: str = "application/pdf") -> Dict[str, Any]:
        """Tải file lên thư mục Google Drive đã chọn"""
        if not self.service and not self._init_connection():
            return {"success": False, "message": "Chưa kết nối Google Drive."}

        try:
            # Metadata
            file_metadata = {'name': filename}
            if folder_id and folder_id != "root":
                file_metadata['parents'] = [folder_id]

            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mimetype, resumable=True)

            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size'
            ).execute()

            return {
                "success": True,
                "id": uploaded_file.get('id'),
                "name": uploaded_file.get('name'),
                "webViewLink": uploaded_file.get('webViewLink'),
                "message": f"Tải lên thành công: {uploaded_file.get('name')}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi đẩy file lên Google Drive: {str(e)}"
            }

    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Xóa tệp trên Google Drive theo file_id"""
        if not file_id:
            return {"success": False, "message": "Thiếu file_id"}
        if not self.service and not self._init_connection():
            return {"success": False, "message": "Chưa kết nối Google Drive."}
        try:
            self.service.files().delete(fileId=file_id).execute()
            return {"success": True, "message": f"Đã xóa file {file_id} trên Google Drive"}
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg or "notFound" in err_msg:
                return {"success": True, "message": "Tệp đã được xóa trước đó trên Google Drive."}
            return {"success": False, "message": f"Lỗi xóa file trên Google Drive: {err_msg}"}

    def delete_file_by_name(self, filename: str, folder_id: str = None) -> Dict[str, Any]:
        """Tìm và xóa tệp trên Google Drive theo tên trong thư mục"""
        if not self.service and not self._init_connection():
            return {"success": False, "message": "Chưa kết nối Google Drive."}
        try:
            q = f"name = '{filename}' and trashed = false"
            if folder_id:
                q += f" and '{folder_id}' in parents"
            res = self.service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
            files = res.get('files', [])
            deleted_count = 0
            for f in files:
                try:
                    self.service.files().delete(fileId=f['id']).execute()
                    deleted_count += 1
                except Exception:
                    pass
            return {"success": True, "deleted_count": deleted_count}
        except Exception as e:
            return {"success": False, "message": f"Lỗi xóa file theo tên: {str(e)}"}

    def save_oauth_credentials(self, client_id: str, client_secret: str, refresh_token: str = "") -> Dict[str, Any]:
        """Lưu thông tin xác thực OAuth2 thủ công hoặc qua form cấu hình"""
        try:
            # Tạo credentials.json chuẩn format Google
            creds_data = {
                "installed": {
                    "client_id": client_id.strip(),
                    "client_secret": client_secret.strip(),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }
            with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)

            # Nếu có refresh_token, tạo token.json
            if refresh_token.strip():
                token_data = {
                    "client_id": client_id.strip(),
                    "client_secret": client_secret.strip(),
                    "refresh_token": refresh_token.strip(),
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "scopes": SCOPES
                }
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    json.dump(token_data, f, indent=2)

            ConfigManager.update_drive_config({
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip(),
                "refresh_token": refresh_token.strip()
            })

            # Thử khởi tạo lại
            reconnected = self._init_connection()
            return {
                "success": True,
                "connected": reconnected,
                "message": "Đã lưu thông tin cấu hình Google Drive thành công!"
            }
        except Exception as e:
            return {"success": False, "message": f"Lỗi lưu thông tin cấu hình: {str(e)}"}

    def import_local_credentials(self) -> Dict[str, Any]:
        """Tự động tìm kiếm và nạp credentials/token có sẵn từ máy tính"""
        parent_dir = os.path.dirname(BASE_DIR)
        candidates = [
            os.path.join(parent_dir, "tiktok_pipeline_app"),
            parent_dir,
            os.path.expanduser("~")
        ]

        found = False
        imported_token = False
        imported_creds = False

        for c_dir in candidates:
            c_token = os.path.join(c_dir, "token.json")
            c_creds = os.path.join(c_dir, "credentials.json")

            if os.path.exists(c_creds) and not imported_creds:
                try:
                    with open(c_creds, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    imported_creds = True
                    found = True
                except Exception:
                    pass

            if os.path.exists(c_token) and not imported_token:
                try:
                    with open(c_token, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    imported_token = True
                    found = True
                except Exception:
                    pass

            if imported_token and imported_creds:
                break

        if found:
            self._init_connection()
            test_res = self.test_connection()
            return {
                "success": True,
                "message": "Đã tự động phát hiện và nạp cấu hình Google Drive thành công!",
                "test": test_res
            }
        else:
            return {
                "success": False,
                "message": "Không tìm thấy file credentials.json hoặc token.json sẵn có trên máy."
            }

drive_service = DriveService()
