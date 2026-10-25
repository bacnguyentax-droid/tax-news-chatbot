import os
import sys
import io
import json
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import threading
import wsgiref.simple_server

# Thư viện Google API
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _ExclusiveWSGIServer, _WSGIRequestHandler
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")
DRIVE_STATE_FILE = os.path.join(BASE_DIR, "drive_state.json")

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Các cột dữ liệu chuẩn theo đúng file Google Sheet 'Thông tin'
STANDARD_COLUMNS = [
    "STT",             # Cột A
    "Chủ đề",          # Cột B
    "Yêu cầu chủ đề",  # Cột C
    "Nội dung",        # Cột D
    "Hag tag",         # Cột E
    "Loại video",      # Cột F
    "Dạng video",      # Cột G
    "duyệt CĐ và HT",  # Cột H
    "Duyệt nội dung",  # Cột I
    "Tạo video",       # Cột J
    "Duyệt đăng",      # Cột K
    "Đăng bài"         # Cột L
]


LOAI_VIDEO_OPTIONS = [
    "Góc cảnh báo",
    "Hỏi nhanh đáp gọn",
    "Tiện ích thuế",
    "Chính sách thuế",
    "Góc nhìn-chia sẽ",
    "Tin thức thời sự"
]

DANG_VIDEO_OPTIONS = [
    "Ảnh cuộn",
    "Trích video từ youtube",
    "Trên (ảnh), dưới (ảnh)",
    "Trên (ảnh), dưới (video)",
    "Trên (video), dưới (video)",
    "Video với nhân vật ở góc (heygen), nói về nội dung (ảnh) ở khung chính",
    "Video với nhân vật ở góc (heygen), nói về nội dung (video) ở khung chính",
    "Video tạo hoàn toàn từ AI"
]



class GoogleDriveManager:
    def __init__(self):
        self.drive_service = None
        self.sheets_service = None
        self.is_connected = False
        self.user_email = ""
        self.folder_id = None
        self.subfolder_id = None
        self.file_id = None
        self.file_name = ""
        self.file_type = "unknown"  # 'spreadsheet' hoặc 'xlsx'
        self.current_data: List[Dict[str, Any]] = []
        self.columns: List[str] = STANDARD_COLUMNS
        self.connection_message = "Chưa kết nối Google Drive. Vui lòng kết nối để tải dữ liệu."

        # Tự động nạp kết nối từ phiên trước đó nếu đã từng đăng nhập
        self.init_connection()

    def _save_persistent_state(self):
        """Lưu lại thông tin định danh file và thư mục Google Drive để tự động nạp ở các lần mở sau"""
        state = {
            "user_email": self.user_email,
            "folder_id": self.folder_id,
            "subfolder_id": self.subfolder_id,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_type": self.file_type
        }
        try:
            with open(DRIVE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Drive] Lỗi lưu drive_state.json: {e}")

    def _load_persistent_state(self) -> Dict[str, Any]:
        """Đọc lại cấu hình Google Drive từ lần chạy trước"""
        if os.path.exists(DRIVE_STATE_FILE):
            try:
                with open(DRIVE_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Drive] Lỗi đọc drive_state.json: {e}")
        return {}

    def init_connection(self) -> bool:
        """
        Khởi tạo và tự động kết nối lại Google Drive:
        Nếu đã đăng nhập trước đó (có token.json hoặc service_account.json),
        hệ thống tự động kích hoạt và load lại dữ liệu từ Google Drive ngay khi mở web app.
        """
        if not GOOGLE_API_AVAILABLE:
            self.connection_message = "Chưa cài đặt thư viện Google API client."
            self.is_connected = False
            self.current_data = []
            return False

        creds = None
        # 1. Thử Service Account trước nếu có
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE, scopes=SCOPES
                )
                self.user_email = "Service Account"
            except Exception as e:
                print(f"[Drive] Lỗi đọc Service Account: {e}")

        # 2. Thử OAuth Token đã lưu từ phiên trước
        if not creds and os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception as e:
                print(f"[Drive] Lỗi đọc token.json: {e}")
                creds = None

        # Tự động refresh token nếu hết hạn
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w', encoding='utf-8') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"[Drive] Lỗi tự động refresh token: {e}")
                creds = None

        # Nếu đã có thông tin xác thực hợp lệ
        if creds and creds.valid:
            try:
                self.drive_service = build('drive', 'v3', credentials=creds)
                self.sheets_service = build('sheets', 'v4', credentials=creds)
                
                # Lấy thông tin user
                try:
                    about = self.drive_service.about().get(fields="user(emailAddress,displayName)").execute()
                    u = about.get('user', {})
                    self.user_email = f"{u.get('displayName', '')} ({u.get('emailAddress', '')})".strip()
                except Exception:
                    pass

                self.is_connected = True
                print(f"[Drive] Đã tự động kết nối lại tài khoản: {self.user_email}")

                # Nạp thông tin vị trí file từ phiên trước nếu có
                cached_state = self._load_persistent_state()
                if cached_state.get("file_id") and cached_state.get("file_type"):
                    self.folder_id = cached_state.get("folder_id")
                    self.subfolder_id = cached_state.get("subfolder_id")
                    self.file_id = cached_state.get("file_id")
                    self.file_name = cached_state.get("file_name", "Thông tin")
                    self.file_type = cached_state.get("file_type")

                    # Thử đọc trực tiếp file đã lưu
                    loaded = False
                    if self.file_type == "spreadsheet":
                        loaded = self._load_from_google_sheet(self.file_id)
                    elif self.file_type == "xlsx":
                        loaded = self._load_from_drive_xlsx(self.file_id)

                    if loaded:
                        return True

                # Nếu chưa lưu vị trí hoặc file cũ bị đổi, tiến hành quét tìm lại cây thư mục
                return self.locate_file_and_load()
            except Exception as e:
                self.connection_message = f"Lỗi khởi tạo dịch vụ Google: {e}"
                print(self.connection_message)

        # Chưa có xác thực -> KHÔNG đưa dữ liệu test ra
        self.is_connected = False
        self.current_data = []
        self.columns = STANDARD_COLUMNS
        self.file_name = ""
        self.connection_message = "Chưa kết nối Google Drive. Vui lòng kết nối để tải danh sách video."
        return False

    def start_oauth_flow(self) -> Tuple[bool, str]:
        """Khởi động server callback và trả về auth_url trực tiếp cho trình duyệt"""
        if not os.path.exists(CREDENTIALS_FILE):
            return False, "Chưa tìm thấy file 'credentials.json'. Vui lòng nạp file credentials.json từ Google Cloud Console trước."

        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            success_msg = "Xac thuc Google thanh cong! Ban co the dong tab nay va quay lai ung dung TikTok Studio."
            wsgi_app = _RedirectWSGIApp(success_msg)

            local_server = None
            for p in range(8090, 8100):
                try:
                    local_server = wsgiref.simple_server.make_server(
                        "localhost",
                        p,
                        wsgi_app,
                        server_class=_ExclusiveWSGIServer,
                        handler_class=_WSGIRequestHandler,
                    )
                    break
                except OSError:
                    continue

            if not local_server:
                return False, "Không thể mở cổng lắng nghe Google OAuth."

            actual_port = local_server.server_port
            flow.redirect_uri = f"http://localhost:{actual_port}/"
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

            def _wait_for_callback():
                try:
                    local_server.timeout = 180
                    local_server.handle_request()
                    auth_resp = wsgi_app.last_request_uri.replace("http://", "https://")
                    flow.fetch_token(authorization_response=auth_resp)
                    creds = flow.credentials

                    with open(TOKEN_FILE, 'w', encoding='utf-8') as tf:
                        tf.write(creds.to_json())

                    self.drive_service = build('drive', 'v3', credentials=creds)
                    self.sheets_service = build('sheets', 'v4', credentials=creds)
                    try:
                        about = self.drive_service.about().get(fields="user(emailAddress,displayName)").execute()
                        u = about.get('user', {})
                        self.user_email = f"{u.get('displayName', '')} ({u.get('emailAddress', '')})".strip()
                    except Exception:
                        pass

                    self.locate_file_and_load()
                    self.is_connected = True
                    print(f"[OAuth] Đăng nhập Google thành công: {self.user_email}")
                except Exception as ex:
                    print(f"[OAuth] Lỗi xác thực: {ex}")
                finally:
                    try:
                        local_server.server_close()
                    except Exception:
                        pass

            threading.Thread(target=_wait_for_callback, daemon=True).start()
            return True, auth_url

        except Exception as e:
            return False, f"Lỗi khởi tạo OAuth: {str(e)}"

    def locate_file_and_load(self) -> bool:
        """
        Tìm cây thư mục trên Google Drive:
        1. Thư mục cha: '_____Xây dựng video_____'
        2. Thư mục con: 'Tạo video'
        3. File: 'Thông tin' (Google Sheet hoặc .xlsx)
        """
        if not self.drive_service:
            self.current_data = []
            return False

        try:
            # 1. Tìm thư mục cha (Automation Video, Xây dựng video, hoặc tìm trực tiếp 'Tạo video')
            query1 = "(name contains 'Xây dựng video' or name contains 'Automation Video' or name contains 'Xay dung video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res1 = self.drive_service.files().list(q=query1, fields="files(id, name)").execute()
            folders = res1.get('files', [])

            subfolders = []
            if folders:
                self.folder_id = folders[0]['id']
                parent_name = folders[0]['name']
                query2 = f"'{self.folder_id}' in parents and (name contains 'Tạo video' or name contains 'Tao video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                res2 = self.drive_service.files().list(q=query2, fields="files(id, name)").execute()
                subfolders = res2.get('files', [])

            # Nếu chưa tìm thấy qua parent, tìm trực tiếp thư mục 'Tạo video' trên Drive
            if not subfolders:
                query_direct_sub = "(name contains 'Tạo video' or name contains 'Tao video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                res_sub = self.drive_service.files().list(q=query_direct_sub, fields="files(id, name, parents)").execute()
                all_subs = res_sub.get('files', [])
                if all_subs:
                    subfolders = all_subs
                    self.subfolder_id = subfolders[0]['id']
                    sub_name = subfolders[0]['name']
                    if subfolders[0].get('parents'):
                        self.folder_id = subfolders[0]['parents'][0]
                        try:
                            pf = self.drive_service.files().get(fileId=self.folder_id, fields="name").execute()
                            parent_name = pf.get('name', '____Automation Video____')
                        except Exception:
                            parent_name = '____Automation Video____'
                    else:
                        parent_name = '____Automation Video____'

            if not subfolders:
                self.connection_message = "Không tìm thấy thư mục 'Tạo video' hoặc 'Automation Video' trên Google Drive. Bạn có thể bấm 'Tạo cây thư mục mẫu' để tự động tạo."
                self.current_data = []
                return False

            self.subfolder_id = subfolders[0]['id']
            sub_name = subfolders[0]['name']
            if not getattr(self, 'folder_id', None) and subfolders[0].get('parents'):
                self.folder_id = subfolders[0]['parents'][0]
                parent_name = '____Automation Video____'

            # 3. Tìm file Thông tin (hoặc Google Spreadsheet) bên trong 'Tạo video'
            query3 = f"'{self.subfolder_id}' in parents and (name contains 'Thông tin' or name contains 'Thong tin') and trashed = false"
            res3 = self.drive_service.files().list(q=query3, fields="files(id, name, mimeType)").execute()
            files = res3.get('files', [])

            if not files:
                query3_alt = f"'{self.subfolder_id}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
                res3_alt = self.drive_service.files().list(q=query3_alt, fields="files(id, name, mimeType)").execute()
                files = res3_alt.get('files', [])

            if not files:
                self.connection_message = f"Tìm thấy thư mục '{parent_name} / {sub_name}' nhưng chưa có file 'Thông tin'."
                self.current_data = []
                return False

            target = files[0]
            self.file_id = target['id']
            self.file_name = target['name']
            mime = target.get('mimeType', '')

            loaded = False
            if mime == 'application/vnd.google-apps.spreadsheet':
                self.file_type = "spreadsheet"
                loaded = self._load_from_google_sheet(self.file_id)
            else:
                self.file_type = "xlsx"
                loaded = self._load_from_drive_xlsx(self.file_id)

            if loaded:
                self._save_persistent_state()
            return loaded

        except Exception as e:
            self.connection_message = f"Lỗi tìm kiếm trên Google Drive: {e}"
            print(self.connection_message)
            self.current_data = []
            return False

    def _load_from_google_sheet(self, spreadsheet_id: str) -> bool:
        """Đọc toàn bộ dữ liệu từ Google Spreadsheet thực tế"""
        try:
            sheet_meta = self.sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_meta.get('sheets', [])
            if not sheets:
                self.current_data = []
                return False

            sheet_title = sheets[0]['properties']['title']
            res = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_title}'!A1:Z2000"
            ).execute()

            values = res.get('values', [])
            if not values:
                self.columns = STANDARD_COLUMNS
                self.current_data = []
                self.connection_message = f"Google Sheet '{self.file_name}' hiện chưa có dữ liệu."
                return True

            headers = [str(h).strip() for h in values[0]]
            self.columns = headers if len(headers) > 0 else STANDARD_COLUMNS
            
            rows = []
            for idx, row in enumerate(values[1:], start=1):
                item = {}
                for col_idx, col_name in enumerate(self.columns):
                    item[col_name] = row[col_idx] if col_idx < len(row) else ""
                if "STT" not in item or not item["STT"]:
                    item["STT"] = idx

                # Hỗ trợ bí danh cột tương thích với Sheet thực tế của người dùng
                if "Hag tag" in item and "Hashtag" not in item:
                    item["Hashtag"] = item["Hag tag"]
                if "duyệt CĐ và HT" in item:
                    if "Duyệt CĐ" not in item:
                        item["Duyệt CĐ"] = item["duyệt CĐ và HT"]
                    if "HT" not in item:
                        item["HT"] = item["duyệt CĐ và HT"]
                rows.append(item)

            self.current_data = rows
            self.connection_message = f"🟢 Đã tải {len(rows)} dòng từ Google Sheet '{self.file_name}'"
            return True
        except Exception as e:
            print(f"[Drive] Lỗi đọc Google Sheet: {e}")
            self.connection_message = f"Lỗi đọc Google Sheet: {e}"
            self.current_data = []
            return False

    def _load_from_drive_xlsx(self, file_id: str) -> bool:
        """Tải file .xlsx từ Google Drive và nạp vào pandas"""
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            fh.seek(0)
            df = pd.read_excel(fh)
            self.columns = list(df.columns)
            df = df.fillna("")
            self.current_data = df.to_dict(orient="records")
            self.connection_message = f"🟢 Đã tải {len(self.current_data)} dòng từ file Excel Drive '{self.file_name}'"
            return True
        except Exception as e:
            print(f"[Drive] Lỗi đọc Excel từ Drive: {e}")
            self.connection_message = f"Lỗi đọc Excel Drive: {e}"
            self.current_data = []
            return False

    def update_row(self, row_index: int, updated_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Cập nhật dữ liệu 1 dòng trực tiếp vào Google Drive"""
        if not self.is_connected or not self.file_id:
            return False, "Chưa kết nối Google Drive! Vui lòng kết nối để lưu dữ liệu."

        if row_index < 0 or row_index >= len(self.current_data):
            return False, f"Chỉ số dòng không hợp lệ: {row_index}"

        # Cập nhật trong bộ nhớ
        for k, v in updated_data.items():
            self.current_data[row_index][k] = v
            # Đồng bộ hai chiều cho các bí danh cột
            if k == "Hashtag":
                self.current_data[row_index]["Hag tag"] = v
            elif k == "Hag tag":
                self.current_data[row_index]["Hashtag"] = v

            if k == "duyệt CĐ và HT":
                self.current_data[row_index]["Duyệt CĐ"] = v
                self.current_data[row_index]["HT"] = v
            elif k in ("Duyệt CĐ", "HT"):
                cd_val = updated_data.get("Duyệt CĐ", self.current_data[row_index].get("Duyệt CĐ", ""))
                ht_val = updated_data.get("HT", self.current_data[row_index].get("HT", ""))
                self.current_data[row_index]["duyệt CĐ và HT"] = "x" if (cd_val == "x" or ht_val == "x") else ""

        # 1. Nếu là Google Sheet
        if self.file_type == "spreadsheet":
            try:
                meta = self.sheets_service.spreadsheets().get(spreadsheetId=self.file_id).execute()
                sheet_title = meta['sheets'][0]['properties']['title']
                
                sheet_row = row_index + 2  # Dòng 1 là Header
                row_values = []
                for col in self.columns:
                    val = self.current_data[row_index].get(col, "")
                    row_values.append(str(val) if val is not None else "")

                body = {'values': [row_values]}
                range_name = f"'{sheet_title}'!A{sheet_row}:Z{sheet_row}"
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.file_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()

                return True, f"✅ Đã lưu cập nhật dòng {row_index + 1} vào Google Sheet!"
            except Exception as e:
                return False, f"Lỗi cập nhật Google Sheet: {str(e)}"

        # 2. Nếu là file .xlsx trên Google Drive
        elif self.file_type == "xlsx":
            try:
                df = pd.DataFrame(self.current_data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)

                media = MediaIoBaseUpload(
                    output, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    resumable=True
                )
                self.drive_service.files().update(
                    fileId=self.file_id,
                    media_body=media
                ).execute()

                return True, f"✅ Đã lưu cập nhật dòng {row_index + 1} vào file Excel Google Drive!"
            except Exception as e:
                return False, f"Lỗi cập nhật file Excel Google Drive: {str(e)}"

        return False, "Không xác định được loại file trên Google Drive."

    def add_row(self, new_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Thêm một dòng mới và lưu lên Google Drive"""
        if not self.is_connected or not self.file_id:
            return False, "Chưa kết nối Google Drive!"

        new_row = {}
        for col in self.columns:
            new_row[col] = new_data.get(col, "")
        if not new_row.get("STT"):
            new_row["STT"] = len(self.current_data) + 1

        self.current_data.append(new_row)
        return self.save_all()

    def delete_row(self, row_index: int) -> Tuple[bool, str]:
        """Xóa 1 dòng khỏi danh sách trên Google Drive"""
        if not self.is_connected or not self.file_id:
            return False, "Chưa kết nối Google Drive!"

        if row_index < 0 or row_index >= len(self.current_data):
            return False, "Dòng không tồn tại"
        del self.current_data[row_index]
        for idx, r in enumerate(self.current_data, 1):
            r["STT"] = idx
        return self.save_all()

    def save_all(self) -> Tuple[bool, str]:
        """Đồng bộ toàn bộ bảng lên Google Drive"""
        if not self.is_connected or not self.file_id:
            return False, "Chưa kết nối Google Drive!"

        if self.file_type == "spreadsheet":
            try:
                meta = self.sheets_service.spreadsheets().get(spreadsheetId=self.file_id).execute()
                sheet_title = meta['sheets'][0]['properties']['title']

                values = [self.columns]
                for row in self.current_data:
                    values.append([str(row.get(c, "")) for c in self.columns])

                self.sheets_service.spreadsheets().values().clear(
                    spreadsheetId=self.file_id,
                    range=f"'{sheet_title}'!A1:Z2000"
                ).execute()

                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.file_id,
                    range=f"'{sheet_title}'!A1",
                    valueInputOption="USER_ENTERED",
                    body={'values': values}
                ).execute()
                return True, "✅ Đã đồng bộ toàn bộ dữ liệu lên Google Sheet!"
            except Exception as e:
                return False, f"Lỗi đồng bộ Google Sheet: {str(e)}"

        elif self.file_type == "xlsx":
            try:
                df = pd.DataFrame(self.current_data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
                media = MediaIoBaseUpload(
                    output, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    resumable=True
                )
                self.drive_service.files().update(
                    fileId=self.file_id,
                    media_body=media
                ).execute()
                return True, "✅ Đã lưu toàn bộ dữ liệu vào file Excel trên Google Drive!"
            except Exception as e:
                return False, f"Lỗi lưu file Excel Google Drive: {str(e)}"

        return False, "Chưa kết nối Google Drive"

    def create_drive_structure(self) -> Tuple[bool, str]:
        """Tự động tạo cây thư mục: _____Xây dựng video_____ -> Tạo video -> File Thông tin trên Google Drive"""
        if not self.drive_service:
            return False, "Google Drive chưa được xác thực. Vui lòng đăng nhập Google trước."

        try:
            # 1. Tạo thư mục cha _____Xây dựng video_____ nếu chưa có
            parent_id = self.folder_id
            if not parent_id:
                meta_parent = {
                    'name': '_____Xây dựng video_____',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive_service.files().create(body=meta_parent, fields='id').execute()
                parent_id = folder.get('id')
                self.folder_id = parent_id

            # 2. Tạo thư mục con Tạo video
            sub_id = self.subfolder_id
            if not sub_id:
                meta_sub = {
                    'name': 'Tạo video',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                sub = self.drive_service.files().create(body=meta_sub, fields='id').execute()
                sub_id = sub.get('id')
                self.subfolder_id = sub_id

            # 3. Tạo Google Spreadsheet 'Thông tin' nếu chưa có
            if not self.file_id:
                meta_file = {
                    'name': 'Thông tin',
                    'mimeType': 'application/vnd.google-apps.spreadsheet',
                    'parents': [sub_id]
                }
                f = self.drive_service.files().create(body=meta_file, fields='id').execute()
                self.file_id = f.get('id')
                self.file_name = "Thông tin"
                self.file_type = "spreadsheet"

                # Ghi tiêu đề các cột chuẩn
                values = [STANDARD_COLUMNS]
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.file_id,
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED",
                    body={'values': values}
                ).execute()

            self.is_connected = True
            self._save_persistent_state()
            self.locate_file_and_load()
            return True, "🎉 Đã tự động tạo thành công thư mục '_____Xây dựng video_____ / Tạo video' và file 'Thông tin' trên Google Drive của bạn!"
        except Exception as e:
            return False, f"Lỗi tạo cấu trúc trên Google Drive: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái kết nối và file"""
        return {
            "is_connected": self.is_connected,
            "user_email": self.user_email,
            "folder_id": self.folder_id,
            "folder_name": "_____Xây dựng video_____",
            "subfolder_id": self.subfolder_id,
            "subfolder_name": "Tạo video",
            "file_id": self.file_id,
            "file_name": self.file_name or "Thông tin",
            "file_type": self.file_type,
            "connection_message": self.connection_message,
            "has_credentials_file": os.path.exists(CREDENTIALS_FILE),
            "total_rows": len(self.current_data),
            "columns": self.columns
        }
