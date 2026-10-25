import os
import sys
import json
import datetime
import subprocess
from typing import Dict, Any, List, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config_manager import ConfigManager
from drive_service import drive_service
from attachment_downloader import AttachmentDownloader
from notebooklm_auto import NotebookLMAutoService

class NotebookLMService:
    @staticmethod
    def get_storage_root() -> str:
        """Lấy thư mục gốc lưu trữ nguồn NotebookLM"""
        storage_dir = ConfigManager.get_notebooklm_storage_dir()
        try:
            os.makedirs(storage_dir, exist_ok=True)
            return storage_dir
        except Exception as e:
            print(f"[NotebookLMService] Không thể tạo {storage_dir}: {e}, dùng thư mục nội bộ")
            fallback = os.path.join(CURRENT_DIR, "notebooklm_sources")
            os.makedirs(fallback, exist_ok=True)
            return fallback

    @staticmethod
    def get_notebook_folder(notebook_dict: Dict[str, Any]) -> str:
        """Lấy đường dẫn thư mục chuyên đề của Notebook cụ thể"""
        root = NotebookLMService.get_storage_root()
        folder_name = notebook_dict.get("folder_name") or notebook_dict.get("name") or "Tax_Nghiệp vụ thuế"
        # Chuẩn hóa tên thư mục hợp lệ trên Windows (loại bỏ ký tự cấm và dấu chấm kết thúc)
        clean_name = folder_name.replace(":", "").replace("/", "_").replace("\\", "_").replace("*", "_").replace("?", "_").replace('"', '').replace("<", "").replace(">", "").replace("|", "").rstrip(". ")
        target_path = os.path.join(root, clean_name)
        os.makedirs(target_path, exist_ok=True)
        return target_path

    @staticmethod
    def update_notebook_index(folder_path: str, notebook_name: str, doc_info: Dict[str, Any]):
        """Cập nhật tệp chỉ mục nguồn _NotebookLM_Sources_Index.txt và _manifest.json trong thư mục"""
        try:
            # 1. Cập nhật _manifest.json
            manifest_file = os.path.join(folder_path, "_manifest.json")
            manifest_data = []
            if os.path.exists(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                except Exception:
                    manifest_data = []
            
            # Kiểm tra xem tài liệu đã có trong manifest chưa
            exists = False
            for item in manifest_data:
                if item.get("doc_number") == doc_info.get("doc_number") or item.get("file_name") == doc_info.get("file_name"):
                    item.update(doc_info)
                    item["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    exists = True
                    break
            
            if not exists:
                doc_record = doc_info.copy()
                doc_record["added_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                manifest_data.append(doc_record)

            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, ensure_ascii=False, indent=2)

            # 2. Cập nhật _NotebookLM_Sources_Index.txt trực quan cho người dùng xem và import
            index_txt_file = os.path.join(folder_path, "_NotebookLM_Sources_Index.txt")
            with open(index_txt_file, "w", encoding="utf-8") as f:
                f.write(f"================================================================================\n")
                f.write(f"KHO NGUỒN TRI THỨC NOTEBOOKLM: {notebook_name.upper()}\n")
                f.write(f"Cập nhật lúc: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Tổng số văn bản nguồn: {len(manifest_data)}\n")
                f.write(f"================================================================================\n\n")
                
                for idx, item in enumerate(manifest_data, 1):
                    f.write(f"{idx}. {item.get('doc_number', 'Văn bản')} - {item.get('title', 'Tài liệu')}\n")
                    f.write(f"   • Tệp tin: {item.get('file_name')}\n")
                    f.write(f"   • Cơ quan ban hành: {item.get('issuing_body', 'N/A')} | Ngày ban hành: {item.get('issue_date', 'N/A')}\n")
                    if item.get('summary'):
                        f.write(f"   • Trích yếu: {item.get('summary')[:180]}...\n")
                    if item.get('drive_link'):
                        f.write(f"   • Google Drive link: {item.get('drive_link')}\n")
                    f.write(f"--------------------------------------------------------------------------------\n")
        except Exception as e:
            print(f"[NotebookLMService] Lỗi cập nhật index: {e}")

    @staticmethod
    def save_scanned_document(doc: Dict[str, Any], notebook_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Lưu văn bản quét từ web (Tab 1) vào NotebookLM:
        - Tải file PDF/Word chuẩn xác thực tế
        - Lưu vào thư mục máy tính C:/NotebookLM_Sources/<Notebook_Folder>/
        - Tự động sync/upload lên Google Drive (nếu đã kết nối)
        - Cập nhật manifest và index
        """
        notebooks = ConfigManager.get_notebooks()
        selected_nb = None
        target_nb_id = notebook_id or doc.get("selected_notebook_id") or ConfigManager.get_default_notebook_id()
        
        for nb in notebooks:
            if nb.get("id") == target_nb_id:
                selected_nb = nb
                break
        
        if not selected_nb:
            selected_nb = notebooks[0] if notebooks else {
                "id": "nb_tax_default",
                "name": "Tax_Nghiệp vụ thuế",
                "url": "https://notebooklm.google.com/",
                "folder_name": "Tax_Nghiệp vụ thuế"
            }

        doc_id = doc.get("id", "doc")
        doc_number = doc.get("doc_number", "VB")
        title = doc.get("title", doc_number)
        
        try:
            # 1. Lấy dữ liệu file văn bản thực tế (PDF/Word)
            file_bytes, filename, mimetype = AttachmentDownloader.get_document_payload(doc)

            # 2. Lưu vào thư mục chuyên đề NotebookLM trên máy
            notebook_folder = NotebookLMService.get_notebook_folder(selected_nb)
            local_file_path = os.path.join(notebook_folder, filename)
            
            with open(local_file_path, "wb") as f:
                f.write(file_bytes)

            # 3. Nếu Google Drive kết nối, đồng bộ file lên Google Drive
            drive_link = ""
            drive_file_id = ""
            if drive_service.is_connected:
                target_folder_id = doc.get("selected_folder_id")
                if not target_folder_id or target_folder_id == "root":
                    default_cfg_fid = ConfigManager.load_config().get("google_drive", {}).get("default_folder_id")
                    target_folder_id = default_cfg_fid or "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK"
                try:
                    drive_res = drive_service.upload_file(
                        file_content=file_bytes,
                        filename=filename,
                        folder_id=target_folder_id,
                        mimetype=mimetype
                    )
                    if drive_res.get("success"):
                        drive_link = drive_res.get("webViewLink", "")
                        drive_file_id = drive_res.get("id", "")
                except Exception as ex_drive:
                    print(f"[NotebookLMService] Lưu Drive phụ: {ex_drive}")

            # 4. Cập nhật chỉ mục văn bản nguồn của Notebook
            doc_record = {
                "id": doc_id,
                "doc_number": doc_number,
                "title": title,
                "issuing_body": doc.get("issuing_body", ""),
                "issue_date": doc.get("issue_date", ""),
                "summary": doc.get("summary", ""),
                "file_name": filename,
                "local_path": local_file_path,
                "drive_link": drive_link,
                "notebook_id": selected_nb["id"],
                "notebook_name": selected_nb["name"]
            }
            NotebookLMService.update_notebook_index(notebook_folder, selected_nb["name"], doc_record)

            # 5. Tự động nạp trực tiếp vào Google NotebookLM nếu đã kết nối tự động 100%
            auto_uploaded = False
            auto_res = {}
            try:
                if NotebookLMAutoService.is_storage_present():
                    auto_status = NotebookLMAutoService.check_status()
                    if auto_status.get("connected"):
                        auto_res = NotebookLMAutoService.upload_file(
                            notebook_name=selected_nb["name"],
                            notebook_id=selected_nb.get("google_notebook_id"),
                            file_path=local_file_path,
                            title=f"{doc_number} - {title[:70]}"
                        )
                        if auto_res.get("success"):
                            auto_uploaded = True
            except Exception as ex_auto:
                print(f"[NotebookLMService] Auto upload: {ex_auto}")

            final_nb_url = auto_res.get("notebook_url") or selected_nb.get("url", "https://notebooklm.google.com/")
            return {
                "success": True,
                "id": doc_id,
                "doc_number": doc_number,
                "file_name": filename,
                "notebook_id": selected_nb["id"],
                "notebook_name": selected_nb["name"],
                "notebook_url": final_nb_url,
                "local_path": local_file_path,
                "notebook_folder": notebook_folder,
                "drive_link": drive_link,
                "auto_uploaded": auto_uploaded,
                "auto_message": auto_res.get("message", ""),
                "message": f"Đã lưu thành công vào '{selected_nb['name']}'" + (" (Đã nạp trực tiếp vào NotebookLM 100%!)" if auto_uploaded else "")
            }
        except Exception as e:
            print(f"[NotebookLMService] Lỗi lưu văn bản {doc_number}: {e}")
            return {
                "success": False,
                "id": doc_id,
                "doc_number": doc_number,
                "message": f"Lỗi lưu văn bản: {str(e)}"
            }

    @staticmethod
    def save_local_uploaded_file(file_record: Dict[str, Any], notebook_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Lưu tệp tải lên từ máy tính (Tab 3: PDF, Word, Excel) vào NotebookLM:
        - Sao chép vào thư mục chuyên đề NotebookLM
        - Đồng bộ lên Google Drive (nếu có)
        - Cập nhật manifest và index
        """
        notebooks = ConfigManager.get_notebooks()
        selected_nb = None
        target_nb_id = notebook_id or file_record.get("selected_notebook_id") or ConfigManager.get_default_notebook_id()
        
        for nb in notebooks:
            if nb.get("id") == target_nb_id:
                selected_nb = nb
                break
        
        if not selected_nb:
            selected_nb = notebooks[0] if notebooks else {
                "id": "nb_tax_default",
                "name": "Tax_Nghiệp vụ thuế",
                "url": "https://notebooklm.google.com/",
                "folder_name": "Tax_Nghiệp vụ thuế"
            }

        file_id = file_record.get("id")
        orig_name = file_record.get("original_name") or file_record.get("file_name", "Tài liệu")
        server_path = file_record.get("server_path")
        
        if not server_path or not os.path.exists(server_path):
            return {
                "success": False,
                "id": file_id,
                "file_name": orig_name,
                "message": "Không tìm thấy tệp gốc trên máy chủ."
            }

        try:
            with open(server_path, "rb") as f:
                file_bytes = f.read()

            notebook_folder = NotebookLMService.get_notebook_folder(selected_nb)
            dest_file_path = os.path.join(notebook_folder, orig_name)
            
            with open(dest_file_path, "wb") as f:
                f.write(file_bytes)

            # Đồng bộ Google Drive nếu kết nối
            drive_link = ""
            if drive_service.is_connected:
                target_folder_id = file_record.get("selected_folder_id") or "root"
                try:
                    drive_res = drive_service.upload_file(
                        file_content=file_bytes,
                        filename=orig_name,
                        folder_id=target_folder_id,
                        mimetype=file_record.get("mimetype", "application/octet-stream")
                    )
                    if drive_res.get("success"):
                        drive_link = drive_res.get("webViewLink", "")
                except Exception as ex_drive:
                    print(f"[NotebookLMService] Upload local file to Drive: {ex_drive}")

            # Cập nhật manifest
            doc_record = {
                "id": file_id,
                "doc_number": orig_name,
                "title": orig_name,
                "file_name": orig_name,
                "local_path": dest_file_path,
                "drive_link": drive_link,
                "notebook_id": selected_nb["id"],
                "notebook_name": selected_nb["name"]
            }
            NotebookLMService.update_notebook_index(notebook_folder, selected_nb["name"], doc_record)

            # 5. Tự động nạp trực tiếp vào Google NotebookLM nếu đã kết nối tự động 100%
            auto_uploaded = False
            auto_res = {}
            try:
                if NotebookLMAutoService.is_storage_present():
                    auto_status = NotebookLMAutoService.check_status()
                    if auto_status.get("connected"):
                        auto_res = NotebookLMAutoService.upload_file(
                            notebook_name=selected_nb["name"],
                            notebook_id=selected_nb.get("google_notebook_id"),
                            file_path=dest_file_path,
                            title=orig_name
                        )
                        if auto_res.get("success"):
                            auto_uploaded = True
            except Exception as ex_auto:
                print(f"[NotebookLMService] Auto upload local: {ex_auto}")

            final_nb_url = auto_res.get("notebook_url") or selected_nb.get("url", "https://notebooklm.google.com/")
            return {
                "success": True,
                "id": file_id,
                "file_name": orig_name,
                "notebook_id": selected_nb["id"],
                "notebook_name": selected_nb["name"],
                "notebook_url": final_nb_url,
                "local_path": dest_file_path,
                "notebook_folder": notebook_folder,
                "drive_link": drive_link,
                "auto_uploaded": auto_uploaded,
                "auto_message": auto_res.get("message", ""),
                "message": f"Đã lưu thành công vào '{selected_nb['name']}'" + (" (Đã nạp trực tiếp vào NotebookLM 100%!)" if auto_uploaded else "")
            }
        except Exception as e:
            print(f"[NotebookLMService] Lỗi lưu local file {orig_name}: {e}")
            return {
                "success": False,
                "id": file_id,
                "file_name": orig_name,
                "message": f"Lỗi lưu file: {str(e)}"
            }

    @staticmethod
    def open_storage_folder(subfolder: Optional[str] = None) -> bool:
        """Mở thư mục lưu trữ NotebookLM trên Windows Explorer"""
        target = subfolder if (subfolder and os.path.exists(subfolder)) else NotebookLMService.get_storage_root()
        try:
            if sys.platform == "win32":
                os.startfile(target)
                return True
            else:
                subprocess.Popen(["xdg-open", target])
                return True
        except Exception as e:
            print(f"[NotebookLMService] Lỗi mở Explorer: {e}")
            return False

notebooklm_service = NotebookLMService()
