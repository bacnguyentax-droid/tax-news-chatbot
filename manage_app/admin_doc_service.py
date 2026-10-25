# -*- coding: utf-8 -*-
"""
Dịch vụ Quản lý & Xử lý Văn bản Hành chính chuẩn Nghị định 30/2020/NĐ-CP
- Kiểm tra thể thức, căn lề, font chữ, chính tả, cấu trúc theo NĐ 30/2020/NĐ-CP
- Tự động sửa lỗi và chuẩn hóa văn bản bằng Gemini API
- Soạn thảo văn bản hành chính AI 3 bước chuẩn hanhchanh.ai.vn (hỗ trợ ảnh đính kèm)
- Tinh chỉnh văn bản hành chính theo yêu cầu AI
- Xuất tệp Word (.docx) và PDF chuẩn kích thước A4 và thể thức NĐ 30
- Lưu trực tiếp văn bản lên Google Drive
"""

import os
import io
import re
import sys
import json
import base64
import datetime
import traceback
from typing import Dict, Any, List, Optional, Tuple

import requests

try:
    import docx
    from docx.shared import Pt, Inches, Mm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ADMIN_DOC_CACHE_FILE = os.path.join(CURRENT_DIR, "admin_doc_reference_cache.json")


# Khởi tạo font tiếng Việt cho ReportLab nếu có
TIMES_FONT_PATH = "C:/Windows/Fonts/times.ttf"
TIMES_BOLD_FONT_PATH = "C:/Windows/Fonts/timesbd.ttf"
TIMES_ITALIC_FONT_PATH = "C:/Windows/Fonts/timesi.ttf"
TIMES_BI_FONT_PATH = "C:/Windows/Fonts/timesbi.ttf"

if REPORTLAB_AVAILABLE:
    try:
        if os.path.exists(TIMES_FONT_PATH):
            pdfmetrics.registerFont(TTFont('TimesNewRoman', TIMES_FONT_PATH))
            if os.path.exists(TIMES_BOLD_FONT_PATH):
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', TIMES_BOLD_FONT_PATH))
            if os.path.exists(TIMES_ITALIC_FONT_PATH):
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', TIMES_ITALIC_FONT_PATH))
            if os.path.exists(TIMES_BI_FONT_PATH):
                pdfmetrics.registerFont(TTFont('TimesNewRoman-BoldItalic', TIMES_BI_FONT_PATH))
    except Exception as e:
        print(f"[AdminDocService] Lỗi nạp font Times: {e}")


class AdminDocService:
    """Xử lý nghiệp vụ Văn bản hành chính theo Nghị định 30/2020/NĐ-CP và Gemini API"""

    @classmethod
    def get_api_key(cls) -> str:
        """Lấy Gemini API Key từ cấu hình, file .env.local hoặc biến môi trường"""
        from config_manager import ConfigManager
        cfg = ConfigManager.load_config()
        key = cfg.get("gemini", {}).get("api_key", "").strip()
        if key:
            return key

        # Tìm trong .env.local
        env_path = os.path.join(PROJECT_ROOT, ".env.local")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            k = line.split("=", 1)[1].strip()
                            if k:
                                return k
            except Exception:
                pass

        return os.environ.get("GEMINI_API_KEY", "")

    @classmethod
    def get_model(cls) -> str:
        """Lấy model Gemini đang được cấu hình"""
        from config_manager import ConfigManager
        cfg = ConfigManager.load_config()
        return cfg.get("gemini", {}).get("model", "gemini-2.5-flash")

    @classmethod
    def call_gemini(
        cls, 
        prompt: str, 
        system_instruction: Optional[str] = None, 
        images: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Gọi Gemini API qua REST endpoint chính thức của Google"""
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError("Chưa cấu hình Gemini API Key. Vui lòng vào mục 'Thiết lập cấu hình' để nhập API Key.")

        selected_model = model or cls.get_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"

        parts = []
        if images:
            for img in images:
                mime_type = img.get("mime_type", "image/jpeg")
                b64_data = img.get("data", "")
                if b64_data:
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    })

        parts.append({"text": prompt})

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    parts_out = cands[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts_out)
                return ""
            
            # Nếu model gặp lỗi quota (429) / tải cao (503) / 404, thử fallback sang các model ổn định
            fallback_models = ["gemini-2.5-flash", "gemini-3.5-flash-lite"]
            for fb_m in fallback_models:
                if fb_m != selected_model:
                    try:
                        fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/{fb_m}:generateContent?key={api_key}"
                        resp2 = requests.post(fallback_url, json=payload, headers=headers, timeout=60)
                        if resp2.status_code == 200:
                            data2 = resp2.json()
                            cands2 = data2.get("candidates", [])
                            if cands2:
                                return "".join(p.get("text", "") for p in cands2[0].get("content", {}).get("parts", []))
                    except Exception:
                        pass

            err_msg = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Gemini API lỗi ({resp.status_code}): {err_msg}")
        except requests.RequestException as e:
            raise RuntimeError(f"Lỗi kết nối đến Gemini API: {str(e)}")

    @classmethod
    def test_connection(cls, api_key: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Kiểm tra tính hợp lệ của Gemini API Key và Mô hình AI"""
        key = api_key or cls.get_api_key()
        if not key:
            return {"success": False, "message": "API Key không được để trống."}
        
        target_model = model or cls.get_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": "Kiểm tra kết nối, trả lời 1 từ: OK"}]}]
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            if resp.status_code == 200:
                return {
                    "success": True, 
                    "message": f"Kết nối Gemini API thành công! Mô hình {target_model} hoạt động tốt.",
                    "model": target_model
                }
            
            # Fallback test 2.5-flash hoặc 3.5-flash-lite
            for fb in ["gemini-2.5-flash", "gemini-3.5-flash-lite"]:
                if fb != target_model:
                    fb_url = f"https://generativelanguage.googleapis.com/v1beta/models/{fb}:generateContent?key={key}"
                    resp2 = requests.post(fb_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
                    if resp2.status_code == 200:
                        return {
                            "success": True, 
                            "message": f"Kết nối Gemini API thành công với model dự phòng {fb} (Mô hình {target_model} đang bận hoặc quá hạn mức).",
                            "model": fb
                        }

            err_text = resp.text
            try:
                err_text = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            return {"success": False, "message": f"Kết nối thất bại ({resp.status_code}): {err_text}"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi gọi mạng: {str(e)}"}

    @classmethod
    def docx_to_authentic_html(cls, file_bytes: bytes) -> str:
        """
        Chuyển đổi tệp .docx thành mã HTML hiển thị trung thực theo đúng thể thức văn bản:
        - Giữ nguyên cấu trúc bảng 2 cột đầu trang (Cơ quan ban hành bên trái, Quốc hiệu - Tiêu ngữ bên phải)
        - Giữ nguyên cấu trúc bảng 2 cột cuối trang (Nơi nhận bên trái, Chức vụ và người ký bên phải)
        - Giữ nguyên định dạng in đậm, in nghiêng, căn giữa, căn đều 2 bên, thụt lề đầu dòng 1.27cm
        - Xóa bỏ hoàn toàn đường viền bảng để hiển thị chuẩn trang in công văn hành chính
        """
        if not DOCX_AVAILABLE:
            return ""
        try:
            if isinstance(file_bytes, str):
                with open(file_bytes, 'rb') as f:
                    file_bytes = f.read()
            doc = docx.Document(io.BytesIO(file_bytes))
            html_parts = []
            
            for child in doc.element.body:
                if child.tag.endswith('tbl'):
                    t = docx.table.Table(child, doc)
                    rows_html = []
                    cols_count = len(t.columns) if t.rows else 0
                    for row in t.rows:
                        cells_html = []
                        for c_idx, cell in enumerate(row.cells):
                            cell_ps = []
                            for p in cell.paragraphs:
                                align = 'center' if p.alignment == WD_ALIGN_PARAGRAPH.CENTER else ('right' if p.alignment == WD_ALIGN_PARAGRAPH.RIGHT else 'left')
                                runs_html = []
                                for r in p.runs:
                                    txt = r.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                                    if r.bold:
                                        txt = f"<b>{txt}</b>"
                                    if r.italic:
                                        txt = f"<i>{txt}</i>"
                                    runs_html.append(txt)
                                p_content = "".join(runs_html) or p.text.replace("\n", "<br/>")
                                if not p_content.strip():
                                    continue
                                
                                # Xử lý đường kẻ phân cách nét liền chuẩn Nghị định 30
                                if re.match(r'^[─\-_=—–\.\s]{3,}$', p.text.strip()):
                                    cell_ps.append("<div style='height: 1.2px; background-color: #000; width: 35%; max-width: 140px; margin: 3px auto 5px auto;'></div>")
                                else:
                                    cell_ps.append(f"<div style='text-align: {align}; line-height: 1.35; margin-bottom: 2px;'>{p_content}</div>")
                            
                            w = "45%" if cols_count == 2 and c_idx == 0 else ("55%" if cols_count == 2 and c_idx == 1 else "auto")
                            cells_html.append(f"<td style='width: {w}; vertical-align: top; padding: 2px 8px; border: none;'>{''.join(cell_ps)}</td>")
                        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")
                    html_parts.append(f"<table style='width: 100%; border-collapse: collapse; border: none; margin-bottom: 14px;'>{''.join(rows_html)}</table>")
                
                elif child.tag.endswith('p'):
                    p = docx.text.paragraph.Paragraph(child, doc)
                    txt_raw = p.text.strip()
                    if not txt_raw:
                        html_parts.append("<div style='height: 6px;'></div>")
                        continue
                    
                    # Chuyển đổi dòng gạch nét đứt thành đường nét liền chuẩn Nghị định 30
                    if re.match(r'^[─\-_=—–\.\s]{3,}$', txt_raw):
                        html_parts.append("<div style='height: 1.2px; background-color: #000; width: 35%; max-width: 160px; margin: 4px auto 8px auto;'></div>")
                        continue
                    
                    # Xác định định dạng đoạn văn theo chuẩn văn bản hành chính Việt Nam
                    if txt_raw.startswith("Kính gửi:") or txt_raw.startswith("Kính gửi :"):
                        align = "left"
                        indent = ""
                        margin = "margin-bottom: 10px; margin-top: 6px;"
                    elif re.match(r'^(?:[IVXLCDM]+\.)\s+', txt_raw):
                        align = "left"
                        indent = ""
                        margin = "margin-top: 14px; margin-bottom: 6px; font-weight: bold;"
                    elif re.match(r'^[-+–—•]\s+', txt_raw):
                        align = "justify; text-justify: inter-word"
                        indent = "text-indent: -0.6cm; padding-left: 0.6cm;"
                        margin = "margin-bottom: 5px;"
                    elif re.match(r'^\d+\.\s+', txt_raw):
                        align = "justify; text-justify: inter-word"
                        indent = "text-indent: 1.27cm;"
                        margin = "margin-top: 6px; margin-bottom: 5px;"
                    elif p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                        align = "center"
                        indent = ""
                        margin = "margin-bottom: 8px; margin-top: 6px;"
                    else:
                        align = "justify; text-justify: inter-word"
                        indent = "text-indent: 1.27cm;"
                        margin = "margin-bottom: 6px;"

                    runs_html = []
                    for r in p.runs:
                        txt = r.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                        if r.bold:
                            txt = f"<b>{txt}</b>"
                        if r.italic:
                            txt = f"<i>{txt}</i>"
                        runs_html.append(txt)
                    p_content = "".join(runs_html) or p.text.replace("\n", "<br/>")
                    
                    html_parts.append(f"<p style='text-align: {align}; {indent} {margin} line-height: 1.45; font-size: 13pt; color: #000;'>{p_content}</p>")
                    
            return "".join(html_parts)
        except Exception as e:
            print(f"[AdminDocService] Error docx_to_authentic_html: {repr(e)}")
            return ""

    @classmethod
    def extract_text_from_upload(cls, file_bytes: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Trích xuất nội dung văn bản và thông tin lề/font (nếu có) từ file upload"""
        ext = os.path.splitext(filename)[1].lower()
        extracted_text = ""
        meta = {
            "filename": filename,
            "ext": ext,
            "margins_mm": None,
            "fonts": [],
            "has_tables": False,
            "extracted_html": ""
        }

        if ext == ".docx" and DOCX_AVAILABLE:
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                
                # Kiểm tra lề
                if doc.sections:
                    sec = doc.sections[0]
                    meta["margins_mm"] = {
                        "top": round(sec.top_margin.mm, 1),
                        "bottom": round(sec.bottom_margin.mm, 1),
                        "left": round(sec.left_margin.mm, 1),
                        "right": round(sec.right_margin.mm, 1)
                    }
                # Kiểm tra font
                fonts_seen = set()
                for p in doc.paragraphs:
                    for r in p.runs:
                        if r.font.name:
                            fonts_seen.add(r.font.name)
                meta["fonts"] = list(fonts_seen)
                meta["has_tables"] = len(doc.tables) > 0

                # Trích xuất HTML trung thực bảo toàn định dạng Word
                meta["extracted_html"] = cls.docx_to_authentic_html(file_bytes)

                # Lấy text theo thứ tự tự nhiên của cấu trúc văn bản
                elements_text = []
                for child in doc.element.body:
                    if child.tag.endswith('tbl'):
                        t = docx.table.Table(child, doc)
                        for row in t.rows:
                            row_txt = "   ".join(c.text.strip() for c in row.cells if c.text.strip())
                            if row_txt:
                                elements_text.append(row_txt)
                    elif child.tag.endswith('p'):
                        p = docx.text.paragraph.Paragraph(child, doc)
                        if p.text.strip():
                            elements_text.append(p.text.strip())
                
                extracted_text = "\n\n".join(elements_text)
            except Exception as e:
                print(f"[AdminDocService] Lỗi đọc docx: {e}")

        elif ext == ".pdf" and PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages_text = []
                for i, page in enumerate(reader.pages):
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                extracted_text = "\n\n".join(pages_text)
            except Exception as e:
                print(f"[AdminDocService] Lỗi đọc pdf: {e}")

        elif ext in (".txt", ".md", ".html"):
            try:
                extracted_text = file_bytes.decode("utf-8", errors="replace")
            except Exception:
                extracted_text = file_bytes.decode("latin-1", errors="replace")

        return extracted_text.strip(), meta

    # =========================================================================
    # KHO LƯU TRỮ (CACHE) CÁC FILE QUY ĐỊNH TRONG GOOGLE DRIVE ĐÃ XỬ LÝ (TIẾT KIỆM TOKEN)
    # =========================================================================
    @classmethod
    def _load_ref_cache(cls) -> Dict[str, Any]:
        """Đọc bộ nhớ đệm (Cache) các tệp quy định đã được AI trích xuất/xử lý"""
        if not os.path.exists(ADMIN_DOC_CACHE_FILE):
            return {"files": {}}
        try:
            with open(ADMIN_DOC_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {"files": {}}
                if "files" not in data or not isinstance(data["files"], dict):
                    data["files"] = {}
                return data
        except Exception as e:
            print(f"[AdminDocService] Lỗi đọc cache quy định: {e}")
            return {"files": {}}

    @classmethod
    def _save_ref_cache(cls, cache_data: Dict[str, Any]) -> bool:
        """Ghi bộ nhớ đệm (Cache) các tệp quy định đã xử lý ra ổ cứng"""
        try:
            with open(ADMIN_DOC_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[AdminDocService] Lỗi lưu cache quy định: {e}")
            return False

    @classmethod
    def process_and_cache_file(
        cls,
        file_id: str,
        file_name: str,
        folder_id: str = "",
        modified_time: str = "",
        file_size: int = 0,
        web_view_link: str = "",
        file_bytes: Optional[bytes] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Xử lý trích xuất quy định từ tệp PDF/Word trong thư mục Google Drive và lưu vào bộ nhớ đệm (Cache).
        - Nếu tệp đã được xử lý trước đó (trùng file_id và modified_time) và không yêu cầu force:
          Trả về ngay dữ liệu đã lưu trong Cache -> KHÔNG tốn thêm bất kỳ Token nào.
        - Nếu tệp mới hoặc vừa cập nhật:
          Trích xuất nội dung + dùng Gemini tóm tắt cô đọng các quy định/căn cứ cốt lõi 1 lần duy nhất rồi lưu vào Cache.
        """
        cache_data = cls._load_ref_cache()
        files_map = cache_data.get("files", {})
        cache_key = str(file_id or f"{folder_id}::{file_name}")

        existing = files_map.get(cache_key)
        if (
            existing
            and not force
            and existing.get("condensed_rules")
            and (not modified_time or existing.get("modified_time") == modified_time)
        ):
            return {
                "success": True,
                "from_cache": True,
                "record": existing
            }

        # Nếu chưa có file_bytes, tải từ Google Drive hoặc đọc từ thư mục NotebookLM cục bộ
        if file_bytes is None:
            try:
                from drive_service import drive_service
                if drive_service.is_connected and file_id and not file_id.startswith("local_"):
                    file_bytes = drive_service.service.files().get_media(fileId=file_id).execute()
            except Exception as ex_dl:
                print(f"[AdminDocService] Không thể tải file từ Drive ({file_name}): {ex_dl}")

        if file_bytes is None:
            # Thử tìm trong thư mục NotebookLM cục bộ
            try:
                from config_manager import ConfigManager
                from notebooklm_service import NotebookLMService
                admin_cfg = ConfigManager.get_admin_doc_config()
                nb = ConfigManager.ensure_notebook_for_folder(admin_cfg.get("reference_folder_name", ""), folder_id)
                nb_folder = NotebookLMService.get_notebook_folder(nb)
                local_candidate = os.path.join(nb_folder, file_name)
                if os.path.exists(local_candidate):
                    with open(local_candidate, "rb") as lf:
                        file_bytes = lf.read()
            except Exception:
                pass

        if not file_bytes:
            return {
                "success": False,
                "from_cache": False,
                "message": f"Không thể đọc dữ liệu tệp '{file_name}'."
            }

        raw_text, _ = cls.extract_text_from_upload(file_bytes, file_name)
        condensed_rules = ""
        api_key = cls.get_api_key()

        if raw_text and len(raw_text.strip()) > 60:
            # Nếu văn bản dài > 1600 ký tự và có API Key, dùng Gemini cô đọng quy định 1 lần duy nhất để tiết kiệm token về sau
            if len(raw_text) > 1600 and api_key:
                try:
                    sys_inst = (
                        "Bạn là chuyên gia pháp chế và văn thư hành chính. Hãy trích xuất cô đọng (khoảng 350 - 600 từ) "
                        "toàn bộ các quy định cốt lõi, số hiệu văn bản, căn cứ pháp lý, thẩm quyền ký, thể thức trình bày, "
                        "thời hạn, định mức và các nguyên tắc bắt buộc có trong tài liệu dưới đây để làm bộ quy chiếu chuẩn cho các lần soạn thảo sau."
                    )
                    sum_prompt = f"TÊN TÀI LIỆU QUY ĐỊNH: {file_name}\n\nNỘI DUNG TRÍCH XUẤT:\n{raw_text[:18000]}"
                    ai_summary = cls.call_gemini(sum_prompt, system_instruction=sys_inst)
                    if ai_summary and ai_summary.strip():
                        condensed_rules = ai_summary.strip()
                except Exception as ex_sum:
                    print(f"[AdminDocService] Lỗi tóm tắt quy định {file_name}, dùng trích đoạn trực tiếp: {ex_sum}")

            if not condensed_rules:
                condensed_rules = raw_text[:2800].strip()

        elif file_name.lower().endswith(".pdf") and len(file_bytes) < 12 * 1024 * 1024 and api_key:
            # Trường hợp PDF scan (không có lớp text), gọi Gemini Multimodal OCR 1 lần duy nhất rồi lưu vào Cache
            try:
                b64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                sys_inst = (
                    "Tài liệu đính kèm là tệp PDF quy định/văn bản mẫu. Hãy đọc OCR và trích xuất cô đọng (khoảng 350 - 600 từ) "
                    "toàn bộ số hiệu, căn cứ pháp lý, quy định thể thức, thẩm quyền và các nội dung trọng tâm cần tuân thủ."
                )
                ai_ocr_summary = cls.call_gemini(
                    f"Hãy trích xuất các quy định cốt lõi từ tệp PDF: {file_name}",
                    system_instruction=sys_inst,
                    images=[{"mime_type": "application/pdf", "data": b64_pdf}]
                )
                if ai_ocr_summary and ai_ocr_summary.strip():
                    condensed_rules = ai_ocr_summary.strip()
                    raw_text = condensed_rules
            except Exception as ex_ocr:
                print(f"[AdminDocService] Lỗi OCR PDF scan {file_name}: {ex_ocr}")

        if not condensed_rules:
            condensed_rules = f"Tài liệu tham chiếu quy định: {file_name} (Thuộc thư mục quy định hành chính)."

        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        record = {
            "file_id": cache_key,
            "file_name": file_name,
            "folder_id": folder_id,
            "modified_time": modified_time or "",
            "size": file_size or len(file_bytes),
            "web_view_link": web_view_link or (f"https://drive.google.com/file/d/{file_id}/view" if file_id and not file_id.startswith("local_") else ""),
            "extracted_text": (raw_text or "")[:10000],
            "condensed_rules": condensed_rules,
            "processed_at": now_str,
            "char_count": len(raw_text or condensed_rules),
            "condensed_char_count": len(condensed_rules)
        }

        files_map[cache_key] = record
        # Đồng thời ánh xạ theo tên file để tra cứu nhanh
        files_map[f"name::{file_name.lower()}"] = record
        cache_data["files"] = files_map
        cls._save_ref_cache(cache_data)

        return {
            "success": True,
            "from_cache": False,
            "record": record
        }

    @classmethod
    def list_reference_folder_files(cls, folder_id: Optional[str] = None, folder_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Liệt kê toàn bộ các tệp nằm trong thư mục Google Drive được chọn trong Cấu hình Văn bản hành chính,
        kèm trạng thái đã lưu bộ nhớ đệm (Cache) để tiết kiệm Token.
        """
        from config_manager import ConfigManager
        from drive_service import drive_service
        from notebooklm_service import NotebookLMService

        admin_cfg = ConfigManager.get_admin_doc_config()
        target_fid = folder_id or admin_cfg.get("reference_folder_id") or ""
        target_fname = ConfigManager.clean_drive_folder_name(folder_name or admin_cfg.get("reference_folder_name") or "Tax_Nghiệp vụ thuế")
        matched_nb = ConfigManager.ensure_notebook_for_folder(target_fname, target_fid)

        cache_data = cls._load_ref_cache()
        files_map = cache_data.get("files", {})

        drive_files_list = []
        seen_names = set()

        if not drive_service.is_connected:
            drive_service.test_connection()

        if drive_service.is_connected and target_fid:
            try:
                q_str = f"'{target_fid}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
                res = drive_service.service.files().list(
                    q=q_str,
                    fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
                    orderBy="modifiedTime desc",
                    pageSize=100
                ).execute()
                for f in res.get("files", []):
                    fid = f.get("id", "")
                    fname = f.get("name", "")
                    mtime = f.get("modifiedTime", "")
                    fsize = int(f.get("size", 0) or 0)
                    wlink = f.get("webViewLink") or f"https://drive.google.com/file/d/{fid}/view"

                    cached_rec = files_map.get(fid) or files_map.get(f"name::{fname.lower()}")
                    is_cached = bool(cached_rec and cached_rec.get("condensed_rules") and (not mtime or not cached_rec.get("modified_time") or cached_rec.get("modified_time") == mtime))

                    size_str = f"{fsize / 1024:.1f} KB" if fsize < 1024 * 1024 else f"{fsize / (1024 * 1024):.2f} MB"
                    if fsize == 0:
                        size_str = "Google Docs/Drive"

                    drive_files_list.append({
                        "id": fid,
                        "name": fname,
                        "mimeType": f.get("mimeType", ""),
                        "size": fsize,
                        "size_str": size_str,
                        "modified_time": mtime[:10] if mtime else "",
                        "raw_modified_time": mtime,
                        "webViewLink": wlink,
                        "is_cached": is_cached,
                        "processed_at": cached_rec.get("processed_at", "") if is_cached else "",
                        "condensed_preview": (cached_rec.get("condensed_rules", "")[:220] + "...") if (is_cached and cached_rec.get("condensed_rules")) else "",
                        "source": "google_drive"
                    })
                    seen_names.add(fname.lower())
            except Exception as ex_list:
                print(f"[AdminDocService] Lỗi liệt kê file trong thư mục Drive {target_fid}: {ex_list}")

        # Bổ sung các file PDF/Word đã lưu trong thư mục NotebookLM cục bộ trùng tên (nếu chưa hiện trên Drive)
        try:
            nb_folder = NotebookLMService.get_notebook_folder(matched_nb)
            if os.path.exists(nb_folder):
                for fname in os.listdir(nb_folder):
                    if fname.startswith("_") or fname.lower() in seen_names:
                        continue
                    if any(fname.lower().endswith(ext) for ext in (".pdf", ".docx", ".doc", ".txt")):
                        fpath = os.path.join(nb_folder, fname)
                        fsize = os.path.getsize(fpath)
                        mtime_dt = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d")
                        local_id = f"local_{fname}"
                        cached_rec = files_map.get(local_id) or files_map.get(f"name::{fname.lower()}")
                        is_cached = bool(cached_rec and cached_rec.get("condensed_rules"))
                        size_str = f"{fsize / 1024:.1f} KB" if fsize < 1024 * 1024 else f"{fsize / (1024 * 1024):.2f} MB"
                        drive_files_list.append({
                            "id": local_id,
                            "name": fname,
                            "mimeType": "application/pdf" if fname.lower().endswith(".pdf") else "application/octet-stream",
                            "size": fsize,
                            "size_str": size_str,
                            "modified_time": mtime_dt,
                            "raw_modified_time": mtime_dt,
                            "webViewLink": "",
                            "is_cached": is_cached,
                            "processed_at": cached_rec.get("processed_at", "") if is_cached else "",
                            "condensed_preview": (cached_rec.get("condensed_rules", "")[:220] + "...") if (is_cached and cached_rec.get("condensed_rules")) else "",
                            "source": "notebooklm_local"
                        })
        except Exception as ex_local:
            print(f"[AdminDocService] Lỗi đọc thư mục NotebookLM cục bộ: {ex_local}")

        cached_count = sum(1 for item in drive_files_list if item.get("is_cached"))
        return {
            "success": True,
            "folder_id": target_fid,
            "folder_name": target_fname,
            "notebook_id": matched_nb.get("id", ""),
            "notebook_name": matched_nb.get("name", target_fname),
            "total_files": len(drive_files_list),
            "cached_files": cached_count,
            "files": drive_files_list
        }

    @classmethod
    def get_cached_folder_reference_context(cls, query_hint: str = "", auto_process_limit: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Lấy nội dung quy định tham chiếu từ thư mục Google Drive đã cấu hình để đưa vào Prompt khi AI sinh/tinh chỉnh văn bản.
        - Ưu tiên đọc từ bộ nhớ đệm (Cache) đối với các file AI đã xử lý -> KHÔNG tốn token đọc lại file.
        - Với các file chưa xử lý trong thư mục, tự động xử lý và lưu vào Cache cho các lần tiếp theo.
        """
        from config_manager import ConfigManager
        admin_cfg = ConfigManager.get_admin_doc_config()
        if not admin_cfg.get("enable_reference_on_generate", True):
            return "", []

        folder_id = admin_cfg.get("reference_folder_id", "")
        folder_name = admin_cfg.get("reference_folder_name", "")
        if not folder_id and not folder_name:
            return "", []

        listing = cls.list_reference_folder_files(folder_id=folder_id, folder_name=folder_name)
        files = listing.get("files", [])
        if not files:
            return "", []

        cache_data = cls._load_ref_cache()
        files_map = cache_data.get("files", {})

        # Sắp xếp ưu tiên file khớp từ khóa với yêu cầu soạn thảo (query_hint) hoặc file đã có trong Cache
        q_lower = (query_hint or "").lower()
        q_words = [w for w in re.split(r'\W+', q_lower) if len(w) >= 3]

        def _score_file(f_item: Dict[str, Any]) -> int:
            fname_l = f_item.get("name", "").lower()
            sc = 10 if f_item.get("is_cached") else 0
            for w in q_words:
                if w in fname_l:
                    sc += 15
            if fname_l.endswith(".pdf") or fname_l.endswith(".docx"):
                sc += 5
            return sc

        sorted_files = sorted(files, key=_score_file, reverse=True)
        selected_files = sorted_files[:6]

        snippets = []
        ref_docs_used = []
        newly_processed = 0

        for f_item in selected_files:
            fid = f_item.get("id", "")
            fname = f_item.get("name", "")
            mtime = f_item.get("raw_modified_time", "")
            cached_rec = files_map.get(fid) or files_map.get(f"name::{fname.lower()}")

            if cached_rec and cached_rec.get("condensed_rules") and (not mtime or not cached_rec.get("modified_time") or cached_rec.get("modified_time") == mtime):
                rules_text = cached_rec.get("condensed_rules", "")
                snippets.append(f"• [TÀI LIỆU QUY ĐỊNH (ĐÃ CACHE): {fname}]\n{rules_text}")
                ref_docs_used.append({"id": fid, "name": fname, "from_cache": True})
            elif newly_processed < auto_process_limit:
                proc_res = cls.process_and_cache_file(
                    file_id=fid,
                    file_name=fname,
                    folder_id=folder_id,
                    modified_time=mtime,
                    file_size=f_item.get("size", 0),
                    web_view_link=f_item.get("webViewLink", "")
                )
                newly_processed += 1
                if proc_res.get("success") and proc_res.get("record"):
                    rec = proc_res["record"]
                    rules_text = rec.get("condensed_rules", "")
                    snippets.append(f"• [TÀI LIỆU QUY ĐỊNH (MỚI LƯU CACHE): {fname}]\n{rules_text}")
                    ref_docs_used.append({"id": fid, "name": fname, "from_cache": proc_res.get("from_cache", False)})

        if not snippets:
            return "", []

        context_block = (
            f"\n\n=== CÁC QUY ĐỊNH & VĂN BẢN THAM CHIẾU TRONG THƯ MỤC GOOGLE DRIVE '{folder_name}' (BẮT BUỘC TUÂN THỦ) ===\n"
            + "\n\n".join(snippets)
            + "\n=== KẾT THÚC PHẦN QUY ĐỊNH THAM CHIẾU ===\n"
        )
        return context_block, ref_docs_used


    @classmethod
    def check_nd30_format(cls, text: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Kiểm tra toàn diện quy định thể thức văn bản hành chính theo Nghị định 30/2020/NĐ-CP:
        1. Căn lề khổ A4 (Trái: 30-35mm, Phải: 15-20mm, Trên: 20-25mm, Dưới: 20-25mm)
        2. Font chữ Times New Roman, Unicode TCVN 6909:2001
        3. Quốc hiệu ("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM") & Tiêu ngữ ("Độc lập - Tự do - Hạnh phúc")
        4. Tên cơ quan ban hành, Số ký hiệu
        5. Địa danh và ngày tháng năm
        6. Tên loại văn bản & trích yếu nội dung
        7. Căn cứ pháp lý
        8. Thể thức nơi nhận ("Nơi nhận:", "- Lưu: VT")
        9. Chức vụ & Họ tên người ký
        10. Chính tả tiếng Việt & quy tắc viết hoa
        """
        meta = meta or {}
        issues: List[Dict[str, Any]] = []
        rule_score = 100

        # 1. Kiểm tra Căn lề nếu có metadata từ DOCX
        margins = meta.get("margins_mm")
        if margins:
            left = margins.get("left", 0)
            right = margins.get("right", 0)
            top = margins.get("top", 0)
            bottom = margins.get("bottom", 0)

            if left < 30.0 or left > 35.0:
                issues.append({
                    "id": "margin_left",
                    "component": "Căn lề trang A4",
                    "severity": "error",
                    "title": f"Lề trái không đúng chuẩn ({left} mm)",
                    "original_text": f"Lề trái hiện tại: {left} mm",
                    "suggestion": "Đặt lề trái từ 30 mm đến 35 mm (chuẩn đóng gáy hồ sơ)",
                    "rule_ref": "Phụ lục I, Mục I, Điểm 3 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 10

            if right < 15.0 or right > 20.0:
                issues.append({
                    "id": "margin_right",
                    "component": "Căn lề trang A4",
                    "severity": "error",
                    "title": f"Lề phải không đúng chuẩn ({right} mm)",
                    "original_text": f"Lề phải hiện tại: {right} mm",
                    "suggestion": "Đặt lề phải từ 15 mm đến 20 mm",
                    "rule_ref": "Phụ lục I, Mục I, Điểm 3 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 8

            if top < 20.0 or top > 25.0:
                issues.append({
                    "id": "margin_top",
                    "component": "Căn lề trang A4",
                    "severity": "warning",
                    "title": f"Lề trên chưa tối ưu ({top} mm)",
                    "original_text": f"Lề trên hiện tại: {top} mm",
                    "suggestion": "Đặt lề trên từ 20 mm đến 25 mm",
                    "rule_ref": "Phụ lục I, Mục I, Điểm 3 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 5

            if bottom < 20.0 or bottom > 25.0:
                issues.append({
                    "id": "margin_bottom",
                    "component": "Căn lề trang A4",
                    "severity": "warning",
                    "title": f"Lề dưới chưa tối ưu ({bottom} mm)",
                    "original_text": f"Lề dưới hiện tại: {bottom} mm",
                    "suggestion": "Đặt lề dưới từ 20 mm đến 25 mm",
                    "rule_ref": "Phụ lục I, Mục I, Điểm 3 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 5

        # 2. Kiểm tra Font chữ
        fonts = meta.get("fonts", [])
        if fonts:
            non_times = [f for f in fonts if "times" not in f.lower()]
            if non_times:
                issues.append({
                    "id": "font_family",
                    "component": "Phông chữ",
                    "severity": "error",
                    "title": "Sử dụng phông chữ không đúng quy định",
                    "original_text": f"Phông phát hiện: {', '.join(non_times[:3])}",
                    "suggestion": "Nghị định 30 bắt buộc sử dụng phông chữ Times New Roman (bộ mã ký tự Unicode TCVN 6909:2001)",
                    "rule_ref": "Phụ lục I, Mục I, Điểm 1 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 10

        # 3. Phân tích văn bản bằng Quy tắc chuẩn (Rule-based Regex)
        text_upper = text.upper()

        # Kiểm tra Quốc hiệu
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" not in text_upper:
            issues.append({
                "id": "missing_quoc_hieu",
                "component": "Quốc hiệu và Tiêu ngữ",
                "severity": "error",
                "title": "Thiếu hoặc sai Quốc hiệu",
                "original_text": "Không tìm thấy Quốc hiệu chuẩn",
                "suggestion": "Phải có dòng: 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM' (chữ in hoa, cỡ chữ 12-13, đứng, đậm)",
                "rule_ref": "Phụ lục I, Mục II, Điểm 1 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 15

        # Kiểm tra Tiêu ngữ
        if "ĐỘC LẬP - TỰ DO - HẠNH PHÚC" not in text_upper and "ĐỘC LẬP-TỰ DO-HẠNH PHÚC" not in text_upper:
            issues.append({
                "id": "missing_tieu_ngu",
                "component": "Quốc hiệu và Tiêu ngữ",
                "severity": "error",
                "title": "Thiếu hoặc sai Tiêu ngữ",
                "original_text": "Không tìm thấy Tiêu ngữ chuẩn",
                "suggestion": "Phải có dòng: 'Độc lập - Tự do - Hạnh phúc' (chữ in thường, các chữ cái đầu viết hoa, nối với nhau bằng dấu gạch nối (-), có dấu cách, cỡ chữ 13-14, đứng, đậm)",
                "rule_ref": "Phụ lục I, Mục II, Điểm 1 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 15

        # Kiểm tra Số và Ký hiệu
        so_match = re.search(r'(Số\s*:\s*[0-9]+[a-zA-Z0-9\/\-_]*)', text, re.IGNORECASE)
        if not so_match:
            issues.append({
                "id": "missing_so_ky_hieu",
                "component": "Số và ký hiệu văn bản",
                "severity": "warning",
                "title": "Thiếu số và ký hiệu văn bản hành chính",
                "original_text": "Chưa có Số: .../...-...",
                "suggestion": "Định dạng số ký hiệu: 'Số: [Số thứ tự]/[Ký hiệu tên loại văn bản]-[Ký hiệu cơ quan]'",
                "rule_ref": "Phụ lục I, Mục II, Điểm 3 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 10

        # Kiểm tra Địa danh và Ngày tháng
        date_match = re.search(r'([A-Za-zÀ-ỹ\s]+,\s*ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})', text, re.IGNORECASE)
        if not date_match:
            issues.append({
                "id": "missing_date",
                "component": "Địa danh và thời gian",
                "severity": "warning",
                "title": "Thiếu địa danh hoặc thời gian ban hành văn bản",
                "original_text": "Không tìm thấy định dạng '..., ngày ... tháng ... năm ...'",
                "suggestion": "Trình bày chữ in thường, nghiêng, cỡ chữ 13-14. Ví dụ: 'Hà Nội, ngày 24 tháng 10 năm 2026' (ngày dưới 10 và tháng 1, 2 phải có số 0 phía trước)",
                "rule_ref": "Phụ lục I, Mục II, Điểm 4 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 10
        else:
            # Kiểm tra quy tắc số 0 trước ngày < 10 hoặc tháng 1, 2
            d_str = date_match.group(1)
            bad_date = re.search(r'ngày\s+([1-9])\s+tháng\s+([1-9]|1[0-2])\s+năm', d_str)
            if bad_date and int(bad_date.group(1)) < 10 and not d_str.lower().count(f"ngày 0{bad_date.group(1)}"):
                issues.append({
                    "id": "date_zero_rule",
                    "component": "Địa danh và thời gian",
                    "severity": "warning",
                    "title": "Quy tắc ghi số 0 trước ngày nhỏ hơn 10",
                    "original_text": d_str,
                    "suggestion": f"Theo NĐ 30, những ngày dưới 10 phải thêm số 0 phía trước (ví dụ: ngày 0{bad_date.group(1)} thay vì ngày {bad_date.group(1)})",
                    "rule_ref": "Phụ lục I, Mục II, Điểm 4 NĐ 30/2020/NĐ-CP"
                })
                rule_score -= 5

        # Kiểm tra Nơi nhận
        if "NƠI NHẬN:" not in text_upper and "NOI NHAN:" not in text_upper:
            issues.append({
                "id": "missing_noi_nhan",
                "component": "Nơi nhận",
                "severity": "error",
                "title": "Thiếu mục 'Nơi nhận:'",
                "original_text": "Chưa có phần Nơi nhận văn bản",
                "suggestion": "Trình bày: 'Nơi nhận:' (chữ in thường, nghiêng, đậm, cỡ chữ 12), các gạch đầu dòng nơi nhận cỡ chữ 11, dòng cuối: '- Lưu: VT, ...'",
                "rule_ref": "Phụ lục I, Mục II, Điểm 7 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 15
        elif "- LƯU: VT" not in text_upper and "- LƯU : VT" not in text_upper and "LƯU: VT" not in text_upper:
            issues.append({
                "id": "missing_luu_vt",
                "component": "Nơi nhận",
                "severity": "warning",
                "title": "Thiếu ký hiệu lưu văn thư '- Lưu: VT'",
                "original_text": "Nơi nhận chưa có dòng lưu văn thư",
                "suggestion": "Theo NĐ 30, dòng cuối cùng của nơi nhận phải có '- Lưu: VT, [Ký hiệu đơn vị soạn thảo]'",
                "rule_ref": "Phụ lục I, Mục II, Điểm 7 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 5

        # Kiểm tra Lỗi chính tả / khoảng trắng thông dụng
        spacing_errors = re.findall(r'(\s+[,.\;:\?!])', text)
        if spacing_errors:
            sample_err = spacing_errors[0]
            issues.append({
                "id": "punct_spacing",
                "component": "Kỹ thuật soạn thảo & Dấu câu",
                "severity": "warning",
                "title": "Lỗi khoảng trắng trước dấu câu",
                "original_text": f"Có khoảng trắng trước dấu câu (ví dụ '{sample_err}')",
                "suggestion": "Dấu chấm, phẩy, hai chấm, chấm phẩy phải viết liền ngay sau chữ, sau đó là một khoảng cách trắng",
                "rule_ref": "Phụ lục I, Mục I, Điểm 2 NĐ 30/2020/NĐ-CP"
            })
            rule_score -= 5

        # 4. Sử dụng Gemini AI để phân tích sâu nội dung văn bản nếu có API key
        ai_analysis = None
        api_key = cls.get_api_key()
        if api_key and len(text.strip()) > 30:
            try:
                system_instruction = (
                    "Bạn là chuyên gia thẩm định thể thức văn bản hành chính Việt Nam theo Nghị định số 30/2020/NĐ-CP ngày 05/3/2020 của Chính phủ. "
                    "Hãy kiểm tra nghiêm ngặt văn bản người dùng cung cấp và trả về DUY NHẤT một chuỗi JSON hợp lệ không có markdown bọc quanh."
                )
                prompt = f"""Phân tích văn bản hành chính sau đây theo Nghị định 30/2020/NĐ-CP:
---
{text[:4000]}
---

Yêu cầu trả về định dạng JSON thuần túy (không dùng ```json):
{{
    "overall_score": 75,
    "doc_type_detected": "THÔNG BÁO / CÔNG VĂN / QUYẾT ĐỊNH / TỜ TRÌNH...",
    "summary": "Tóm tắt đánh giá văn bản trong 1-2 câu ngắn gọn",
    "ai_issues": [
        {{
            "id": "issue_1",
            "component": "Tên thành phần (ví dụ: Cơ quan ban hành, Trích yếu, Căn cứ pháp lý, Thể thức chữ ký, Chính tả)",
            "severity": "error hoặc warning",
            "title": "Tiêu đề ngắn về lỗi",
            "original_text": "Đoạn văn bản bị lỗi hoặc thiếu",
            "suggestion": "Cách sửa chuẩn xác theo NĐ 30/2020/NĐ-CP",
            "rule_ref": "Điều khoản hoặc Phụ lục quy định cụ thể"
        }}
    ]
}}"""
                gemini_resp = cls.call_gemini(prompt, system_instruction=system_instruction)
                clean_json = gemini_resp.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
                    clean_json = re.sub(r'\s*```$', '', clean_json)
                ai_data = json.loads(clean_json)
                if isinstance(ai_data, dict):
                    ai_analysis = ai_data
                    ai_issues = ai_data.get("ai_issues", [])
                    # Gộp các lỗi AI phát hiện được
                    for idx, item in enumerate(ai_issues):
                        item["id"] = f"ai_issue_{idx+1}"
                        issues.append(item)
                    if "overall_score" in ai_data:
                        rule_score = min(rule_score, int(ai_data["overall_score"]))
            except Exception as e:
                print(f"[AdminDocService] Lỗi gọi Gemini AI audit: {e}")

        rule_score = max(10, min(100, rule_score))
        return {
            "success": True,
            "overall_score": rule_score,
            "issues_count": len(issues),
            "errors_count": sum(1 for i in issues if i.get("severity") == "error"),
            "warnings_count": sum(1 for i in issues if i.get("severity") == "warning"),
            "issues": issues,
            "metadata": meta,
            "ai_summary": ai_analysis.get("summary") if ai_analysis else "Đã hoàn thành kiểm tra quy tắc Nghị định 30/2020/NĐ-CP."
        }

    @classmethod
    def ai_fix_nd30(cls, original_text: str, issues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Tự động sửa toàn bộ lỗi và chuẩn hóa văn bản theo đúng chuẩn Nghị định 30/2020/NĐ-CP bằng Gemini API"""
        system_instruction = (
            "Bạn là trợ lý pháp lý cao cấp kiêm chuyên gia soạn thảo văn bản hành chính Việt Nam, am tường Nghị định 30/2020/NĐ-CP. "
            "Nhiệm vụ của bạn là nhận văn bản gốc của người dùng (kèm danh sách lỗi nếu có), tự động chỉnh sửa mọi lỗi thể thức, căn lề, "
            "viết hoa, chính tả, dấu câu, căn cứ pháp lý, nơi nhận, chữ ký để trở thành một văn bản hành chính chuẩn mực 100% theo Nghị định 30. "
            "Giữ nguyên tinh thần và dữ liệu cốt lõi, nâng cấp ngôn phong chuẩn văn bản quản lý nhà nước."
        )

        issues_str = ""
        if issues:
            issues_str = "Các lỗi phát hiện cần khắc phục:\n" + "\n".join(
                f"- {i.get('title')}: {i.get('suggestion')}" for i in issues[:10]
            )

        prompt = f"""Hãy hiệu chỉnh toàn diện văn bản sau đây thành văn bản hành chính chuẩn Nghị định 30/2020/NĐ-CP.

{issues_str}

VĂN BẢN GỐC:
---
{original_text}
---

Trả về DUY NHẤT một đối tượng JSON hợp lệ (không kèm bất kỳ chữ giải thích nào ngoài JSON, không bọc markdown ```json):
{{
    "agency_parent": "TÊN CƠ QUAN CHỦ QUẢN CẤP TRÊN (In hoa đứng, nếu có. VD: BỘ TÀI CHÍNH hoặc UBND TỈNH)",
    "agency_name": "TÊN CƠ QUAN BAN HÀNH (In hoa đứng đậm. VD: CỤC THUẾ THÀNH PHỐ HỒ CHÍ MINH)",
    "agency_code": "Mã định danh hoặc ký hiệu cơ quan (VD: CTHCM)",
    "doc_number": "Số hiệu văn bản chuẩn (VD: 125/TB-CTHCM hoặc 89/CV-CTHCM)",
    "republic_title": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "motto": "Độc lập - Tự do - Hạnh phúc",
    "location": "Địa danh (VD: Thành phố Hồ Chí Minh)",
    "date_formatted": "ngày ... tháng ... năm ... (chuẩn số 0 trước ngày <10 và tháng 1,2)",
    "doc_type": "TÊN LOẠI VĂN BẢN (In hoa đậm đứng, VD: THÔNG BÁO / QUYẾT ĐỊNH / CÔNG VĂN / TỜ TRÌNH / KẾ HOẠCH)",
    "subject": "Trích yếu nội dung văn bản (In thường đậm đứng, cô đọng súc tích)",
    "legal_bases": [
        "Căn cứ Luật Quản lý thuế ngày 13 tháng 6 năm 2019;",
        "Căn cứ Nghị định số 126/2020/NĐ-CP ngày 19 tháng 10 năm 2020 của Chính phủ quy định chi tiết một số điều của Luật Quản lý thuế;"
    ],
    "body_paragraphs": [
        "Đoạn 1 nội dung...",
        "Đoạn 2 nội dung..."
    ],
    "body_html": "<p>Nội dung trình bày hoàn chỉnh đã định dạng chuẩn, có thụt lề 1.27cm, căn đều 2 bên...</p>",
    "recipients": [
        "Như Điều 3 (để thực hiện);",
        "Ban Giám đốc (để báo cáo);",
        "- Lưu: VT, NV."
    ],
    "signer_role": "QUYỀN HẠN/CHỨC VỤ (In hoa đậm, VD: CỤC TRƯỞNG hoặc TM. ỦY BAN NHÂN DÂN / CHỦ TỊCH)",
    "signer_name": "Họ và tên người ký (In thường đậm đứng)",
    "applied_fixes": [
        "Đã chuẩn hóa Quốc hiệu và Tiêu ngữ đúng cỡ chữ và dấu nối",
        "Đã thêm số 0 trước ngày/tháng theo quy định NĐ 30",
        "Đã bổ sung căn cứ pháp lý và chuẩn hóa thể thức nơi nhận có '- Lưu: VT'"
    ]
}}"""

        raw_resp = cls.call_gemini(prompt, system_instruction=system_instruction)
        clean_json = raw_resp.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
            clean_json = re.sub(r'\s*```$', '', clean_json)

        try:
            fixed_data = json.loads(clean_json)
            return {
                "success": True,
                "data": fixed_data,
                "message": "Đã tự động chỉnh sửa và chuẩn hóa văn bản theo Nghị định 30/2020/NĐ-CP thành công."
            }
        except Exception as e:
            # Fallback nếu JSON bị lỗi nhẹ
            return {
                "success": False,
                "message": f"Lỗi phân tích dữ liệu AI: {str(e)}",
                "raw_output": raw_resp
            }

    @classmethod
    def ai_generate_admin_doc(cls, wizard_data: Dict[str, Any], images: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Soạn thảo văn bản hành chính bằng AI 3 bước chuẩn hanhchanh.ai.vn
        Hỗ trợ hình ảnh tài liệu tham khảo đính kèm (multimodal).
        """
        system_instruction = (
            "Bạn là trợ lý AI chuyên nghiệp về soạn thảo văn bản hành chính nhà nước Việt Nam chuẩn Nghị định 30/2020/NĐ-CP. "
            "Nhiệm vụ của bạn là nhận thông tin thiết lập từ người dùng và tài liệu/hình ảnh tham khảo đính kèm, sau đó sáng tạo một "
            "văn bản hành chính hoàn chỉnh, ngôn phong hành chính chuẩn xác, trang trọng, chặt chẽ, đầy đủ các thành phần bắt buộc. "
            "Bạn phải trả về DUY NHẤT một chuỗi JSON hợp lệ không có markdown codeblock bọc quanh."
        )

        doc_type = wizard_data.get("doc_type", "THÔNG BÁO").upper()
        agency_name = wizard_data.get("agency_name", "ỦY BAN NHÂN DÂN").strip()
        agency_parent = wizard_data.get("agency_parent", "").strip()
        agency_code = wizard_data.get("agency_code", "XXX").strip()
        doc_number = wizard_data.get("doc_number", f"01/{doc_type[:2]}-{agency_code}").strip()
        location = wizard_data.get("location", "TP. Hồ Chí Minh").strip()
        doc_date = wizard_data.get("doc_date", datetime.date.today().strftime("%Y-%m-%d"))
        
        # Chuyển ngày sang chuẩn tiếng Việt
        try:
            d_obj = datetime.datetime.strptime(doc_date, "%Y-%m-%d")
            date_formatted = f"ngày {d_obj.day:02d} tháng {d_obj.month:02d} năm {d_obj.year}"
        except Exception:
            date_formatted = f"ngày {datetime.date.today().day:02d} tháng {datetime.date.today().month:02d} năm {datetime.date.today().year}"

        purpose = wizard_data.get("purpose", "").strip()
        target_audience = wizard_data.get("target_audience", "").strip()
        legal_bases_input = wizard_data.get("legal_bases", "").strip()
        structure_req = wizard_data.get("structure_req", "").strip()
        recipients_input = wizard_data.get("recipients", [])
        if isinstance(recipients_input, str):
            recipients_list = [r.strip() for r in recipients_input.split("\n") if r.strip()]
        else:
            recipients_list = recipients_input or ["Như trên", "- Lưu: VT."]

        signer_role = wizard_data.get("signer_role", "GIÁM ĐỐC").strip()
        signer_name = wizard_data.get("signer_name", "").strip()

        # Tham chiếu các quy định từ thư mục Google Drive đã chọn trong Cấu hình (tự động đọc từ Cache để tiết kiệm Token)
        ref_context_str, ref_docs_used = "", []
        try:
            ref_context_str, ref_docs_used = cls.get_cached_folder_reference_context(
                query_hint=f"{doc_type} {purpose} {legal_bases_input}"
            )
        except Exception as ex_ref:
            print(f"[AdminDocService] Lỗi nạp quy định tham chiếu từ Cache: {ex_ref}")

        prompt = f"""Hãy soạn thảo một văn bản hành chính thể thức chuẩn Nghị định 30/2020/NĐ-CP dựa trên các thông tin sau:

1. HÌNH THỨC & THỂ THỨC:
- Loại văn bản: {doc_type}
- Cơ quan chủ quản: {agency_parent if agency_parent else '(Không có)'}
- Cơ quan ban hành: {agency_name}
- Số và ký hiệu: {doc_number}
- Địa danh & ngày tháng: {location}, {date_formatted}

2. MỤC ĐÍCH & YÊU CẦU NỘI DUNG:
- Mục đích và nội dung chính: {purpose}
- Đối tượng tiếp nhận / thi hành: {target_audience if target_audience else 'Các đơn vị trực thuộc và cá nhân liên quan'}
- Căn cứ pháp lý gợi ý: {legal_bases_input if legal_bases_input else 'Căn cứ các Luật, Nghị định hiện hành phù hợp'}
- Yêu cầu bố cục cụ thể: {structure_req if structure_req else 'Bố cục chặt chẽ theo chuẩn văn bản hành chính Việt Nam'}

3. NƠI NHẬN & NGƯỜI KÝ:
- Nơi nhận: {', '.join(recipients_list)}
- Chức vụ người ký: {signer_role}
- Họ tên người ký: {signer_name if signer_name else '[Họ và tên]'}
{ref_context_str}
Nếu có tài liệu quy định tham chiếu từ thư mục Google Drive ở trên hoặc hình ảnh đính kèm, hãy áp dụng chính xác các quy định, thể thức, số hiệu văn bản và căn cứ pháp lý liên quan vào văn bản được sinh ra.

Yêu cầu trả về DUY NHẤT một đối tượng JSON hợp lệ (không kèm chữ nào khác):
{{
    "agency_parent": "{agency_parent}",
    "agency_name": "{agency_name}",
    "doc_number": "{doc_number}",
    "republic_title": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "motto": "Độc lập - Tự do - Hạnh phúc",
    "location": "{location}",
    "date_formatted": "{date_formatted}",
    "doc_type": "{doc_type}",
    "subject": "Về việc ... (trích yếu súc tích, in thường, đậm đứng)",
    "legal_bases": [
        "Căn cứ Luật ...;",
        "Căn cứ Nghị định ...;"
    ],
    "body_paragraphs": [
        "Đoạn mở đầu hoặc Điều 1...",
        "Đoạn tiếp theo hoặc Điều 2...",
        "Đoạn kết luận hoặc Điều 3..."
    ],
    "body_html": "<p>Đoạn 1...</p><p>Đoạn 2...</p>",
    "recipients": [
        "Như trên;",
        "- Lưu: VT."
    ],
    "signer_role": "{signer_role}",
    "signer_name": "{signer_name if signer_name else '[Họ và tên]'}",
    "summary_notes": "Tóm tắt ngắn gọn các điểm chính của văn bản được tạo"
}}"""

        raw_resp = cls.call_gemini(prompt, system_instruction=system_instruction, images=images)
        clean_json = raw_resp.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
            clean_json = re.sub(r'\s*```$', '', clean_json)

        try:
            doc_data = json.loads(clean_json)
            return {
                "success": True,
                "data": doc_data,
                "referenced_files": ref_docs_used,
                "message": "Đã tạo nội dung văn bản hành chính AI thành công."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi phân tích JSON từ AI: {str(e)}",
                "raw_output": raw_resp
            }

    @classmethod
    def ai_refine_admin_doc(cls, current_doc: Dict[str, Any], refine_prompt: str) -> Dict[str, Any]:
        """Hiệu chỉnh, tinh chỉnh văn bản hành chính hiện tại theo yêu cầu người dùng bằng Gemini API"""
        system_instruction = (
            "Bạn là chuyên gia hiệu chỉnh văn bản hành chính Việt Nam chuẩn Nghị định 30/2020/NĐ-CP. "
            "Người dùng sẽ cung cấp bản nháp văn bản hiện tại và yêu cầu tinh chỉnh (thêm điều khoản, đổi giọng điệu, bổ sung căn cứ...). "
            "Hãy cập nhật văn bản theo đúng yêu cầu mà vẫn đảm bảo tuyệt đối thể thức NĐ 30/2020/NĐ-CP và các quy định tham chiếu. "
            "Trả về DUY NHẤT một chuỗi JSON hợp lệ không có markdown codeblock."
        )

        ref_context_str = ""
        try:
            ref_context_str, _ = cls.get_cached_folder_reference_context(query_hint=refine_prompt, auto_process_limit=1)
        except Exception:
            pass

        prompt = f"""VĂN BẢN HIỆN TẠI:
{json.dumps(current_doc, ensure_ascii=False, indent=2)}

YÊU CẦU TINH CHỈNH TỪ NGƯỜI DÙNG:
\"{refine_prompt}\"
{ref_context_str}
Hãy cập nhật lại toàn bộ văn bản và trả về JSON với cấu trúc giống hệt như trên:
{{
    "agency_parent": "...",
    "agency_name": "...",
    "doc_number": "...",
    "republic_title": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
    "motto": "Độc lập - Tự do - Hạnh phúc",
    "location": "...",
    "date_formatted": "...",
    "doc_type": "...",
    "subject": "...",
    "legal_bases": [...],
    "body_paragraphs": [...],
    "body_html": "...",
    "recipients": [...],
    "signer_role": "...",
    "signer_name": "...",
    "summary_notes": "Tóm tắt những điểm đã tinh chỉnh theo yêu cầu"
}}"""

        raw_resp = cls.call_gemini(prompt, system_instruction=system_instruction)
        clean_json = raw_resp.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
            clean_json = re.sub(r'\s*```$', '', clean_json)

        try:
            refined_data = json.loads(clean_json)
            return {
                "success": True,
                "data": refined_data,
                "message": "Đã tinh chỉnh văn bản theo yêu cầu AI thành công."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi phân tích JSON: {str(e)}",
                "raw_output": raw_resp
            }

    @classmethod
    def export_word(cls, doc_data: Dict[str, Any]) -> io.BytesIO:
        """Xuất file Word (.docx) chuẩn 100% kích thước, căn lề và định dạng theo Nghị định 30/2020/NĐ-CP"""
        if not DOCX_AVAILABLE:
            raise RuntimeError("Thư viện python-docx chưa được cài đặt trên hệ thống.")

        doc = docx.Document()
        
        # Thiết lập Khổ giấy A4 và Căn lề chuẩn NĐ 30:
        # Lề trên: 20mm, Lề dưới: 20mm, Lề trái: 30mm, Lề phải: 15mm
        section = doc.sections[0]
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        section.left_margin = Mm(30)
        section.right_margin = Mm(15)

        # Cấu hình Font mặc định Times New Roman
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(13)
        font.color.rgb = RGBColor(0, 0, 0)

        agency_parent = doc_data.get("agency_parent", "").strip()
        agency_name = doc_data.get("agency_name", "CƠ QUAN BAN HÀNH").strip().upper()
        doc_number = doc_data.get("doc_number", "Số: ...").strip()
        if not doc_number.lower().startswith("số"):
            doc_number = f"Số: {doc_number}"

        republic_title = doc_data.get("republic_title", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").strip().upper()
        motto = doc_data.get("motto", "Độc lập - Tự do - Hạnh phúc").strip()
        location = doc_data.get("location", "Địa danh").strip()
        date_formatted = doc_data.get("date_formatted", "").strip()
        location_date = f"{location}, {date_formatted}" if date_formatted else location

        # BẢNG HEADER: 1 dòng 2 cột (Cột 1: Cơ quan + Số hiệu | Cột 2: Quốc hiệu + Tiêu ngữ + Ngày tháng)
        table = doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Tỉ lệ 40% - 60% của chiều rộng trang (165mm khả dụng = 66mm và 99mm)
        col_widths = (Mm(70), Mm(95))
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width

        # Ô BÊN TRÁI: Cơ quan & Số hiệu
        cell_left = table.cell(0, 0)
        cell_left_p = cell_left.paragraphs[0]
        cell_left_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell_left_p.paragraph_format.line_spacing = 1.0
        cell_left_p.paragraph_format.space_after = Pt(2)

        if agency_parent:
            run_parent = cell_left_p.add_run(agency_parent.upper() + "\n")
            run_parent.font.name = 'Times New Roman'
            run_parent.font.size = Pt(12)
            run_parent.bold = False

        run_agency = cell_left_p.add_run(agency_name + "\n")
        run_agency.font.name = 'Times New Roman'
        run_agency.font.size = Pt(12)
        run_agency.bold = True

        # Đường kẻ nét liền dưới tên cơ quan ban hành (dài 1/3 - 1/2 tên cơ quan theo NĐ 30)
        run_divider = cell_left_p.add_run("────────" + "\n")
        run_divider.font.name = 'Arial'
        run_divider.font.size = Pt(8)
        run_divider.bold = True

        run_num = cell_left_p.add_run(doc_number)
        run_num.font.name = 'Times New Roman'
        run_num.font.size = Pt(12)
        run_num.bold = False

        # Ô BÊN PHẢI: Quốc hiệu, Tiêu ngữ, Địa danh & Ngày tháng
        cell_right = table.cell(0, 1)
        cell_right_p = cell_right.paragraphs[0]
        cell_right_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell_right_p.paragraph_format.line_spacing = 1.0
        cell_right_p.paragraph_format.space_after = Pt(2)

        run_qh = cell_right_p.add_run(republic_title + "\n")
        run_qh.font.name = 'Times New Roman'
        run_qh.font.size = Pt(12)
        run_qh.bold = True

        # Tiêu ngữ có đường gạch liền nét độ dài bằng độ dài dòng chữ theo NĐ 30
        run_tn = cell_right_p.add_run(motto + "\n")
        run_tn.font.name = 'Times New Roman'
        run_tn.font.size = Pt(13)
        run_tn.bold = True
        run_tn.underline = True

        run_date = cell_right_p.add_run(location_date)
        run_date.font.name = 'Times New Roman'
        run_date.font.size = Pt(13)
        run_date.italic = True

        # Khoảng cách sau Header
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(8)
        p_space.paragraph_format.space_after = Pt(4)

        # TÊN LOẠI VĂN BẢN (Cỡ 14, Đứng, Đậm, In hoa, Căn giữa)
        doc_type = doc_data.get("doc_type", "THÔNG BÁO").strip().upper()
        p_type = doc.add_paragraph()
        p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_type.paragraph_format.space_after = Pt(4)
        run_type = p_type.add_run(doc_type)
        run_type.font.name = 'Times New Roman'
        run_type.font.size = Pt(14)
        run_type.bold = True

        # TRÍCH YẾU NỘI DUNG (Cỡ 13-14, Đứng, Đậm, Căn giữa)
        subject = doc_data.get("subject", "").strip()
        if subject:
            p_sub = doc.add_paragraph()
            p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_sub.paragraph_format.space_after = Pt(6)
            run_sub = p_sub.add_run(subject)
            run_sub.font.name = 'Times New Roman'
            run_sub.font.size = Pt(13)
            run_sub.bold = True

            # Đường gạch ngang nét liền dưới trích yếu (dài 1/3 - 1/2 trích yếu theo NĐ 30)
            p_line = doc.add_paragraph()
            p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_line.paragraph_format.space_after = Pt(10)
            run_l = p_line.add_run("────────")
            run_l.font.name = 'Arial'
            run_l.font.size = Pt(8)

        # CĂN CỨ PHÁP LÝ (Cỡ 13, Nghiêng, Thụt lề 1.27cm, Kết thúc bằng dấu chấm phẩy ;)
        legal_bases = doc_data.get("legal_bases", [])
        if legal_bases:
            for base in legal_bases:
                b_text = str(base).strip()
                if not b_text:
                    continue
                p_base = doc.add_paragraph()
                p_base.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_base.paragraph_format.first_line_indent = Mm(12.7)
                p_base.paragraph_format.line_spacing = 1.15
                p_base.paragraph_format.space_after = Pt(3)
                r_base = p_base.add_run(b_text)
                r_base.font.name = 'Times New Roman'
                r_base.font.size = Pt(13)
                r_base.italic = True

        # NỘI DUNG CHÍNH (Cỡ 13-14, Thụt đầu dòng 1.27cm, Căn đều 2 bên, Giãn dòng 1.15)
        body_paragraphs = doc_data.get("body_paragraphs", [])
        if not body_paragraphs and "body_html" in doc_data:
            # Tách từ body_html
            raw_html = doc_data.get("body_html", "")
            paras = re.findall(r'<p[^>]*>(.*?)</p>', raw_html, re.DOTALL)
            body_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()]

        for p_text in body_paragraphs:
            p_clean = str(p_text).strip()
            if not p_clean:
                continue
            p_body = doc.add_paragraph()
            p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_body.paragraph_format.first_line_indent = Mm(12.7)
            p_body.paragraph_format.line_spacing = 1.15
            p_body.paragraph_format.space_after = Pt(6)
            
            # Kiểm tra xem có phải tiêu đề Điều/Mục hay không
            is_title = bool(re.match(r'^(Điều\s+\d+|Chương\s+[IVXLCDM]+|Mục\s+\d+)', p_clean, re.IGNORECASE))
            r_body = p_body.add_run(p_clean)
            r_body.font.name = 'Times New Roman'
            r_body.font.size = Pt(13)
            if is_title:
                r_body.bold = True

        # KHOẢNG CÁCH TRƯỚC PHẦN KÝ
        p_sign_space = doc.add_paragraph()
        p_sign_space.paragraph_format.space_before = Pt(12)

        # PHẦN CUỐI: BẢNG 1 DÒNG 2 CỘT (Cột 1: Nơi nhận | Cột 2: Quyền hạn, Chức vụ & Chữ ký)
        sign_table = doc.add_table(rows=1, cols=2)
        sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        sign_table.autofit = False

        for row in sign_table.rows:
            row.cells[0].width = Mm(70)
            row.cells[1].width = Mm(95)

        # CỘT TRÁI: NƠI NHẬN
        c_left = sign_table.cell(0, 0)
        p_nn_title = c_left.paragraphs[0]
        p_nn_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_nn_title.paragraph_format.space_after = Pt(2)
        r_nn_title = p_nn_title.add_run("Nơi nhận:\n")
        r_nn_title.font.name = 'Times New Roman'
        r_nn_title.font.size = Pt(12)
        r_nn_title.bold = True
        r_nn_title.italic = True

        recipients = doc_data.get("recipients", ["Như trên", "- Lưu: VT."])
        for r_item in recipients:
            r_clean = str(r_item).strip()
            if not r_clean:
                continue
            if not r_clean.startswith("-") and not r_clean.lower().startswith("như"):
                r_clean = f"- {r_clean}"
            p_rec = c_left.add_paragraph()
            p_rec.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_rec.paragraph_format.line_spacing = 1.0
            p_rec.paragraph_format.space_after = Pt(1)
            r_rec = p_rec.add_run(r_clean)
            r_rec.font.name = 'Times New Roman'
            r_rec.font.size = Pt(11)

        # CỘT PHẢI: CHỨC VỤ & CHỮ KÝ
        c_right = sign_table.cell(0, 1)
        p_sign = c_right.paragraphs[0]
        p_sign.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sign.paragraph_format.space_after = Pt(2)

        signer_role = doc_data.get("signer_role", "GIÁM ĐỐC").strip().upper()
        signer_name = doc_data.get("signer_name", "").strip()

        r_role = p_sign.add_run(signer_role + "\n\n\n\n")
        r_role.font.name = 'Times New Roman'
        r_role.font.size = Pt(13)
        r_role.bold = True

        if signer_name:
            r_name = p_sign.add_run(signer_name)
            r_name.font.name = 'Times New Roman'
            r_name.font.size = Pt(13)
            r_name.bold = True

        out_stream = io.BytesIO()
        doc.save(out_stream)
        out_stream.seek(0)
        return out_stream

    @classmethod
    def export_pdf(cls, doc_data: Dict[str, Any]) -> io.BytesIO:
        """Xuất file PDF chuẩn Nghị định 30/2020/NĐ-CP sử dụng ReportLab"""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("Thư viện reportlab chưa được cài đặt trên hệ thống.")

        out_stream = io.BytesIO()
        
        # Căn lề chuẩn A4: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm
        # 1 mm = 2.83465 pt
        left_margin_pt = 30 * 2.83465
        right_margin_pt = 15 * 2.83465
        top_margin_pt = 20 * 2.83465
        bottom_margin_pt = 20 * 2.83465

        doc = SimpleDocTemplate(
            out_stream,
            pagesize=A4,
            leftMargin=left_margin_pt,
            rightMargin=right_margin_pt,
            topMargin=top_margin_pt,
            bottomMargin=bottom_margin_pt
        )

        font_normal = 'TimesNewRoman' if 'TimesNewRoman' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        font_bold = 'TimesNewRoman-Bold' if 'TimesNewRoman-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        font_italic = 'TimesNewRoman-Italic' if 'TimesNewRoman-Italic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Oblique'

        styles = getSampleStyleSheet()

        style_agency = ParagraphStyle(
            'AgencyHeader',
            fontName=font_bold,
            fontSize=11,
            leading=14,
            alignment=1, # Center
            textColor=colors.black
        )

        style_qh = ParagraphStyle(
            'QuocHieuHeader',
            fontName=font_bold,
            fontSize=11,
            leading=14,
            alignment=1, # Center
            textColor=colors.black
        )

        style_tn = ParagraphStyle(
            'TieuNguHeader',
            fontName=font_bold,
            fontSize=12,
            leading=15,
            alignment=1, # Center
            textColor=colors.black
        )

        style_date = ParagraphStyle(
            'DateHeader',
            fontName=font_italic,
            fontSize=12,
            leading=15,
            alignment=1, # Center
            textColor=colors.black
        )

        style_type = ParagraphStyle(
            'DocType',
            fontName=font_bold,
            fontSize=14,
            leading=18,
            alignment=1, # Center
            spaceAfter=6,
            textColor=colors.black
        )

        style_subject = ParagraphStyle(
            'Subject',
            fontName=font_bold,
            fontSize=13,
            leading=16,
            alignment=1, # Center
            spaceAfter=10,
            textColor=colors.black
        )

        style_base = ParagraphStyle(
            'LegalBase',
            fontName=font_italic,
            fontSize=12,
            leading=16,
            alignment=4, # Justify
            firstLineIndent=36,
            spaceAfter=4,
            textColor=colors.black
        )

        style_body = ParagraphStyle(
            'DocBody',
            fontName=font_normal,
            fontSize=13,
            leading=17,
            alignment=4, # Justify
            firstLineIndent=36,
            spaceAfter=6,
            textColor=colors.black
        )

        story = []

        agency_parent = doc_data.get("agency_parent", "").strip()
        agency_name = doc_data.get("agency_name", "CƠ QUAN BAN HÀNH").strip().upper()
        doc_number = doc_data.get("doc_number", "Số: ...").strip()
        if not doc_number.lower().startswith("số"):
            doc_number = f"Số: {doc_number}"

        republic_title = doc_data.get("republic_title", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").strip().upper()
        motto = doc_data.get("motto", "Độc lập - Tự do - Hạnh phúc").strip()
        location = doc_data.get("location", "Địa danh").strip()
        date_formatted = doc_data.get("date_formatted", "").strip()
        location_date = f"{location}, {date_formatted}" if date_formatted else location

        # BẢNG HEADER (Chuẩn nét liền theo Nghị định 30/2020/NĐ-CP)
        from reportlab.platypus import HRFlowable
        p_agency_top = Paragraph(f"{agency_parent + '<br/>' if agency_parent else ''}<b>{agency_name}</b>", style_agency)
        hr_agency = HRFlowable(width="38%", thickness=1.2, color=colors.black, spaceBefore=2, spaceAfter=4, hAlign='CENTER')
        p_doc_num = Paragraph(doc_number, style_agency)
        cell_left_flowables = [p_agency_top, hr_agency, p_doc_num]

        p_qh = Paragraph(f"<b>{republic_title}</b>", style_qh)
        p_motto = Paragraph(f"<u><b>{motto}</b></u>", style_qh)
        p_date = Paragraph(f"<i>{location_date}</i>", style_qh)
        cell_right_flowables = [p_qh, p_motto, Spacer(1, 4), p_date]

        header_table = Table(
            [[cell_left_flowables, cell_right_flowables]],
            colWidths=[195, 275]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # TÊN LOẠI VĂN BẢN
        doc_type = doc_data.get("doc_type", "THÔNG BÁO").strip().upper()
        story.append(Paragraph(doc_type, style_type))

        # TRÍCH YẾU (Đường kẻ nét liền chuẩn NĐ 30)
        subject = doc_data.get("subject", "").strip()
        if subject:
            story.append(Paragraph(subject, style_subject))
            story.append(HRFlowable(width="35%", thickness=1.2, color=colors.black, spaceBefore=3, spaceAfter=8, hAlign='CENTER'))

        # CĂN CỨ PHÁP LÝ
        for base in doc_data.get("legal_bases", []):
            b_clean = str(base).strip()
            if b_clean:
                story.append(Paragraph(b_clean, style_base))

        story.append(Spacer(1, 6))

        # NỘI DUNG CHÍNH
        body_paragraphs = doc_data.get("body_paragraphs", [])
        if not body_paragraphs and "body_html" in doc_data:
            paras = re.findall(r'<p[^>]*>(.*?)</p>', doc_data.get("body_html", ""), re.DOTALL)
            body_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()]

        for p_text in body_paragraphs:
            p_clean = str(p_text).strip()
            if p_clean:
                story.append(Paragraph(p_clean, style_body))

        story.append(Spacer(1, 15))

        # NƠI NHẬN & CHỮ KÝ
        recipients = doc_data.get("recipients", ["Như trên", "- Lưu: VT."])
        nn_lines = ["<b><i>Nơi nhận:</i></b>"]
        for r_item in recipients:
            r_c = str(r_item).strip()
            if r_c:
                if not r_c.startswith("-") and not r_c.lower().startswith("như"):
                    r_c = f"- {r_c}"
                nn_lines.append(f"<font size='10'>{r_c}</font>")
        nn_text = "<br/>".join(nn_lines)

        signer_role = doc_data.get("signer_role", "GIÁM ĐỐC").strip().upper()
        signer_name = doc_data.get("signer_name", "").strip()
        sign_text = f"<b>{signer_role}</b><br/><br/><br/><br/><b>{signer_name}</b>"

        bottom_table = Table(
            [[Paragraph(nn_text, style_agency), Paragraph(sign_text, style_qh)]],
            colWidths=[200, 270]
        )
        bottom_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(bottom_table)

        doc.build(story)
        out_stream.seek(0)
        return out_stream


admin_doc_service = AdminDocService()
