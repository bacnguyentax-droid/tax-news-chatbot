import os
import sys
import json
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config_manager import ConfigManager

class NotebookLMAutoService:
    @staticmethod
    def get_storage_path() -> Path:
        """Đường dẫn tệp lưu trữ phiên đăng nhập NotebookLM"""
        try:
            from notebooklm import auth
            return auth.get_storage_path()
        except Exception:
            user_home = Path.home()
            return user_home / ".notebooklm" / "profiles" / "default" / "storage_state.json"

    @staticmethod
    def is_storage_present() -> bool:
        """Kiểm tra tệp phiên đăng nhập có tồn tại trên máy không"""
        p = NotebookLMAutoService.get_storage_path()
        return p.exists() and p.stat().st_size > 100

    @staticmethod
    async def _async_check_status() -> Dict[str, Any]:
        """Kiểm tra xác thực trực tiếp với Google NotebookLM qua async API"""
        from notebooklm import NotebookLMClient
        try:
            async with NotebookLMClient.from_storage() as client:
                email = await client.get_account_email()
                return {
                    "connected": True,
                    "email": email or "Google Account",
                    "message": f"Đã kết nối tài khoản Google ({email})" if email else "Đã kết nối với Google NotebookLM"
                }
        except Exception as e:
            err_msg = str(e)
            return {
                "connected": False,
                "email": "",
                "error": err_msg,
                "message": "Chưa kết nối hoặc phiên đăng nhập đã hết hạn. Vui lòng bấm 'Đăng nhập Google NotebookLM'."
            }

    @staticmethod
    def check_status() -> Dict[str, Any]:
        """Kiểm tra trạng thái kết nối tự động (Sync wrapper)"""
        if not NotebookLMAutoService.is_storage_present():
            return {
                "connected": False,
                "email": "",
                "message": "Chưa có phiên đăng nhập Google NotebookLM trên máy."
            }
        try:
            return asyncio.run(NotebookLMAutoService._async_check_status())
        except Exception as e:
            return {
                "connected": False,
                "email": "",
                "error": str(e),
                "message": "Chưa kết nối với NotebookLM."
            }

    @staticmethod
    def start_login_browser(browser: str = "msedge") -> Dict[str, Any]:
        """
        Khởi chạy trình duyệt đăng nhập Google một lần duy nhất.
        Sau khi người dùng đăng nhập tài khoản Google thành công,
        cửa sổ sẽ tự động đóng và lưu session vào máy.
        """
        try:
            # Dọn dẹp tiến trình Playwright cũ nếu có bị kẹt
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*ms-playwright*' } | Stop-Process -Force"],
                        capture_output=True,
                        timeout=5
                    )
            except Exception:
                pass

            bat_path = os.path.abspath(os.path.join(CURRENT_DIR, "..", "Dang_Nhap_NotebookLM.bat"))
            if os.path.exists(bat_path):
                subprocess.Popen(
                    f'cmd.exe /c start "" "{bat_path}"',
                    shell=True
                )
            else:
                use_browser = browser if browser in ["msedge", "chrome"] else "msedge"
                cmd = [sys.executable, "-m", "notebooklm", "login", "--browser", use_browser]
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )

            return {
                "success": True,
                "message": "Cửa sổ đăng nhập Google NotebookLM đang được mở trên màn hình. Quý khách vui lòng chọn hoặc đăng nhập tài khoản Google của mình."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Không thể khởi chạy cửa sổ đăng nhập: {str(e)}"
            }

    @staticmethod
    async def _async_sync_notebooks() -> Dict[str, Any]:
        """Lấy danh sách Notebook thật từ tài khoản Google NotebookLM và đồng bộ vào config.json"""
        from notebooklm import NotebookLMClient
        try:
            async with NotebookLMClient.from_storage() as client:
                google_notebooks = await client.notebooks.list()
                
                # Đọc danh sách hiện tại từ config
                current_nbs = ConfigManager.get_notebooks()
                
                matched_count = 0
                for g_nb in google_notebooks:
                    g_title = g_nb.title.strip()
                    g_id = g_nb.id
                    
                    found = False
                    for c_nb in current_nbs:
                        if c_nb.get("name", "").strip().lower() == g_title.lower():
                            c_nb["google_notebook_id"] = g_id
                            c_nb["sources_count"] = getattr(g_nb, "sources_count", 0)
                            c_nb["url"] = f"https://notebooklm.google.com/notebook/{g_id}"
                            found = True
                            matched_count += 1
                            break
                    
                    # Nếu trên Google có notebook mà local chưa có, thêm mới
                    if not found:
                        new_item = {
                            "id": f"nb_{g_id[:8]}",
                            "name": g_title,
                            "google_notebook_id": g_id,
                            "url": f"https://notebooklm.google.com/notebook/{g_id}",
                            "folder_name": g_title,
                            "description": f"Đồng bộ từ Google NotebookLM ({getattr(g_nb, 'sources_count', 0)} nguồn)",
                            "is_default": False
                        }
                        current_nbs.append(new_item)

                ConfigManager.save_notebooks(current_nbs)
                return {
                    "success": True,
                    "total_google": len(google_notebooks),
                    "matched": matched_count,
                    "notebooks": current_nbs,
                    "message": f"Đã đồng bộ thành công {len(google_notebooks)} sổ ghi chú từ Google NotebookLM!"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Lỗi đồng bộ sổ ghi chú từ Google: {str(e)}"
            }

    @staticmethod
    def sync_notebooks() -> Dict[str, Any]:
        """Đồng bộ Notebooks từ Google (Sync wrapper)"""
        try:
            return asyncio.run(NotebookLMAutoService._async_sync_notebooks())
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    async def _async_upload_file(notebook_name: str, notebook_id: Optional[str], file_path: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Tự động nạp trực tiếp file vào Sổ ghi chú trên Google NotebookLM 100%"""
        from notebooklm import NotebookLMClient
        try:
            if not os.path.exists(file_path):
                return {"success": False, "message": f"Tệp tin không tồn tại: {file_path}"}

            async with NotebookLMClient.from_storage() as client:
                # 1. Tìm sổ ghi chú trên Google
                google_notebooks = await client.notebooks.list()
                target_nb = None

                # Thử tìm theo google_notebook_id trước
                if notebook_id:
                    for nb in google_notebooks:
                        if nb.id == notebook_id:
                            target_nb = nb
                            break

                # Nếu chưa tìm thấy, tìm theo tiêu đề
                if not target_nb and notebook_name:
                    clean_target = notebook_name.strip().lower()
                    for nb in google_notebooks:
                        if nb.title.strip().lower() == clean_target:
                            target_nb = nb
                            break

                # Nếu vẫn chưa tìm thấy, tự động tạo mới sổ ghi chú trên Google
                if not target_nb:
                    create_title = notebook_name or "Tax_Nghiệp vụ thuế"
                    target_nb = await client.notebooks.create(create_title)

                # 2. Đẩy trực tiếp tệp tin vào sổ ghi chú trên Google NotebookLM
                file_title = title or os.path.basename(file_path)
                source = await client.sources.add_file(
                    notebook_id=target_nb.id,
                    file_path=file_path,
                    title=file_title,
                    wait=False
                )

                notebook_url = f"https://notebooklm.google.com/notebook/{target_nb.id}"
                return {
                    "success": True,
                    "auto_uploaded": True,
                    "google_notebook_id": target_nb.id,
                    "notebook_title": target_nb.title,
                    "notebook_url": notebook_url,
                    "source_id": getattr(source, "id", ""),
                    "source_title": getattr(source, "title", file_title),
                    "message": f"Đã tự động nạp thẳng tệp vào Sổ ghi chú '{target_nb.title}' trên Google NotebookLM 100%!"
                }
        except Exception as e:
            return {
                "success": False,
                "auto_uploaded": False,
                "error": str(e),
                "message": f"Lỗi tự động đẩy file lên NotebookLM: {str(e)}"
            }

    @staticmethod
    def upload_file(notebook_name: str, notebook_id: Optional[str], file_path: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Tự động nạp file vào Google NotebookLM (Sync wrapper)"""
        try:
            return asyncio.run(NotebookLMAutoService._async_upload_file(notebook_name, notebook_id, file_path, title))
        except Exception as e:
            return {
                "success": False,
                "auto_uploaded": False,
                "error": str(e),
                "message": f"Lỗi thực thi tự động hóa: {str(e)}"
            }

notebooklm_auto_service = NotebookLMAutoService()
