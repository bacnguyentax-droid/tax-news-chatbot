"""
GOOGLE AUTH SERVICE - Quản lý kết nối Google OAuth 2.0 đa dịch vụ:
- Google Calendar API
- Google Tasks API
- Google Drive API
- Google Spreadsheets API
Phục vụ Thư ký nhắc việc Cô Tấm và Hệ thống Văn bản Quản lý Thuế
Tài khoản bảo trợ: bacnguyentax@gmail.com
"""

import os
import sys

# Cho phép oauthlib chấp nhận scope mở rộng hoặc thay đổi thứ tự từ Google (như openid)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" 
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

CREDENTIALS_FILE = os.path.join(CURRENT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(CURRENT_DIR, "token.json")

ALL_GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    GOOGLE_LIBS_OK = True
except Exception as e:
    GOOGLE_LIBS_OK = False
    print(f"[GoogleAuthService] Thư viện Google API chưa đầy đủ: {e}")


class GoogleAuthService:
    @staticmethod
    def get_credentials() -> Optional[Any]:
        """Tải và kiểm tra tính hợp lệ của Credentials từ token.json"""
        if not GOOGLE_LIBS_OK or not os.path.exists(TOKEN_FILE):
            return None

        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                    print("[GoogleAuthService] Đã tự động làm mới Google Token thành công!")
                except Exception as ref_err:
                    print(f"[GoogleAuthService] Lỗi refresh token: {ref_err}")
                    return None
            return creds if creds and creds.valid else None
        except Exception as e:
            print(f"[GoogleAuthService] Lỗi nạp token.json: {e}")
            return None

    @classmethod
    def get_auth_status(cls) -> Dict[str, Any]:
        """
        Kiểm tra toàn diện trạng thái Google OAuth 2.0:
        - Tồn tại file token.json
        - Trạng thái các Scope: Calendar, Tasks, Drive, Spreadsheets
        - Trạng thái kết nối thời gian thực
        - Nguyên nhân nếu chưa kết nối (Token hết hạn, thiếu quyền...)
        """
        status = {
            "credentials_file_exists": os.path.exists(CREDENTIALS_FILE),
            "token_file_exists": os.path.exists(TOKEN_FILE),
            "google_account": "bacnguyentax@gmail.com",
            "is_connected": False,
            "calendar_connected": False,
            "tasks_connected": False,
            "drive_connected": False,
            "notebooklm_connected": False,
            "active_scopes": [],
            "missing_scopes": [],
            "scope_details": {
                "calendar": False,
                "tasks": False,
                "drive": False,
                "spreadsheets": False
            },
            "error_message": "",
            "diagnostic_code": "OK"
        }

        if not status["credentials_file_exists"]:
            status["error_message"] = "Thiếu file credentials.json cấu hình Client ID & Secret."
            status["diagnostic_code"] = "NO_CREDENTIALS"
            return status

        if not status["token_file_exists"]:
            status["error_message"] = "Chưa có token.json. Vui lòng bấm 'Đăng nhập & Cấp quyền Google' để cấp quyền."
            status["diagnostic_code"] = "NO_TOKEN"
            status["missing_scopes"] = ALL_GOOGLE_SCOPES
            return status

        # Đọc dữ liệu thô từ token.json để phân tích scopes và expiration
        token_data = {}
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                token_data = json.load(f)
        except Exception as e:
            status["error_message"] = f"Lỗi đọc nội dung file token.json: {e}"
            status["diagnostic_code"] = "CORRUPT_TOKEN"
            return status

        scopes_in_file = token_data.get("scopes", [])
        status["active_scopes"] = scopes_in_file

        status["scope_details"]["calendar"] = any("calendar" in s for s in scopes_in_file)
        status["scope_details"]["tasks"] = any("tasks" in s for s in scopes_in_file)
        status["scope_details"]["drive"] = any("drive" in s for s in scopes_in_file)
        status["scope_details"]["spreadsheets"] = any("spreadsheets" in s for s in scopes_in_file)

        missing = []
        if not status["scope_details"]["calendar"]:
            missing.append("https://www.googleapis.com/auth/calendar")
        if not status["scope_details"]["tasks"]:
            missing.append("https://www.googleapis.com/auth/tasks")
        if not status["scope_details"]["drive"]:
            missing.append("https://www.googleapis.com/auth/drive")
        status["missing_scopes"] = missing

        # Thử nạp Credentials và refresh
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                    status["diagnostic_code"] = "TOKEN_REFRESHED"
                except Exception as ref_e:
                    err_str = str(ref_e)
                    if "invalid_grant" in err_str:
                        status["error_message"] = (
                            "Google OAuth 2.0 báo lỗi 'invalid_grant: Token expired or revoked'. "
                            "Refresh token đã hết hạn do ứng dụng Google Cloud đang ở chế độ Testing (hết hạn sau 7 ngày) "
                            "hoặc quyền truy cập đã bị thu hồi. Vui lòng bấm 'Đăng nhập & Cấp quyền Google' để cấp lại quyền mới."
                        )
                        status["diagnostic_code"] = "INVALID_GRANT"
                    else:
                        status["error_message"] = f"Lỗi làm mới token: {err_str}"
                        status["diagnostic_code"] = "REFRESH_FAILED"
                    return status

            if creds.valid:
                # Kiểm tra kết nối thực tế tới Calendar và Tasks
                if status["scope_details"]["calendar"]:
                    try:
                        cal_service = build("calendar", "v3", credentials=creds)
                        # Gọi thử list calendar
                        cal_service.calendarList().list(maxResults=1).execute()
                        status["calendar_connected"] = True
                    except Exception as ce:
                        print(f"[GoogleAuthService] Lỗi gọi Calendar API: {ce}")

                if status["scope_details"]["tasks"]:
                    try:
                        task_service = build("tasks", "v1", credentials=creds)
                        task_service.tasklists().list(maxResults=1).execute()
                        status["tasks_connected"] = True
                    except Exception as te:
                        print(f"[GoogleAuthService] Lỗi gọi Tasks API: {te}")

                if status["scope_details"]["drive"]:
                    status["drive_connected"] = True
                    status["notebooklm_connected"] = True

                status["is_connected"] = status["calendar_connected"] or status["drive_connected"]

                if missing:
                    status["error_message"] = (
                        "Tài khoản Google đã kết nối nhưng THIẾU QUYỀN (Scope) cần thiết. "
                        f"Thiếu: {', '.join(missing)}. "
                        "Do chính sách phân quyền tối thiểu (Least Privilege) của Google OAuth 2.0, "
                        "bạn cần bấm 'Đăng nhập & Cấp quyền Google' để tài khoản bacnguyentax@gmail.com xác nhận cấp thêm quyền Calendar & Tasks."
                    )
                    status["diagnostic_code"] = "MISSING_SCOPES"
                else:
                    status["error_message"] = "Kết nối Google OAuth 2.0 toàn diện thành công!"
                    status["diagnostic_code"] = "SUCCESS"

        except Exception as e:
            status["error_message"] = f"Lỗi xác thực Google Credentials: {e}"
            status["diagnostic_code"] = "AUTH_EXCEPTION"

        return status

    @classmethod
    def generate_auth_url(cls, redirect_uri: str = "http://localhost:5055/oauth2callback") -> Dict[str, Any]:
        """
        Tạo URL đăng nhập Google OAuth 2.0 với đầy đủ cả 4 Scopes:
        - Google Calendar
        - Google Tasks
        - Google Drive
        - Google Spreadsheets
        Thiết lập login_hint='bacnguyentax@gmail.com' và prompt='consent'
        để Google luôn trả về refresh_token mới.
        """
        if not os.path.exists(CREDENTIALS_FILE):
            return {
                "success": False,
                "message": "Không tìm thấy file credentials.json"
            }

        try:
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=ALL_GOOGLE_SCOPES,
                redirect_uri=redirect_uri
            )
            flow.autogenerate_code_verifier = False

            auth_url, state = flow.authorization_url(
                access_type="offline",
                prompt="consent",
                include_granted_scopes="true",
                login_hint="bacnguyentax@gmail.com"
            )

            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "redirect_uri": redirect_uri,
                "account": "bacnguyentax@gmail.com",
                "scopes": ALL_GOOGLE_SCOPES
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi tạo Authorization URL: {str(e)}"
            }

    @classmethod
    def exchange_code(cls, code: str, redirect_uri: str = "http://localhost:5055/oauth2callback") -> Dict[str, Any]:
        """
        Đổi Authorization Code lấy Access & Refresh Token,
        lưu vào token.json và tự động kích hoạt DriveService & ChiefSecretary.
        """
        if not os.path.exists(CREDENTIALS_FILE):
            return {"success": False, "message": "Không tìm thấy file credentials.json"}

        try:
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=ALL_GOOGLE_SCOPES,
                redirect_uri=redirect_uri
            )
            flow.autogenerate_code_verifier = False
            flow.fetch_token(code=code.strip())
            creds = flow.credentials

            # Ghi vào token.json
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

            # Kích hoạt làm mới DriveService nếu có
            try:
                from drive_service import drive_service
                drive_service._init_connection()
            except Exception:
                pass

            return {
                "success": True,
                "message": "Đã cấp quyền và kết nối Google OAuth 2.0 thành công cho tài khoản bacnguyentax@gmail.com!",
                "account": "bacnguyentax@gmail.com",
                "scopes": getattr(creds, "scopes", ALL_GOOGLE_SCOPES)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi đổi mã code xác thực OAuth 2.0: {str(e)}"
            }

    @classmethod
    def save_manual_refresh_token(cls, refresh_token: str) -> Dict[str, Any]:
        """Lưu refresh token nhập thủ công từ người dùng"""
        if not refresh_token.strip():
            return {"success": False, "message": "Refresh token không được để trống."}

        try:
            # Đọc client_id và client_secret từ credentials.json
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            inst = c_data.get("installed") or c_data.get("web") or {}
            client_id = inst.get("client_id", "")
            client_secret = inst.get("client_secret", "")

            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token.strip(),
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ALL_GOOGLE_SCOPES,
                "account": "bacnguyentax@gmail.com"
            }
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)

            # Khởi tạo và kiểm tra
            creds = cls.get_credentials()
            if creds and creds.valid:
                try:
                    from drive_service import drive_service
                    drive_service._init_connection()
                except Exception:
                    pass
                return {
                    "success": True,
                    "message": "Đã lưu Refresh Token và kích hoạt kết nối Google thành công!",
                    "connected": True
                }
            else:
                return {
                    "success": False,
                    "message": "Refresh Token đã lưu nhưng không thể làm mới xác thực với Google. Vui lòng kiểm tra lại token.",
                    "connected": False
                }
        except Exception as e:
            return {"success": False, "message": f"Lỗi lưu Refresh Token: {str(e)}"}


    @classmethod
    def insert_calendar_event(cls, ev_data: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm sự kiện trực tiếp lên Google Calendar API của bacnguyentax@gmail.com"""
        creds = cls.get_credentials()
        if not creds:
            return {"success": False, "message": "Chưa có Google credentials"}
        try:
            service = build("calendar", "v3", credentials=creds)
            date_str = ev_data.get("date", datetime.date.today().strftime("%Y-%m-%d"))
            start_time = ev_data.get("start_time", "08:30")
            end_time = ev_data.get("end_time", "09:30")

            event_body = {
                "summary": ev_data.get("title", "Lịch làm việc CIO"),
                "location": ev_data.get("location", "Phòng họp CIO 3D"),
                "description": ev_data.get("description", ""),
                "start": {
                    "dateTime": f"{date_str}T{start_time}:00+07:00",
                    "timeZone": "Asia/Ho_Chi_Minh"
                },
                "end": {
                    "dateTime": f"{date_str}T{end_time}:00+07:00",
                    "timeZone": "Asia/Ho_Chi_Minh"
                }
            }
            created = service.events().insert(calendarId="primary", body=event_body).execute()
            return {
                "success": True,
                "google_id": created.get("id"),
                "html_link": created.get("htmlLink"),
                "message": "Đã thêm sự kiện lên Google Calendar (bacnguyentax@gmail.com) thành công!"
            }
        except Exception as e:
            return {"success": False, "message": f"Lỗi gọi Google Calendar API: {str(e)}"}

    @classmethod
    def insert_task(cls, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm nhiệm vụ trực tiếp lên Google Tasks API của bacnguyentax@gmail.com"""
        creds = cls.get_credentials()
        if not creds:
            return {"success": False, "message": "Chưa có Google credentials"}
        try:
            service = build("tasks", "v1", credentials=creds)
            tasklists_res = service.tasklists().list(maxResults=1).execute()
            items = tasklists_res.get("items", [])
            tl_id = items[0]["id"] if items else "@default"

            due_date = task_data.get("due_date", datetime.date.today().strftime("%Y-%m-%d"))
            due_time = task_data.get("due_time", "17:00")

            task_body = {
                "title": task_data.get("title", "Nhiệm vụ mới"),
                "notes": task_data.get("notes", ""),
                "due": f"{due_date}T{due_time}:00.000Z"
            }
            created = service.tasks().insert(tasklist=tl_id, body=task_body).execute()
            return {
                "success": True,
                "google_id": created.get("id"),
                "message": "Đã thêm công việc lên Google Tasks (bacnguyentax@gmail.com) thành công!"
            }
        except Exception as e:
            return {"success": False, "message": f"Lỗi gọi Google Tasks API: {str(e)}"}

    @classmethod
    def fetch_live_calendar_events(cls) -> Optional[List[Dict[str, Any]]]:
        """Tải các sự kiện thực tế từ Google Calendar API nếu đã xác thực thành công (bacnguyentax@gmail.com)"""
        creds = cls.get_credentials()
        if not creds:
            return None

        try:
            service = build("calendar", "v3", credentials=creds)
            # Lấy sự kiện từ đầu tuần hiện tại đến hết tuần tới để không sót sự kiện nào trong ngày
            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())
            time_min = datetime.datetime.combine(monday, datetime.time.min).isoformat() + "Z"
            time_max = (datetime.datetime.combine(today + datetime.timedelta(days=14), datetime.time.max)).isoformat() + "Z"

            events_result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            items = events_result.get("items", [])
            parsed_events = []
            for item in items:
                start = item.get("start", {})
                end = item.get("end", {})
                start_dt = start.get("dateTime") or start.get("date") or ""
                end_dt = end.get("dateTime") or end.get("date") or ""

                ev_date = start_dt.split("T")[0] if "T" in str(start_dt) else str(start_dt)
                start_time = start_dt.split("T")[1][:5] if "T" in str(start_dt) else "08:00"
                end_time = end_dt.split("T")[1][:5] if "T" in str(end_dt) else "09:00"

                attendees_list = item.get("attendees", [])
                attendees_str = ", ".join([a.get("displayName") or a.get("email") for a in attendees_list if a.get("email")]) if attendees_list else "CIO Bắc Nguyễn, Ban Điều Hành"

                parsed_events.append({
                    "id": item.get("id"),
                    "title": item.get("summary", "Lịch họp không tên"),
                    "date": ev_date,
                    "time": f"{start_time} - {end_time}",
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": item.get("location") or "Phòng họp Lãnh đạo / Trực tuyến",
                    "attendees": attendees_str,
                    "description": item.get("description", ""),
                    "source": "Google Calendar (bacnguyentax@gmail.com)",
                    "status": item.get("status", "confirmed")
                })
            return parsed_events
        except Exception as e:
            print(f"[GoogleAuthService] Không thể lấy sự kiện Google Calendar trực tiếp: {e}")
            return None

    @classmethod
    def fetch_live_tasks(cls) -> Optional[List[Dict[str, Any]]]:
        """Tải danh sách công việc thực tế từ tất cả các danh mục Google Tasks API (bacnguyentax@gmail.com)"""
        creds = cls.get_credentials()
        if not creds:
            return None

        try:
            service = build("tasks", "v1", credentials=creds)
            tasklists_result = service.tasklists().list(maxResults=50).execute()
            items = tasklists_result.get("items", [])
            if not items:
                return []

            parsed_tasks = []
            for tl in items:
                tl_id = tl.get("id")
                tl_title = tl.get("title", "Việc hôm nay")
                try:
                    tasks_result = service.tasks().list(tasklist=tl_id, maxResults=100, showCompleted=True).execute()
                    task_items = tasks_result.get("items", [])
                    for t in task_items:
                        due = t.get("due", "")
                        due_date = ""
                        due_time = None
                        if due:
                            parts = str(due).split("T")
                            due_date = parts[0]
                            if len(parts) > 1:
                                t_part = parts[1].replace("Z", "")
                                if t_part and not t_part.startswith("00:00:00"):
                                    due_time = t_part[:5]

                        title_str = t.get("title", "Công việc không tên")
                        notes_str = t.get("notes", "")
                        if "15:30" in title_str or "15:30" in notes_str:
                            due_time = "15:30"

                        parsed_tasks.append({
                            "id": t.get("id"),
                            "title": title_str,
                            "due_date": due_date,  # KHÔNG gán mặc định hôm nay nếu không có due!
                            "due_time": due_time,
                            "completed": t.get("status") == "completed",
                            "notes": notes_str,
                            "category": tl_title,
                            "source": f"Google Tasks - {tl_title} (bacnguyentax@gmail.com)"
                        })
                except Exception as ex_list:
                    print(f"[GoogleAuthService] Lỗi khi lấy tasklist {tl_title}: {ex_list}")

            return parsed_tasks
        except Exception as e:
            print(f"[GoogleAuthService] Không thể lấy Google Tasks trực tiếp: {e}")
            return None
