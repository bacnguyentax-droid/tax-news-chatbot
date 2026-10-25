import urllib.request
import ssl
import re
import os
import io
import sys
import json
import base64
from typing import Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup

try:
    import docx
except ImportError:
    docx = None

try:
    import mammoth
except ImportError:
    mammoth = None

from pdf_generator import PDFGenerator

# SSL Context không kiểm tra chứng chỉ cho các trang chính phủ
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(CACHE_DIR, exist_ok=True)

CORRUPTED_TOKEN = "tm-8mq6BhNw0NbrKRhTDAaHMpvrqWaeHuYm7lW3HNfzTzww8Myg35dDL_fJB4izwTMOXudjJNi"

def safe_log(msg: str):
    """Ghi log an toàn tránh lỗi UnicodeEncodeError trên console Windows"""
    try:
        sys.stdout.write(f"{msg}\n")
        sys.stdout.flush()
    except Exception:
        try:
            sys.stdout.write(f"{msg.encode('ascii', errors='replace').decode('ascii')}\n")
            sys.stdout.flush()
        except Exception:
            pass

class AttachmentDownloader:
    @staticmethod
    def resolve_attachment_url(doc: Dict[str, Any], prefer_ext: str = "pdf") -> str:
        """
        Tìm kiếm đường link file đính kèm thực tế trên website cơ quan ban hành theo định dạng mong muốn.
        - prefer_ext='pdf': ưu tiên lấy file PDF để mở xem trực quan trong trình duyệt
        - prefer_ext='docx' hoặc 'doc': ưu tiên lấy file Word gốc để tải về chỉnh sửa
        """
        doc_num = (doc.get("doc_number") or "").strip()
        att_url = str(doc.get("attachment_url") or "")

        # Kiểm tra nếu attachment_url có sẵn và hợp lệ
        if att_url.startswith("http"):
            # Kiểm tra token bị gán nhầm
            is_corrupted = CORRUPTED_TOKEN in att_url and "115/2026/VBHN" not in doc_num
            if not is_corrupted:
                if prefer_ext == "pdf" and att_url.lower().endswith(".pdf"):
                    return att_url
                if prefer_ext in ["doc", "docx"] and any(att_url.lower().endswith(x) for x in [".doc", ".docx"]):
                    return att_url

        source_url = doc.get("source_url", "")
        if not source_url or not source_url.startswith("http"):
            # Nếu không có source_url mà có attachment_url (dù khác prefer_ext), dùng tạm attachment_url
            if att_url.startswith("http") and not (CORRUPTED_TOKEN in att_url and "115/2026/VBHN" not in doc_num):
                return att_url
            return ""

        clean_url = source_url.replace(" ", "%20")
        try:
            req = urllib.request.Request(clean_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=6) as res:
                html = res.read().decode('utf-8', errors='ignore')

            if "Request Rejected" in html or len(html) < 400:
                return att_url if att_url.startswith("http") else ""

            soup = BeautifulSoup(html, 'html.parser')

            # Thu thập tất cả ứng viên thẻ <a>
            candidates = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                h_low = href.lower()
                t_low = text.lower()

                is_cand = (
                    'cdnchinhphu.vn' in href or
                    '/wps/wcm/connect/' in href or
                    'download' in h_low or 'tải' in t_low or 'đính kèm' in t_low or
                    any(ext in h_low or ext in t_low for ext in ['.pdf', '.doc', '.docx'])
                )
                if is_cand:
                    full_href = href
                    if href.startswith('/'):
                        base = 'https://gdt.gov.vn' if 'gdt.gov.vn' in clean_url else ('https://congbao.chinhphu.vn' if 'congbao' in clean_url else 'https://vbpl.vn')
                        full_href = f"{base}{href}"
                    elif not href.startswith('http'):
                        base = 'https://congbao.chinhphu.vn' if 'congbao' in clean_url else 'https://gdt.gov.vn/wps/portal'
                        full_href = f"{base}/{href.lstrip('/')}"
                    candidates.append((full_href, text))

            # Lọc các ứng viên khớp với số hiệu văn bản (tránh nhầm văn bản khác)
            parts = [re.sub(r'[^a-zA-Z0-9]', '', p).lower() for p in doc_num.split('/') if len(re.sub(r'[^a-zA-Z0-9]', '', p)) >= 2]
            matched = []
            for href, text in candidates:
                combined = (href + ' ' + text).lower()
                if any(p in combined for p in parts):
                    matched.append((href, text))

            # CHỈ sử dụng ứng viên thực sự khớp với số hiệu văn bản (tuyệt đối không dùng candidates để tránh nhầm văn bản khác)
            if not matched:
                safe_log(f"[AttachmentDownloader] Khong tim thay link dinh kem khop so hieu {doc_num} tren {clean_url}")
                return ""

            pool = matched

            # 1. Nếu cần PDF: tìm link .pdf trước
            if prefer_ext == "pdf":
                for href, text in pool:
                    combined = (href + ' ' + text).lower()
                    if '.pdf' in combined:
                        return href

            # 2. Nếu cần Word: tìm link .docx / .doc
            if prefer_ext in ["doc", "docx"]:
                for href, text in pool:
                    combined = (href + ' ' + text).lower()
                    if any(ext in combined for ext in ['.docx', '.doc']):
                        return href

            # 3. Fallback: trả về ứng viên tốt nhất đầu tiên
            if pool:
                return pool[0][0]

        except Exception as e:
            safe_log(f"[AttachmentDownloader] Error resolving URL from {clean_url}: {e}")

        return att_url if att_url.startswith("http") else ""

    @staticmethod
    def download_vbpl_document(doc: Dict[str, Any], prefer_ext: str = "pdf") -> Optional[Tuple[bytes, str, str]]:
        """
        Tải file văn bản gốc trực tiếp từ CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn)
        sử dụng Next.js Server Action API của hệ thống vbpl mới.
        """
        vbpl_id = doc.get("vbpl_id")
        file_name = doc.get("vbpl_file_name")
        doc_num = (doc.get("doc_number") or "").strip()

        # Nếu chưa có vbpl_id, tra cứu nhanh qua Server Action tìm kiếm của vbpl.vn
        if not vbpl_id and doc_num:
            try:
                search_action = "c529d164f28418e5898a834422629e64c6816af1"
                payload = json.dumps([{"keyword": doc_num, "pageSize": 5}]).encode('utf-8')
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Next-Action': search_action,
                    'Content-Type': 'text/plain;charset=UTF-8',
                    'Accept': 'text/x-component'
                }
                req = urllib.request.Request("https://vbpl.vn", data=payload, headers=headers)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as res:
                    search_res = res.read().decode('utf-8', errors='ignore')
                m = re.search(r'\{"total":\d+,"pageNumber":\d+.*?"items":\[(.*?)\]\}', search_res)
                if m:
                    items = json.loads("[" + m.group(1) + "]")
                    if items:
                        item = items[0]
                        vbpl_id = item.get("id")
                        related_files = [f.get("fileName") for f in item.get("documentRelatedList", []) if f.get("fileName")]
                        if prefer_ext == "pdf":
                            pdf_files = [f for f in related_files if f.lower().endswith(".pdf")]
                            file_name = pdf_files[0] if pdf_files else (related_files[0] if related_files else None)
                        else:
                            word_files = [f for f in related_files if any(f.lower().endswith(x) for x in [".docx", ".doc"])]
                            file_name = word_files[0] if word_files else (related_files[0] if related_files else None)
            except Exception as e:
                safe_log(f"[AttachmentDownloader] Loi tra cuu VBPL API: {e}")

        if not vbpl_id or not file_name:
            return None

        # Tải file từ vbpl.vn Server Action
        try:
            dl_action = "bad13391811d5f14d7670e66189def56c08ceb1f"
            dl_payload = json.dumps([{
                "bucketName": "vbpl",
                "folderName": vbpl_id,
                "objectName": file_name,
                "preview": None
            }]).encode('utf-8')
            dl_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Next-Action': dl_action,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Accept': 'text/x-component'
            }
            req2 = urllib.request.Request("https://vbpl.vn", data=dl_payload, headers=dl_headers)
            with urllib.request.urlopen(req2, context=SSL_CTX, timeout=30) as res2:
                dl_res = res2.read().decode('utf-8', errors='ignore')

            # Trích xuất dữ liệu base64 theo chuẩn Next.js RSC
            m2 = re.search(r'([0-9a-fA-F]+):T([0-9a-fA-F]+),', dl_res)
            if m2:
                row_id = m2.group(1)
                hex_len = m2.group(2)
                byte_len = int(hex_len, 16)
                prefix = f"{row_id}:T{hex_len},"
                idx = dl_res.find(prefix) + len(prefix)
                b64_content = dl_res[idx : idx + byte_len]
                raw_bytes = base64.b64decode(b64_content)
                if raw_bytes and len(raw_bytes) > 1000:
                    field = doc.get("field", "Chung")
                    clean_num = re.sub(r'[/\\:*?"<>| ]', '_', doc_num)
                    clean_field = re.sub(r'[/\\:*?"<>| ]', '_', field)
                    ext = ".pdf" if file_name.lower().endswith(".pdf") else (".docx" if file_name.lower().endswith(".docx") else ".doc")
                    mimetype = "application/pdf" if ext == ".pdf" else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if ext == ".docx" else "application/msword")
                    filename = f"{clean_num}_{clean_field}{ext}"
                    cache_path = os.path.join(CACHE_DIR, filename)
                    try:
                        with open(cache_path, "wb") as f:
                            f.write(raw_bytes)
                    except Exception:
                        pass
                    safe_log(f"[AttachmentDownloader] VBPL Action downloaded: {filename} ({len(raw_bytes):,} bytes)")
                    return raw_bytes, filename, mimetype
        except Exception as e:
            safe_log(f"[AttachmentDownloader] Loi tai file tu VBPL Action: {e}")

        return None

    @staticmethod
    def get_document_payload(doc: Dict[str, Any], prefer_ext: str = "pdf") -> Tuple[bytes, str, str]:
        """
        Tải file văn bản thực tế từ link đính kèm trên website nguồn.
        - Nếu prefer_ext='pdf': Đảm bảo LUÔN trả về file PDF hợp lệ (mimetype='application/pdf').
          Nếu nguồn chỉ có file Word, tự động trích xuất nội dung và sinh bản PDF chuẩn hành chính
          để iframe trình duyệt có thể render mượt mà, không bao giờ bị hiện tượng khung xám hay ép tải về.
        - Nếu prefer_ext='docx' hoặc 'doc': Trả về file Word thực tế để tải về chỉnh sửa.
        """
        doc_num = (doc.get("doc_number") or "VanBan").strip()
        field = doc.get("field", "Chung")
        clean_num = re.sub(r'[/\\:*?"<>| ]', '_', doc_num)
        clean_field = re.sub(r'[/\\:*?"<>| ]', '_', field)

        # 0. Kiểm tra cache file đã tải trên đĩa cứng
        if prefer_ext == "pdf":
            cache_file = os.path.join(CACHE_DIR, f"{clean_num}_{clean_field}.pdf")
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 1000:
                try:
                    with open(cache_file, "rb") as f:
                        cached_bytes = f.read()
                    # Kiểm tra tính hợp lệ của PDF
                    if cached_bytes.startswith(b'%PDF'):
                        return cached_bytes, f"{clean_num}_{clean_field}.pdf", "application/pdf"
                    else:
                        os.remove(cache_file)
                except Exception:
                    pass
        elif prefer_ext in ["doc", "docx"]:
            for ext, mt in [
                (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                (".doc", "application/msword")
            ]:
                cache_file = os.path.join(CACHE_DIR, f"{clean_num}_{clean_field}{ext}")
                if os.path.exists(cache_file) and os.path.getsize(cache_file) > 1000:
                    try:
                        with open(cache_file, "rb") as f:
                            cached_bytes = f.read()
                        return cached_bytes, f"{clean_num}_{clean_field}{ext}", mt
                    except Exception:
                        pass

        # 0.5. Nếu là văn bản từ vbpl.vn, ưu tiên tải trực tiếp qua Server Action
        source = doc.get("source", "").lower()
        source_url = doc.get("source_url", "").lower()
        if "vbpl" in source or "vbpl" in source_url or doc.get("vbpl_id"):
            vbpl_res = AttachmentDownloader.download_vbpl_document(doc, prefer_ext=prefer_ext)
            if vbpl_res:
                content, fname, mt = vbpl_res
                # Nếu yêu cầu PDF nhưng tải về Word, chuyển đổi/sinh PDF
                if prefer_ext == "pdf" and not fname.lower().endswith(".pdf"):
                    pdf_bytes = PDFGenerator.generate_document_pdf(doc)
                    pdf_filename = f"{clean_num}_{clean_field}.pdf"
                    try:
                        with open(os.path.join(CACHE_DIR, pdf_filename), "wb") as f:
                            f.write(pdf_bytes)
                    except Exception:
                        pass
                    return pdf_bytes, pdf_filename, "application/pdf"
                return vbpl_res

        # 1. Thử lấy link tải file đính kèm thực tế từ web nguồn
        att_url = AttachmentDownloader.resolve_attachment_url(doc, prefer_ext=prefer_ext)
        if att_url:
            try:
                clean_att_url = att_url.replace(" ", "%20").replace("www.gdt.gov.vn", "gdt.gov.vn")
                dl_headers = dict(HEADERS)
                if 'gdt.gov.vn' in clean_att_url:
                    dl_headers['Referer'] = 'https://gdt.gov.vn/wps/portal/?uri=nm:oid:Z6_049IL8VSOR0PF0I1OQQRMV3KU3'
                req = urllib.request.Request(clean_att_url, headers=dl_headers)
                with urllib.request.urlopen(req, context=SSL_CTX, timeout=15) as res:
                    content = res.read()
                    
                    if content and len(content) > 500 and not content.startswith(b'<html>') and b'Request Rejected' not in content:
                        is_pdf = content.startswith(b'%PDF')
                        is_docx = content.startswith(b'PK\x03\x04')
                        is_doc = content.startswith(b'\xd0\xcf\x11\xe0')

                        if is_pdf:
                            filename = f"{clean_num}_{clean_field}.pdf"
                            cache_path = os.path.join(CACHE_DIR, filename)
                            try:
                                with open(cache_path, "wb") as f:
                                    f.write(content)
                            except Exception:
                                pass
                            safe_log(f"[AttachmentDownloader] Da tai FILE PDF THUC TE: {filename} ({len(content):,} bytes)")
                            return content, filename, "application/pdf"

                        elif is_docx or is_doc:
                            word_ext = ".docx" if is_docx else ".doc"
                            word_mt = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if is_docx else "application/msword"
                            word_filename = f"{clean_num}_{clean_field}{word_ext}"
                            word_cache = os.path.join(CACHE_DIR, word_filename)
                            try:
                                with open(word_cache, "wb") as f:
                                    f.write(content)
                            except Exception:
                                pass
                            safe_log(f"[AttachmentDownloader] Da tai FILE WORD THUC TE: {word_filename} ({len(content):,} bytes)")

                            # Trích xuất nội dung văn bản từ file Word nếu có thư viện python-docx
                            if is_docx and docx:
                                try:
                                    doc_obj = docx.Document(io.BytesIO(content))
                                    paras = [p.text.strip() for p in doc_obj.paragraphs if p.text.strip()]
                                    if paras:
                                        full_extracted = "\n".join(paras)
                                        # Kiểm tra tính khớp số hiệu trước khi ghi đè
                                        num_core = re.sub(r'[^a-zA-Z0-9]', '', doc_num.split('/')[0]).lower()
                                        if num_core in re.sub(r'[^a-zA-Z0-9]', '', full_extracted[:2000]).lower():
                                            if len(full_extracted) > len(doc.get("content", "")):
                                                doc["content"] = full_extracted
                                except Exception as err:
                                    safe_log(f"[AttachmentDownloader] Trich xuat text tu docx: {err}")

                            # Nếu người gọi cần PDF để xem trong iframe: tự động sinh PDF từ nội dung chính thức
                            if prefer_ext == "pdf":
                                pdf_bytes = PDFGenerator.generate_document_pdf(doc)
                                pdf_filename = f"{clean_num}_{clean_field}.pdf"
                                try:
                                    with open(os.path.join(CACHE_DIR, pdf_filename), "wb") as f:
                                        f.write(pdf_bytes)
                                except Exception:
                                    pass
                                return pdf_bytes, pdf_filename, "application/pdf"
                            else:
                                return content, word_filename, word_mt

            except Exception as e:
                safe_log(f"[AttachmentDownloader] Khong the tai tu link {att_url}: {e}")

        # 2. Sinh file PDF văn bản chính thức chuẩn thể thức hành chính với TOÀN VĂN NỘI DUNG ĐẦY ĐỦ
        safe_log(f"[AttachmentDownloader] Sinh file PDF van ban chinh thuc: {doc_num}")
        pdf_bytes = PDFGenerator.generate_document_pdf(doc)
        filename = f"{clean_num}_{clean_field}.pdf"

        # Lưu vào cache để lần sau tải nhanh
        cache_path = os.path.join(CACHE_DIR, filename)
        try:
            with open(cache_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception:
            pass

        return pdf_bytes, filename, "application/pdf"

    @staticmethod
    def get_word_html_preview(doc: Dict[str, Any]) -> str:
        """
        Tạo bản xem trước trực quan HTML từ file Word (.docx) bằng thư viện mammoth.
        Nếu không có file .docx, tạo giao diện văn bản hành chính mẫu đẹp mắt.
        """
        doc_num = (doc.get("doc_number") or "VanBan").strip()
        field = doc.get("field", "Chung")
        clean_num = re.sub(r'[/\\:*?"<>| ]', '_', doc_num)
        clean_field = re.sub(r'[/\\:*?"<>| ]', '_', field)

        # 1. Thử đọc file .docx từ cache
        docx_path = os.path.join(CACHE_DIR, f"{clean_num}_{clean_field}.docx")
        if not os.path.exists(docx_path):
            # Thử tải file Word về
            try:
                AttachmentDownloader.get_document_payload(doc, prefer_ext="docx")
            except Exception:
                pass

        if os.path.exists(docx_path) and mammoth:
            try:
                with open(docx_path, "rb") as f:
                    result = mammoth.convert_to_html(f)
                    if result.value and len(result.value.strip()) > 100:
                        return f"""<div class="mammoth-rendered-document bg-white p-8 md:p-12 shadow-sm border border-slate-200 rounded max-w-4xl mx-auto font-serif text-slate-800 leading-relaxed text-sm md:text-base">
                            {result.value}
                        </div>"""
            except Exception as e:
                safe_log(f"[AttachmentDownloader] Mammoth convert error: {e}")

        # 2. Fallback: Render văn bản hành chính đẹp mắt từ doc["content"]
        raw_content = doc.get("content", doc.get("title", ""))
        lines = raw_content.split("\n")
        
        # Lọc bỏ các dòng tiêu đề trùng lặp ở đầu nếu có
        cleaned_lines = []
        in_hdr = True
        hdr_pats = [
            r'^\s*cộng\s+hòa\s+xã\s+hội\s+chủ\s+nghĩa\s+việt\s+nam\s*$',
            r'^\s*độc\s+lập\s*[-–—]\s*tự\s+do\s*[-–—]\s*hạnh\s+phúc\s*$',
            r'^\s*[-–—_=\*\.]{3,}\s*$',
            r'^\s*số\s*:\s*.*$',
            r'^\s*(?:hà\s+nội|tp\.?|thành\s+phố|tỉnh)\s*.*,\s*ngày.*$',
        ]
        issuing = doc.get("issuing_body", "").strip()
        doc_num = doc.get("doc_number", "").strip()
        title = doc.get("title", "").strip()

        for line in lines:
            l = line.strip()
            if not l:
                continue
            if in_hdr:
                is_h = False
                for p in hdr_pats:
                    if re.match(p, l, re.IGNORECASE):
                        is_h = True
                        break
                if not is_h and issuing and l.upper() == issuing.upper():
                    is_h = True
                if not is_h and doc_num and doc_num.lower() in l.lower() and len(l) < len(doc_num) + 15:
                    is_h = True
                if not is_h and (l.upper() == title.upper() or (len(l) > 20 and l.lower() in title.lower() and len(l) > len(title) * 0.8)):
                    is_h = True
                if not is_h and (l.upper().startswith("V/V ") or l.upper().startswith("V/V: ")) and len(l) < 140:
                    is_h = True
                if is_h:
                    continue
                else:
                    in_hdr = False
            cleaned_lines.append(l)

        html_lines = []
        for l in cleaned_lines:
            if re.match(r'^(?:NƠI NHẬN|Nơi nhận)\s*:', l, re.IGNORECASE):
                break
            elif re.match(r'^(?:Kính gửi|KÍNH GỬI)\s*:', l, re.IGNORECASE):
                html_lines.append(f'<p class="font-bold italic text-[#002e5b] mt-3 mb-1 text-sm md:text-base">{l}</p>')
            elif re.match(r'^(?:[0-9IVXLCDM]+\.|\-|\+)\s+', l):
                html_lines.append(f'<p class="my-1.5 pl-4 text-justify font-sans">{l}</p>')
            elif re.match(r'^(?:Điều|ĐIỀU|Chương|CHƯƠNG)\s+[0-9IVXLCDM]+', l):
                html_lines.append(f'<h3 class="font-bold text-base text-[#002e5b] mt-4 mb-2">{l}</h3>')
            elif re.match(r'^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+', l):
                html_lines.append(f'<h2 class="font-black text-base text-[#004b93] uppercase mt-5 mb-2 border-b border-blue-100 pb-1">{l}</h2>')
            elif 'Căn cứ' in l or 'căn cứ' in l:
                html_lines.append(f'<p class="italic text-slate-600 my-1 text-sm">{l}</p>')
            else:
                html_lines.append(f'<p class="my-1.5 text-justify leading-relaxed">{l}</p>')

        body_html = "\n".join(html_lines)
        return f"""<div class="admin-rendered-document bg-white p-8 md:p-12 shadow-sm border border-slate-200 rounded max-w-4xl mx-auto font-serif text-slate-800 leading-relaxed">
            <div class="grid grid-cols-2 gap-4 pb-6 border-b border-slate-200 text-xs md:text-sm font-sans mb-6">
                <div class="text-center font-bold text-[#002e5b]">
                    <p class="uppercase">{doc.get('issuing_body', 'CƠ QUAN BAN HÀNH')}</p>
                    <p class="text-xs text-slate-600 font-mono mt-1">Số: {doc.get('doc_number', '...')}</p>
                    <hr class="w-20 mx-auto mt-2 border-[#004b93]"/>
                </div>
                <div class="text-center font-bold text-slate-900">
                    <p class="uppercase">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p>
                    <p class="text-xs text-slate-800">Độc lập - Tự do - Hạnh phúc</p>
                    <hr class="w-28 mx-auto mt-2 border-slate-800"/>
                    <p class="italic font-normal text-xs text-slate-600 mt-2">Hà Nội, ngày {doc.get('issue_date', '2026')}</p>
                </div>
            </div>
            <div class="text-center my-6">
                <h1 class="text-lg md:text-xl font-black text-[#002e5b] uppercase tracking-wide">{doc.get('doc_type', 'VĂN BẢN')}</h1>
                <p class="font-bold text-slate-800 mt-2 max-w-2xl mx-auto text-sm md:text-base leading-snug">{doc.get('title', '')}</p>
            </div>
            <div class="document-content-body text-sm md:text-[15px] space-y-1">
                {body_html}
            </div>
            <div class="grid grid-cols-2 gap-4 pt-8 mt-8 border-t border-slate-200 text-xs font-sans">
                <div>
                    <p class="font-bold italic text-slate-700">Nơi nhận:</p>
                    <p class="text-slate-600">- Các đơn vị trực thuộc;</p>
                    <p class="text-slate-600">- Người nộp thuế, Doanh nghiệp;</p>
                    <p class="text-slate-600">- Lưu: VT, PC.</p>
                </div>
                <div class="text-center">
                    <p class="font-bold uppercase text-[#002e5b]">{doc.get('signer_title', 'THỦ TRƯỞNG ĐƠN VỊ')}</p>
                    <div class="h-14 flex items-center justify-center text-emerald-700 font-semibold italic text-xs">
                        (Đã ký số điện tử)
                    </div>
                    <p class="font-bold text-slate-900">{doc.get('signer_name', '')}</p>
                </div>
            </div>
        </div>"""
