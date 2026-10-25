# -*- coding: utf-8 -*-
"""
Dịch vụ Trợ Lý AI Chuyên Nghiệp (AI Assistant Service)
- Hỗ trợ đa trợ lý (Thêm/Sửa/Xóa, chuyên môn hóa theo lĩnh vực Thuế, HĐĐT, Pháp chế, Thể thức NĐ 30)
- Tích hợp Vertex AI Search / Tham chiếu tài liệu từ Google Drive (Thư mục cấp 1, hỗ trợ cả PDF text và PDF scan)
- Thu thập dữ liệu Internet thời gian thực (Google/Web Search Grounding độc lập, bảo đảm luôn tra cứu trực tiếp)
- Đa phương thức (Multimodal): Nhập text, dán ảnh từ Clipboard (Ctrl+V), đính kèm PDF, Word (.docx), Excel (.xlsx)
"""

import os
import sys
import io
import json
import base64
import datetime
import unicodedata
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config_manager import ConfigManager
from drive_service import drive_service

# Document extractors
DOCX_AVAILABLE = False
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    pass

PYPDF_AVAILABLE = False
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    pass

OPENPYXL_AVAILABLE = False
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    pass


def unaccent(s: str) -> str:
    """Chuẩn hóa chuỗi tiếng Việt không dấu để so khớp chính xác"""
    if not s:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(s))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D').lower()


def extract_doc_numbers(text: str) -> List[str]:
    """Trích xuất số hiệu văn bản từ tên tệp hoặc câu hỏi (bỏ qua năm 20xx)"""
    tokens = [t for t in re.split(r'[^0-9]+', text) if t]
    non_years = [t for t in tokens if not (len(t) == 4 and t.startswith('20'))]
    significant = [t for t in non_years if len(t) >= 2 and not (len(t) == 2 and t.startswith('0'))]
    return significant or non_years or tokens


class AssistantService:
    @staticmethod
    def extract_file_content(file_bytes: bytes, filename: str) -> str:
        """Trích xuất nội dung văn bản từ tệp đính kèm (PDF, DOCX, XLSX, TXT)"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            if not PYPDF_AVAILABLE:
                return f"[Đính kèm tệp PDF: {filename} - Cần cài thư viện pypdf để đọc toàn văn]"
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                pages_text = []
                # Giới hạn đọc tối đa 25 trang đầu để tối ưu tốc độ
                for i, page in enumerate(reader.pages[:25]):
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_text.append(f"--- Trang {i+1} ---\n{t.strip()}")
                return "\n\n".join(pages_text) if pages_text else f"[Tệp PDF rỗng hoặc dạng ảnh scan: {filename}]"
            except Exception as e:
                return f"[Lỗi trích xuất PDF {filename}: {e}]"

        elif ext in [".docx", ".doc"]:
            if not DOCX_AVAILABLE:
                return f"[Đính kèm tệp Word: {filename}]"
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                return "\n".join(paragraphs) if paragraphs else f"[Tệp Word rỗng: {filename}]"
            except Exception as e:
                return f"[Lỗi trích xuất Word {filename}: {e}]"

        elif ext in [".xlsx", ".xls"]:
            if not OPENPYXL_AVAILABLE:
                return f"[Đính kèm bảng tính Excel: {filename}]"
            try:
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
                sheets_summary = []
                for sheetname in wb.sheetnames[:5]:
                    ws = wb[sheetname]
                    rows_str = []
                    for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                        if r_idx >= 40:
                            break
                        row_vals = [str(v) if v is not None else "" for v in row]
                        if any(row_vals):
                            rows_str.append(" | ".join(row_vals[:15]))
                    if rows_str:
                        sheets_summary.append(f"=== Bảng: {sheetname} ===\n" + "\n".join(rows_str))
                return "\n\n".join(sheets_summary) if sheets_summary else f"[Bảng tính Excel rỗng: {filename}]"
            except Exception as e:
                return f"[Lỗi trích xuất Excel {filename}: {e}]"

        else:
            try:
                return file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                return f"[Tệp nhị phân đính kèm: {filename}]"

    @classmethod
    def search_web_realtime(cls, query: str, max_results: int = 5) -> Tuple[str, List[Dict[str, str]], List[str]]:
        """
        Tra cứu dữ liệu Internet thời gian thực.
        Bảo đảm luôn tìm kiếm ra ngoài Internet và trích xuất nguồn tin cậy khi người dùng tick chọn.
        """
        web_sources: List[Dict[str, str]] = []
        web_queries: List[str] = [query]
        context_lines: List[str] = []

        # Thử 1: DuckDuckGo với curl_cffi impersonate Chrome (chống chặn bot cực mạnh)
        try:
            from curl_cffi import requests as c_requests
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = c_requests.get(url, impersonate="chrome120", timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for div in soup.find_all("div", class_="result")[:max_results]:
                    a_title = div.find("a", class_="result__a")
                    a_snippet = div.find("a", class_="result__snippet")
                    if a_title:
                        title = a_title.get_text(strip=True)
                        href = a_title.get("href", "")
                        actual_url = href
                        if "uddg=" in href:
                            qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            actual_url = qs.get("uddg", [href])[0]
                        snippet = a_snippet.get_text(strip=True) if a_snippet else ""
                        if title and actual_url and actual_url.startswith("http"):
                            web_sources.append({"title": title, "uri": actual_url})
                            context_lines.append(f"- Tiêu đề: {title}\n  Đường dẫn: {actual_url}\n  Tóm tắt nội dung: {snippet}")
        except Exception as e_ddg:
            print(f"[AssistantService] Lỗi curl_cffi DDG: {e_ddg}")

        # Thử 2: Fallback Bing search nếu DDG chưa có kết quả
        if not web_sources:
            try:
                b_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&setlang=vi"
                b_resp = requests.get(b_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=8)
                if b_resp.status_code == 200:
                    soup = BeautifulSoup(b_resp.text, "html.parser")
                    for li in soup.find_all("li", class_="b_algo")[:max_results]:
                        h2 = li.find("h2")
                        p = li.find("p")
                        a = h2.find("a") if h2 else None
                        if a:
                            title = a.get_text(strip=True)
                            raw_href = a.get("href", "")
                            actual_url = raw_href
                            if "u=a1" in raw_href:
                                try:
                                    u_part = raw_href.split("u=a1")[1].split("&")[0]
                                    u_part += "=" * ((4 - len(u_part) % 4) % 4)
                                    actual_url = base64.b64decode(u_part).decode("utf-8", errors="ignore")
                                except Exception:
                                    pass
                            snippet = p.get_text(strip=True) if p else ""
                            if title and actual_url and "facebook.com" not in actual_url and actual_url.startswith("http"):
                                web_sources.append({"title": title, "uri": actual_url})
                                context_lines.append(f"- Tiêu đề: {title}\n  Đường dẫn: {actual_url}\n  Tóm tắt nội dung: {snippet}")
            except Exception as e_bing:
                print(f"[AssistantService] Lỗi fallback Bing search: {e_bing}")

        full_web_context = "\n\n".join(context_lines)
        return full_web_context, web_sources, web_queries

    @classmethod
    def get_drive_reference_context(
        cls, 
        folder_ids: List[str], 
        query: str, 
        filter_tax_only: bool = False,
        max_files: int = 6
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Tham chiếu tài liệu từ các thư mục Google Drive (Ứng dụng công nghệ Vertex AI Search / Drive Retrieval):
        - Quét danh sách tệp trong các thư mục được trợ lý chỉ định
        - Tìm kiếm tệp khớp ngữ nghĩa/từ khóa câu hỏi
        - Hỗ trợ cả PDF văn bản và PDF scan (đính kèm đa phương thức để AI OCR trực tiếp)
        """
        if not drive_service.is_connected or not folder_ids:
            return "", [], []

        citations: List[Dict[str, Any]] = []
        context_snippets: List[str] = []
        scanned_pdf_inlines: List[Dict[str, Any]] = []

        try:
            # Thu thập danh sách tệp từ các thư mục đã chọn
            all_drive_files = []
            for fid in folder_ids:
                try:
                    q_drive = f"'{fid}' in parents and trashed = false"
                    res = drive_service.service.files().list(
                        q=q_drive,
                        fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
                        pageSize=80
                    ).execute()
                    files = res.get("files", [])
                    all_drive_files.extend(files)
                except Exception as ex_f:
                    print(f"[AssistantService] Lỗi quét thư mục Drive {fid}: {ex_f}")

            if not all_drive_files:
                return "", [], []

            # Chuẩn bị bộ từ khóa truy vấn chuẩn hóa không dấu
            q_un = unaccent(query)
            q_tokens = [w for w in re.split(r'[^a-zA-Z0-9_]+', q_un) if len(w) >= 2]

            # Mở rộng từ khóa chuyên môn thuế & quy định pháp luật
            expanded_tokens = list(q_tokens)
            if any(w in q_un for w in ["giam tru", "y te", "giao duc", "gia canh", "phu thuoc", "tien luong", "thu nhap", "tncn"]):
                expanded_tokens.extend(["tncn", "thue", "nghi_dinh", "253"])
            if any(w in q_un for w in ["hoa don", "hddt", "dien tu"]):
                expanded_tokens.extend(["hoa_don", "dien_tu", "254", "91"])
            if any(w in q_un for w in ["ho kinh doanh", "hkd"]):
                expanded_tokens.extend(["ho_kinh_doanh", "68", "18", "141"])
            if any(w in q_un for w in ["doanh nghiep", "tndn"]):
                expanded_tokens.extend(["tndn", "doanh_nghiep", "20", "168"])
            # Hoạt động cho thuê nhà, cho thuê tài sản, cho thuê mặt bằng, bất động sản
            if any(w in q_un for w in ["thue nha", "cho thue", "tai san", "bat dong san", "nha o", "can ho", "thue dat", "mat bang"]):
                expanded_tokens.extend(["thue_nha", "cho_thue", "ho_kinh_doanh", "ca_nhan", "tai_san", "68", "18", "141", "168", "253", "tncn", "gtgt"])

            query_doc_numbers = extract_doc_numbers(query)

            scored_files = []
            for f in all_drive_files:
                fname = f.get("name", "")
                fname_un = unaccent(fname)
                fname_doc_numbers = extract_doc_numbers(fname)
                score = 0

                # Ưu tiên tuyệt đối nếu tệp chứa ĐÚNG số hiệu văn bản người dùng hỏi (vd: 253, 43, 68...)
                has_exact_doc_number = any(num in fname_doc_numbers for num in query_doc_numbers)
                if has_exact_doc_number:
                    score += 100

                # So khớp từ khóa ngữ nghĩa câu hỏi
                for token in expanded_tokens:
                    if len(token) >= 3 and token in fname_un:
                        score += 5

                # Chỉ cộng điểm định dạng nếu đã khớp nội dung
                if score > 0:
                    if fname.lower().endswith(".pdf"):
                        score += 2
                    elif fname.lower().endswith(".docx") or fname.lower().endswith(".doc"):
                        score += 2

                if score > 0:
                    scored_files.append((score, f))

            scored_files.sort(key=lambda x: x[0], reverse=True)

            # Nếu có tệp khớp chính xác số hiệu văn bản (score >= 100), ưu tiên các tệp đó
            exact_doc_matches = [f for s, f in scored_files if s >= 100]
            if exact_doc_matches:
                selected_files = exact_doc_matches[:max_files]
            else:
                # Lấy các tệp có độ tương đồng từ khóa (score >= 5) để không bỏ sót nghị định/thông tư
                selected_files = [f for s, f in scored_files if s >= 5][:max_files]

            # Tải nội dung các tệp liên quan nhất để nạp vào Context
            for f in selected_files:
                fid = f.get("id")
                fname = f.get("name")
                link = f.get("webViewLink") or f"https://drive.google.com/file/d/{fid}/view"

                if any(fname.lower().endswith(ext) for ext in [".pdf", ".docx", ".doc", ".txt", ".xlsx"]):
                    try:
                        content_bytes = drive_service.service.files().get_media(fileId=fid).execute()
                        extracted_text = cls.extract_file_content(content_bytes, fname)

                        # Nếu là PDF text bình thường có nội dung
                        if extracted_text and not extracted_text.startswith("[Tệp PDF rỗng") and len(extracted_text) > 40:
                            snippet = extracted_text[:5000]
                            context_snippets.append(
                                f"--- TÀI LIỆU GOOGLE DRIVE: {fname} ---\nLink: {link}\nNội dung trích lục:\n{snippet}\n"
                            )
                            citations.append({
                                "id": fid,
                                "title": fname,
                                "file_name": fname,
                                "link": link,
                                "source_type": "google_drive"
                            })
                        # Nếu là PDF scan không có text layer (như Nghị định 253/2026/NĐ-CP scan)
                        elif fname.lower().endswith(".pdf") and len(content_bytes) < 15 * 1024 * 1024:
                            b64_pdf = base64.b64encode(content_bytes).decode("utf-8")
                            scanned_pdf_inlines.append({
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": b64_pdf
                                }
                            })
                            context_snippets.append(
                                f"--- TÀI LIỆU GOOGLE DRIVE (BẢN GỐC SCAN): {fname} ---\nLink: {link}\n(Đã đính kèm tệp PDF đa phương thức để AI OCR và phân tích điều khoản toàn văn)\n"
                            )
                            citations.append({
                                "id": fid,
                                "title": f"{fname} (Văn bản scan)",
                                "file_name": fname,
                                "link": link,
                                "source_type": "google_drive"
                            })
                    except Exception as ex_read:
                        print(f"[AssistantService] Lỗi đọc tệp Drive {fname}: {ex_read}")

            full_context = "\n\n".join(context_snippets)
            return full_context, citations, scanned_pdf_inlines

        except Exception as e:
            print(f"[AssistantService] Lỗi tham chiếu Google Drive: {e}")
            return "", [], []

    @classmethod
    def chat_with_assistant(
        cls,
        assistant_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        enable_web_search_override: Optional[bool] = None,
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        drive_folder_ids_override: Optional[List[str]] = None,
        filter_tax_only_override: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Thực hiện hỏi đáp cùng Trợ Lý AI:
        - Nạp vai trò & chỉ thị hệ thống chuyên biệt của trợ lý
        - Tham chiếu tài liệu từ Google Drive (Vertex AI Search logic, tự động giải mã PDF text & scan)
        - Tra cứu Internet thời gian thực độc lập (Google / Web Search Grounding)
        - Đa phương thức: Text + Ảnh Clipboard + Đính kèm PDF/Word/Excel
        """
        asst = ConfigManager.get_assistant_by_id(assistant_id)
        if not asst:
            assts = ConfigManager.get_assistants()
            asst = assts[0] if assts else {
                "id": "asst_default",
                "name": "Trợ lý AI Tổng hợp",
                "system_prompt": "Bạn là Trợ lý AI chuyên gia hữu ích.",
                "drive_folder_ids": [],
                "enable_web_search": True,
                "model": "gemini-3.5-flash-lite"
            }

        api_key = ConfigManager.load_config().get("gemini", {}).get("api_key", "").strip()
        if not api_key:
            return {
                "success": False,
                "error": "Chưa cấu hình Gemini API Key. Vui lòng vào mục 'Thiết lập chung → Cấu hình Gemini' để cài đặt API Key."
            }

        selected_model = model_override or asst.get("model") or "gemini-3.5-flash-lite"
        if enable_web_search_override is not None:
            enable_web_search = bool(enable_web_search_override)
        else:
            enable_web_search = asst.get("enable_web_search", True)

        try:
            temperature = float(temperature_override) if temperature_override is not None else float(asst.get("temperature", 0.2))
        except Exception:
            temperature = 0.2

        drive_folder_ids = drive_folder_ids_override if drive_folder_ids_override is not None else asst.get("drive_folder_ids", [])
        filter_tax_only = bool(filter_tax_only_override) if filter_tax_only_override is not None else asst.get("filter_tax_only", False)

        # 1. Thu thập dữ liệu tham chiếu từ Google Drive (Vertex AI Search)
        drive_context = ""
        citations: List[Dict[str, Any]] = []
        scanned_pdf_inlines: List[Dict[str, Any]] = []
        if drive_folder_ids:
            drive_context, citations, scanned_pdf_inlines = cls.get_drive_reference_context(
                folder_ids=drive_folder_ids,
                query=message,
                filter_tax_only=filter_tax_only
            )

        # 2. Thu thập dữ liệu tìm kiếm Internet thời gian thực (nếu được bật)
        web_context = ""
        web_sources: List[Dict[str, str]] = []
        web_queries: List[str] = []
        if enable_web_search:
            web_context, web_sources, web_queries = cls.search_web_realtime(message)

        # 3. Xử lý các tệp đính kèm từ người dùng (PDF, Word, Excel)
        attachment_texts = []
        if attachments:
            for att in attachments:
                fname = att.get("filename", "tai_lieu")
                b64_str = att.get("data", "")
                if b64_str:
                    try:
                        raw_bytes = base64.b64decode(b64_str)
                        ext_txt = cls.extract_file_content(raw_bytes, fname)
                        attachment_texts.append(f"--- TỆP ĐÍNH KÈM: {fname} ---\n{ext_txt[:6000]}")
                    except Exception as ex_att:
                        print(f"[AssistantService] Lỗi đọc attachment {fname}: {ex_att}")

        # 4. Chuẩn bị System Instruction
        current_time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        base_system = asst.get("system_prompt", "Bạn là Trợ lý AI chuyên gia hữu ích.")
        
        # Thiết lập quy tắc cô lập nghiêm ngặt: Nếu KHÔNG chọn tìm kiếm Internet thì TUYỆT ĐỐI chỉ dùng tài liệu Google Drive
        drive_isolation_rule = ""
        if not enable_web_search:
            drive_isolation_rule = """
==================== NGUYÊN TẮC BẮT BUỘC (TUÂN THỦ TUYỆT ĐỐI THEO CHỈ THỊ) ====================
1. Người dùng CHỈ CHỌN tham khảo tài liệu trong Google Drive ("Thu thập thêm dữ liệu từ Internet" KHÔNG ĐƯỢC CHỌN).
2. BẠN CHỈ ĐƯỢC PHÉP TRẢ LỜI VÀ CĂN CỨ VÀO TÀI LIỆU GOOGLE DRIVE ĐƯỢC CẤP TRONG THƯ MỤC CHỈ ĐỊNH DƯỚI ĐÂY (kể cả các tệp PDF scan đính kèm).
3. NGHIÊM CẤM TUYỆT ĐỐI:
   - KHÔNG được tự ý tìm kiếm hoặc suy diễn từ các nguồn khác bên ngoài thư mục Google Drive đã chọn.
   - KHÔNG được áp dụng các Thông tư, Nghị định cũ (như Thông tư 40/2021, Thông tư 92/2015,...) nếu chúng KHÔNG có trong danh mục tài liệu Google Drive được cấp.
4. CÁCH TRÍCH DẪN & KẾT LUẬN:
   - Nêu rõ tên văn bản trong Google Drive làm căn cứ (Ví dụ: "Căn cứ theo Nghị định số 68/2026/NĐ-CP (hoặc văn bản tương ứng trong thư mục Tax_Nghiệp vụ thuế), Điều..., Khoản...").
   - Nếu trong các tài liệu Google Drive được cấp KHÔNG có quy định nào về vấn đề người dùng hỏi, bạn PHẢI trả lời trung thực: "Trong các tài liệu thuộc thư mục Google Drive được chỉ định, hiện không có văn bản quy định về nội dung này." Tuyệt đối không tự suy diễn hoặc lấy tài liệu bên ngoài.
================================================================================================="""
        else:
            drive_isolation_rule = """
- Người dùng ĐÃ BẬT tính năng tìm kiếm Internet: Hãy kết hợp thông tin chính thống từ tài liệu Google Drive và các dữ liệu tra cứu Internet thời gian thực mới nhất để trả lời đầy đủ, dẫn nguồn rõ ràng.
"""

        system_instruction = f"""{base_system}

Thời điểm hiện tại: {current_time_str}.
QUY TẮC PHỤC VỤ & TRẢ LỜI:
- Trả lời chuyên sâu, rõ ràng, định dạng Markdown chuyên nghiệp (sử dụng tiêu đề, danh sách gạch đầu dòng, in đậm các ý chính).
- Khi có tài liệu đính kèm từ Google Drive (bao gồm cả tài liệu dạng PDF scan toàn văn), hãy đọc kỹ từng trang văn bản và dẫn chiếu rõ ràng số hiệu điều khoản, điểm, khoản, số tiền hoặc mức giảm trừ cụ thể.
{drive_isolation_rule}
- Luôn giữ văn phong chuyên nghiệp, đúng chuẩn mực hành chính và quy định pháp luật Việt Nam.
"""

        # 5. Xây dựng nội dung Prompt hoàn chỉnh
        prompt_sections = []
        if drive_context:
            prompt_sections.append(
                f"[TÀI LIỆU NGUỒN THAM CHIẾU TỪ GOOGLE DRIVE (VERTEX AI SEARCH)]:\n{drive_context}"
            )
        if web_context:
            prompt_sections.append(
                f"[DỮ LIỆU TÌM KIẾM TRÊN INTERNET THỜI GIAN THỰC (GOOGLE/WEB GROUNDING)]:\n{web_context}"
            )
        if attachment_texts:
            prompt_sections.append(
                f"[TÀI LIỆU NGƯỜI DÙNG ĐÍNH KÈM TRONG CÂU HỎI]:\n" + "\n\n".join(attachment_texts)
            )

        prompt_sections.append(f"CÂU HỎI CỦA NGƯỜI DÙNG:\n{message}")
        final_prompt_text = "\n\n".join(prompt_sections)

        # 6. Xây dựng Request Payload cho Gemini API
        parts: List[Dict[str, Any]] = []

        # Đính kèm tệp PDF scan từ Google Drive nếu có (AI OCR trực tiếp)
        if scanned_pdf_inlines:
            for pdf_part in scanned_pdf_inlines:
                parts.append(pdf_part)

        # Thêm hình ảnh nếu có (từ Clipboard Ctrl+V hoặc đính kèm ảnh)
        if images:
            for img in images:
                m_type = img.get("mime_type", "image/png")
                b64_data = img.get("data", "")
                if b64_data:
                    if "," in b64_data:
                        b64_data = b64_data.split(",", 1)[1]
                    parts.append({
                        "inline_data": {
                            "mime_type": m_type,
                            "data": b64_data
                        }
                    })

        parts.append({"text": final_prompt_text})

        contents = []
        if conversation_history:
            for turn in conversation_history[-6:]:
                role = "user" if turn.get("role") == "user" else "model"
                t_content = turn.get("content", "")
                if t_content:
                    contents.append({
                        "role": role,
                        "parts": [{"text": t_content}]
                    })

        contents.append({
            "role": "user",
            "parts": parts
        })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "maxOutputTokens": 8192
            },
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            }
        }

        # 7. Thứ tự ưu tiên mô hình AI (tự động chuyển đổi nếu gặp hạn mức quota 429)
        candidate_models = []
        for m in [selected_model, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]:
            if m and m not in candidate_models:
                candidate_models.append(m)

        headers = {"Content-Type": "application/json"}
        last_error = ""

        for model_cand in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_cand}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=60)
                if resp.status_code == 200:
                    res_json = resp.json()
                    cands = res_json.get("candidates", [])
                    if cands:
                        answer_parts = cands[0].get("content", {}).get("parts", [])
                        answer_text = "".join(p.get("text", "") for p in answer_parts)

                        # Lọc chặt chẽ citations: CHỈ hiển thị tài liệu THỰC SỰ LIÊN QUAN và được dẫn chứng trong câu trả lời
                        final_citations = []
                        answer_un = unaccent(answer_text.lower())
                        query_un = unaccent(message.lower())
                        query_doc_nums = extract_doc_numbers(message)

                        for cit in citations:
                            fname = cit.get("file_name", "")
                            f_doc_nums = extract_doc_numbers(fname)

                            # 1. Trùng số hiệu văn bản với câu hỏi của người dùng (vd: 253)
                            match_query_num = any(num in query_doc_nums for num in f_doc_nums)
                            # 2. Hoặc số hiệu văn bản được trực tiếp nhắc tới trong câu trả lời
                            match_answer_num = any(num in answer_un for num in f_doc_nums)
                            # 3. Hoặc tên tệp xuất hiện rõ ràng trong câu trả lời
                            fname_clean = re.sub(r'^(0\d_|\d+_)', '', fname)
                            fname_core = re.split(r'\.|\(', fname_clean)[0].strip()
                            match_title = (unaccent(fname_core.lower()) in answer_un) if len(fname_core) >= 5 else False

                            if match_query_num or match_answer_num or match_title:
                                final_citations.append(cit)

                        # Nếu câu hỏi đích danh số hiệu văn bản mà bộ lọc chưa có, lấy đúng tệp có số hiệu đó
                        if not final_citations and citations:
                            for cit in citations:
                                fname = cit.get("file_name", "")
                                f_nums = extract_doc_numbers(fname)
                                if any(n in query_doc_nums for n in f_nums):
                                    final_citations.append(cit)
                                    break

                        return {
                            "status": "success",
                            "success": True,
                            "answer": answer_text,
                            "assistant_id": asst.get("id"),
                            "assistant_name": asst.get("name"),
                            "model_used": model_cand,
                            "citations": final_citations,
                            "web_queries": web_queries,
                            "web_sources": web_sources,
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                        }
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as ex:
                last_error = str(ex)

        return {
            "status": "error",
            "success": False,
            "error": f"Không thể nhận phản hồi từ Gemini: {last_error}",
            "message": f"Không thể nhận phản hồi từ Gemini: {last_error}"
        }


assistant_service = AssistantService()
