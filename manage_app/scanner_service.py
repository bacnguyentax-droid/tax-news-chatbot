import os
import sys
import re
import json
import hashlib
import datetime
import urllib.request
import ssl
from typing import List, Dict, Any, Optional

from config_manager import ConfigManager

class ScannerService:
    def __init__(self):
        self.catalog_file = os.path.join(os.path.dirname(__file__), "full_catalog.json")
        self.cached_documents = self._load_initial_catalog()
        self.last_crawl_time = None

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Chuyển đổi chuỗi ngày định dạng DD/MM/YYYY hoặc YYYY-MM-DD thành datetime.date"""
        if not date_str:
            return None
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _load_initial_catalog(self) -> List[Dict[str, Any]]:
        """Tải toàn bộ cơ sở dữ liệu văn bản từ file full_catalog.json"""
        docs = []
        if os.path.exists(self.catalog_file):
            try:
                with open(self.catalog_file, "r", encoding="utf-8") as f:
                    docs = json.load(f)
            except Exception as e:
                print(f"[ScannerService] Error loading full_catalog.json: {e}")
        
        # Nếu chưa có hoặc lỗi, nạp dữ liệu mặc định
        if not docs:
            docs = self._init_fallback_db()

        self._normalize_docs_metadata(docs)
        return docs

    def _normalize_docs_metadata(self, docs: List[Dict[str, Any]]) -> None:
        """Đảm bảo mọi văn bản có đầy đủ ID, file_name, folder_id và status"""
        config = ConfigManager.load_config()
        default_fid = config.get("google_drive", {}).get("default_folder_id", "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK")

        for doc in docs:
            num = doc.get("doc_number", "VB")
            date_s = doc.get("issue_date", "2026")
            field = doc.get("field", "Thuế")
            raw_id = f"{num}_{date_s}"
            
            if "id" not in doc or not doc["id"]:
                doc["id"] = hashlib.md5(raw_id.encode('utf-8')).hexdigest()[:12]
            
            if "selected_folder_id" not in doc or not doc["selected_folder_id"]:
                doc["selected_folder_id"] = default_fid
            
            if "status" not in doc:
                doc["status"] = "Chưa lưu Drive"
            
            if "is_downloaded" not in doc:
                doc["is_downloaded"] = False
                
            if "drive_link" not in doc:
                doc["drive_link"] = ""
                
            clean_num = re.sub(r'[/\\:*?"<>|]', '_', num)
            doc["file_name"] = f"{clean_num}_{field}.pdf"

    def crawl_live_gdt_portal(self, timeout: int = 5) -> int:
        """
        Dò quét trực tiếp và tự động từ Cổng Thông tin Điện tử Tổng cục Thuế (gdt.gov.vn).
        Trích xuất văn bản mới nhất từ bảng tra cứu và tự động lưu link tải file PDF đính kèm chính thức.
        """
        urls = [
            'https://gdt.gov.vn/wps/portal/?uri=nm:oid:Z6_049IL8VSOR0PF0I1OQQRMV3KU3',
            'https://gdt.gov.vn/wps/portal/?uri=nm:oid:Z6_CQKCVKV008FRE0IM9AV84E10D1',
            'https://gdt.gov.vn/wps/portal'
        ]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        from bs4 import BeautifulSoup
        new_count = 0
        existing_numbers = {d.get("doc_number") for d in self.cached_documents if d.get("doc_number")}

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as res:
                    html = res.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')

                # 1. Quét theo các hàng bảng văn bản chính thức (Table Rows)
                for tr in soup.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) >= 4:
                        stt = tds[0].get_text(strip=True)
                        if not stt.isdigit():
                            continue
                        num_a = tds[1].find('a')
                        doc_number = (num_a.get_text(strip=True) if num_a else tds[1].get_text(strip=True)).strip()
                        doc_number = doc_number.replace('С', 'C').replace('Р', 'P')
                        issue_date = tds[2].get_text(strip=True)

                        title_a = tds[3].find('a')
                        title = title_a.get_text(strip=True) if title_a else tds[3].get_text(strip=True)

                        detail_href = (num_a.get('href') if num_a else (title_a.get('href') if title_a else ''))
                        detail_url = f"https://gdt.gov.vn{detail_href}" if detail_href.startswith('/') else (detail_href or url)

                        # Bóc tách link tải file PDF chính thức từ nút 'Tải về' hoặc link connect
                        att_url = ''
                        for a in tds[3].find_all('a'):
                            h = a.get('href', '')
                            if 'tải về' in a.get_text(strip=True).lower() or '/wps/wcm/connect/' in h or '.pdf' in h.lower():
                                att_url = f"https://gdt.gov.vn{h}" if h.startswith('/') else h
                                break

                        if not doc_number:
                            continue

                        # Nếu văn bản đã có sẵn, cập nhật link tải file đính kèm chính thức và link chi tiết
                        if doc_number in existing_numbers:
                            for ex in self.cached_documents:
                                if ex.get("doc_number") == doc_number:
                                    if att_url and not ex.get("attachment_url"):
                                        ex["attachment_url"] = att_url
                                    if detail_url and 'http' in detail_url:
                                        ex["source_url"] = detail_url
                            continue

                        # Xác định loại văn bản
                        doc_type = "Công văn"
                        t_lower = title.lower()
                        if "quyết định" in t_lower or "qđ" in doc_number.lower():
                            doc_type = "Quyết định"
                        elif "thông tư" in t_lower or "tt" in doc_number.lower():
                            doc_type = "Thông tư"
                        elif "nghị định" in t_lower or "nđ" in doc_number.lower():
                            doc_type = "Nghị định"
                        elif "nghị quyết" in t_lower or "nq" in doc_number.lower():
                            doc_type = "Nghị quyết"

                        # Cơ quan ban hành
                        issuing_body = "Cục Thuế"
                        if "bộ tài chính" in t_lower or "btc" in doc_number.lower():
                            issuing_body = "Bộ Tài chính"
                        elif "tổng cục thuế" in t_lower or "tct" in doc_number.lower():
                            issuing_body = "Tổng cục Thuế"
                        elif "chính phủ" in t_lower:
                            issuing_body = "Chính phủ"

                        # Lĩnh vực
                        field = "Thuế"
                        if any(k in t_lower for k in ['hóa đơn', 'hđđt', 'máy tính tiền', 'tem điện tử']):
                            field = "Hóa đơn điện tử"
                        elif any(k in t_lower for k in ['thuê đất', 'tiền đất', 'tiền sử dụng đất', 'đất đai']):
                            field = "Doanh nghiệp"
                        elif any(k in t_lower for k in ['gtgt', 'giá trị gia tăng']):
                            field = "Giá trị gia tăng"
                        elif any(k in t_lower for k in ['tndn', 'thu nhập doanh nghiệp']):
                            field = "Thu nhập doanh nghiệp"
                        elif any(k in t_lower for k in ['tncn', 'thu nhập cá nhân', 'tiền lương', 'vneid']):
                            field = "Thu nhập cá nhân"
                        elif any(k in t_lower for k in ['hộ kinh doanh', 'khoán thuế']):
                            field = "Hộ kinh doanh"
                        elif any(k in t_lower for k in ['quản lý thu', 'nộp khoản thu', 'lệ phí', 'thủ tục']):
                            field = "Doanh nghiệp"

                        new_doc = {
                            "doc_number": doc_number,
                            "doc_type": doc_type,
                            "issuing_body": issuing_body,
                            "issue_date": issue_date,
                            "effective_date": issue_date,
                            "title": title,
                            "summary": title,
                            "field": field,
                            "source": "gdt.gov.vn",
                            "source_name": "Tổng cục Thuế",
                            "source_url": detail_url,
                            "attachment_url": att_url,
                            "signer_title": "Lãnh đạo cơ quan ban hành",
                            "signer_name": issuing_body,
                            "content": f"{title}\n\nVăn bản được phát hành chính thức ngày {issue_date} trên Cổng thông tin Tổng cục Thuế (gdt.gov.vn)."
                        }
                        self.cached_documents.insert(0, new_doc)
                        existing_numbers.add(doc_number)
                        new_count += 1

                # 2. Quét bổ sung các liên kết thẻ a trên trang
                for a in soup.find_all('a'):
                    text = a.get_text(strip=True)
                    href = a.get('href', '')
                    if not href or len(text) < 15:
                        continue

                    doc_type = None
                    if 'công văn' in text.lower():
                        doc_type = 'Công văn'
                    elif 'quyết định' in text.lower():
                        doc_type = 'Quyết định'
                    elif 'thông tư' in text.lower():
                        doc_type = 'Thông tư'
                    elif 'nghị định' in text.lower():
                        doc_type = 'Nghị định'

                    if not doc_type:
                        continue

                    m = re.search(r'([0-9]+/[0-9]{4}/[A-Z0-9_\-\.À-ỹ\u0400-\u04FF]+)', text, re.IGNORECASE)
                    if m:
                        doc_number = m.group(1).replace('С', 'C').replace('Р', 'P')
                    else:
                        m2 = re.search(r'(?:số|số:)\s*([0-9]+/[A-Z0-9_\-\.À-ỹ]+)', text, re.IGNORECASE)
                        if m2:
                            doc_number = m2.group(1).strip()
                        else:
                            continue

                    if doc_number in existing_numbers:
                        continue

                    date_match = re.search(r'ngày\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})|\((\d{1,2}[/-]\d{1,2}[/-]\d{4})\)', text)
                    issue_date = "2026"
                    if date_match:
                        d_str = date_match.group(1) or date_match.group(2)
                        d_str = d_str.replace('-', '/')
                        parts = d_str.split('/')
                        if len(parts) == 3:
                            issue_date = f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"

                    issuing_body = "Cục Thuế"
                    if 'bộ tài chính' in text.lower():
                        issuing_body = 'Bộ Tài chính'
                    elif 'tổng cục thuế' in text.lower():
                        issuing_body = 'Tổng cục Thuế'
                    elif 'chính phủ' in text.lower():
                        issuing_body = 'Chính phủ'

                    full_url = f"https://gdt.gov.vn{href}" if href.startswith('/') else href

                    new_doc = {
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": issue_date,
                        "effective_date": issue_date,
                        "title": text,
                        "summary": text,
                        "field": "Thuế",
                        "source": "gdt.gov.vn",
                        "source_name": "Tổng cục Thuế",
                        "source_url": full_url,
                        "attachment_url": "",
                        "signer_title": "Lãnh đạo cơ quan ban hành",
                        "signer_name": issuing_body,
                        "content": f"{text}\n\nVăn bản phát hành ngày {issue_date}."
                    }
                    self.cached_documents.insert(0, new_doc)
                    existing_numbers.add(doc_number)
                    new_count += 1
            except Exception:
                pass

        if new_count > 0:
            self._normalize_docs_metadata(self.cached_documents)
            try:
                with open(self.catalog_file, "w", encoding="utf-8") as f:
                    json.dump(self.cached_documents, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        self.last_crawl_time = datetime.datetime.now()
        return new_count

    def crawl_live_congbao_portal(self, timeout: int = 5) -> int:
        """
        Dò quét trực tiếp và tự động từ Cổng Công báo Nước CHXHCN Việt Nam (congbao.chinhphu.vn).
        Trích xuất văn bản mới nhất, tự động lấy link tải file PDF/DOCX từ g7.cdnchinhphu.vn.
        """
        urls = [
            'https://congbao.chinhphu.vn/van-ban-dang-cong-bao.htm',
            'https://congbao.chinhphu.vn/van-ban-dang-cong-bao/bo-tai-chinh-c10.htm',
            'https://congbao.chinhphu.vn/van-ban-dang-cong-bao/van-ban-hop-nhat-l7.htm',
            'https://congbao.chinhphu.vn/van-ban-dang-cong-bao/chinh-phu-c1.htm'
        ]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        from bs4 import BeautifulSoup
        new_count = 0
        existing_numbers = {d.get("doc_number") for d in self.cached_documents if d.get("doc_number")}

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as res:
                    html = res.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')

                items = soup.find_all('div', class_='item--vb')
                for it in items:
                    a_tag = it.find('a', href=re.compile(r'/van-ban/'))
                    if not a_tag:
                        continue
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get('href', '')
                    if not href or len(title) < 15:
                        continue

                    full_url = f"https://congbao.chinhphu.vn{href}" if href.startswith('/') else href

                    # Phân loại văn bản
                    doc_type = "Văn bản"
                    t_lower = title.lower()
                    if "văn bản hợp nhất" in t_lower:
                        doc_type = "Văn bản hợp nhất"
                    elif "nghị định" in t_lower:
                        doc_type = "Nghị định"
                    elif "thông tư" in t_lower:
                        doc_type = "Thông tư"
                    elif "quyết định" in t_lower:
                        doc_type = "Quyết định"
                    elif "nghị quyết" in t_lower:
                        doc_type = "Nghị quyết"
                    elif "luật" in t_lower:
                        doc_type = "Luật"

                    # Bóc tách số hiệu
                    doc_number = None
                    m = re.search(r'(?:số|số:)\s*([0-9]+/[0-9]{4}/[A-Z0-9_\-\.]+)', title, re.IGNORECASE)
                    if not m:
                        m = re.search(r'([0-9]+/[0-9]{4}/[A-Z0-9_\-\.]+)', title)
                    if not m:
                        m = re.search(r'(?:số|số:)\s*([0-9]+/[A-Z0-9_\-\.]+)', title, re.IGNORECASE)
                    
                    if m:
                        doc_number = m.group(1).strip()
                    else:
                        continue

                    if doc_number in existing_numbers:
                        continue

                    # Bóc tách ngày tháng
                    text_all = it.get_text(" ", strip=True)
                    dm = re.search(r'ngày\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', text_all)
                    date_s = "2026"
                    if dm:
                        d_val = dm.group(1)
                        if '-' in d_val:
                            p = d_val.split('-')
                            if len(p) == 3:
                                date_s = f"{p[2]}/{p[1]}/{p[0]}"
                        else:
                            date_s = d_val

                    # Cơ quan ban hành
                    issuing_body = "Chính phủ"
                    if "nhnn" in doc_number.lower() or "ngân hàng" in t_lower:
                        issuing_body = "Ngân hàng Nhà nước"
                    elif "btc" in doc_number.lower() or "tài chính" in t_lower:
                        issuing_body = "Bộ Tài chính"
                    elif "ttg" in doc_number.lower() or "thủ tướng" in t_lower:
                        issuing_body = "Thủ tướng Chính phủ"
                    elif "bca" in doc_number.lower():
                        issuing_body = "Bộ Công an"

                    # Lĩnh vực
                    field = "Doanh nghiệp"
                    if any(k in t_lower for k in ["thuế", "lệ phí", "ngân sách"]):
                        field = "Thuế"
                    elif "hóa đơn" in t_lower:
                        field = "Hóa đơn điện tử"
                    elif "ngoại hối" in t_lower or "đầu tư" in t_lower or "doanh nghiệp" in t_lower:
                        field = "Doanh nghiệp"
                    elif "hộ kinh doanh" in t_lower:
                        field = "Hộ kinh doanh"

                    new_doc = {
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": date_s,
                        "effective_date": date_s,
                        "title": title,
                        "summary": f"{title}. Đăng tải trên Cổng Công báo Nước CHXHCN Việt Nam (congbao.chinhphu.vn).",
                        "field": field,
                        "source": "congbao.chinhphu.vn",
                        "source_name": "Cổng Công báo Nước CHXHCN Việt Nam",
                        "source_url": full_url,
                        "attachment_url": "",
                        "signer_title": issuing_body,
                        "signer_name": "",
                        "content": f"{title}\n\nVăn bản được đăng tải chính thức trên Cổng Công báo Nước CHXHCN Việt Nam ngày {date_s}. Quy định chi tiết các điều khoản thi hành, quyền hạn và nghĩa vụ đối với tổ chức, cá nhân, doanh nghiệp trên toàn quốc."
                    }
                    self.cached_documents.insert(0, new_doc)
                    existing_numbers.add(doc_number)
                    new_count += 1
            except Exception:
                pass

        if new_count > 0:
            self._normalize_docs_metadata(self.cached_documents)
            try:
                with open(self.catalog_file, "w", encoding="utf-8") as f:
                    json.dump(self.cached_documents, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return new_count

    def crawl_live_vbpl_portal(self, timeout: int = 5) -> int:
        """
        Dò quét trực tiếp và tự động từ CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn).
        Trích xuất văn bản mới nhất, lấy định danh id, file đính kèm chính thức và
        đường dẫn chi tiết theo định dạng chuẩn https://vbpl.vn/van-ban/chi-tiet/<slug>.
        """
        action_id = "c529d164f28418e5898a834422629e64c6816af1"
        url = "https://vbpl.vn"
        keywords = ["390/2026", "2026", "thuế", "kinh doanh vàng"]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Next-Action': action_id,
            'Content-Type': 'text/plain;charset=UTF-8',
            'Accept': 'text/x-component'
        }

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        import unicodedata
        def make_vbpl_slug(title_str: str) -> str:
            text = title_str.lower()
            text = text.replace('đ', 'd').replace('Đ', 'd')
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
            text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
            return text

        new_count = 0
        existing_numbers = {d.get("doc_number") for d in self.cached_documents if d.get("doc_number")}

        for kw in keywords:
            try:
                payload = json.dumps([{"keyword": kw, "pageSize": 10}]).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as res:
                    data = res.read().decode('utf-8', errors='ignore')

                m = re.search(r'\{"total":\d+,"pageNumber":\d+.*?"items":\[(.*?)\]\}', data)
                if not m:
                    continue
                items = json.loads("[" + m.group(1) + "]")
                for it in items:
                    doc_number = (it.get("docNum") or "").strip()
                    title = (it.get("title") or "").strip()
                    if not doc_number or not title:
                        continue

                    if doc_number in existing_numbers:
                        # Cập nhật thêm vbpl_id và link chi tiết nếu văn bản đã có sẵn
                        for ex in self.cached_documents:
                            if ex.get("doc_number") == doc_number:
                                if not ex.get("vbpl_id") and it.get("id"):
                                    ex["vbpl_id"] = it.get("id")
                                slug = make_vbpl_slug(title)
                                ex["source_url"] = f"https://vbpl.vn/van-ban/chi-tiet/{slug}"
                                rel_files = [f.get("fileName") for f in it.get("documentRelatedList", []) if f.get("fileName")]
                                if rel_files:
                                    pdf_files = [f for f in rel_files if f.lower().endswith(".pdf")]
                                    ex["vbpl_file_name"] = pdf_files[0] if pdf_files else rel_files[0]
                                    ex["vbpl_files"] = rel_files
                        continue

                    # Bóc tách ngày ban hành
                    issue_date_raw = it.get("issueDate") or it.get("effFrom")
                    issue_date = "2026"
                    if issue_date_raw:
                        dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', issue_date_raw)
                        if dm:
                            issue_date = f"{dm.group(3)}/{dm.group(2)}/{dm.group(1)}"

                    eff_date_raw = it.get("effFrom") or issue_date_raw
                    effective_date = issue_date
                    if eff_date_raw:
                        dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', eff_date_raw)
                        if dm:
                            effective_date = f"{dm.group(3)}/{dm.group(2)}/{dm.group(1)}"

                    # Loại văn bản
                    doc_type_obj = it.get("docType") or {}
                    doc_type = doc_type_obj.get("name") or "Văn bản"
                    t_lower = title.lower()
                    if not doc_type or doc_type == "Văn bản":
                        if "nghị định" in t_lower:
                            doc_type = "Nghị định"
                        elif "thông tư" in t_lower:
                            doc_type = "Thông tư"
                        elif "nghị quyết" in t_lower:
                            doc_type = "Nghị quyết"
                        elif "quyết định" in t_lower:
                            doc_type = "Quyết định"
                        elif "luật" in t_lower:
                            doc_type = "Luật"

                    # Cơ quan ban hành
                    issuing_body = it.get("agencyName") or "Chính phủ"
                    if "quốc hội" in t_lower or "ubtvqh" in doc_number.lower() or "qh" in doc_number.lower():
                        issuing_body = "Quốc hội"
                    elif "bộ tài chính" in t_lower or "btc" in doc_number.lower():
                        issuing_body = "Bộ Tài chính"

                    # Lĩnh vực
                    field = "Doanh nghiệp"
                    if any(k in t_lower for k in ["thuế", "lệ phí", "ngân sách", "tài chính"]):
                        field = "Thuế"
                    elif any(k in t_lower for k in ["hóa đơn", "hđđt", "kinh doanh vàng"]):
                        field = "Hóa đơn điện tử"
                    elif any(k in t_lower for k in ["thu nhập cá nhân", "tncn"]):
                        field = "Thu nhập cá nhân"
                    elif any(k in t_lower for k in ["giá trị gia tăng", "gtgt"]):
                        field = "Giá trị gia tăng"

                    # Link chi tiết văn bản
                    slug = make_vbpl_slug(title)
                    detail_url = f"https://vbpl.vn/van-ban/chi-tiet/{slug}"

                    # Danh sách file đính kèm
                    rel_files = [f.get("fileName") for f in it.get("documentRelatedList", []) if f.get("fileName")]
                    pdf_files = [f for f in rel_files if f.lower().endswith(".pdf")]
                    chosen_file = pdf_files[0] if pdf_files else (rel_files[0] if rel_files else "")

                    new_doc = {
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": issue_date,
                        "effective_date": effective_date,
                        "title": title,
                        "summary": f"{title}. CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn).",
                        "field": field,
                        "source": "vbpl.vn",
                        "source_name": "Cơ sở dữ liệu Quốc gia về VBPL",
                        "source_url": detail_url,
                        "vbpl_id": it.get("id"),
                        "vbpl_file_name": chosen_file,
                        "vbpl_files": rel_files,
                        "signer_title": "Thủ tướng Chính phủ" if issuing_body == "Chính phủ" else "Lãnh đạo cơ quan ban hành",
                        "signer_name": "Phạm Minh Chính" if issuing_body == "Chính phủ" else "",
                        "content": f"{title}\n\nVăn bản được đăng tải chính thức trên CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn) ngày {issue_date}."
                    }
                    self.cached_documents.insert(0, new_doc)
                    existing_numbers.add(doc_number)
                    new_count += 1
            except Exception:
                pass

        if new_count > 0:
            self._normalize_docs_metadata(self.cached_documents)
            try:
                with open(self.catalog_file, "w", encoding="utf-8") as f:
                    json.dump(self.cached_documents, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return new_count

    def _domain_matches(self, doc_source: str, active_domain: str) -> bool:
        """Kiểm tra nguồn văn bản có khớp với nguồn website người dùng chọn hay không"""
        d1 = (doc_source or "").lower().replace("www.", "").strip()
        d2 = (active_domain or "").lower().replace("www.", "").strip()
        if not d1 or not d2:
            return False
        if d1 == d2:
            return True
        # Hỗ trợ tên miền Công báo linh hoạt (congbao.chinhphu.vn hoặc congbao.gov.vn)
        if "congbao" in d1 and "congbao" in d2:
            return True
        # Hỗ trợ Quốc hội (quochoi.vn hoặc vietlaw.quochoi.vn)
        if "quochoi" in d1 and "quochoi" in d2:
            return True
        # Hỗ trợ Bộ Tài chính (mof.gov.vn)
        if "mof" in d1 and "mof" in d2:
            return True
        # Hỗ trợ Tổng cục Thuế (gdt.gov.vn)
        if "gdt" in d1 and "gdt" in d2:
            return True
        # Hỗ trợ VBPL (vbpl.vn)
        if "vbpl" in d1 and "vbpl" in d2:
            return True
        if d1.endswith("." + d2) or d2.endswith("." + d1) or (d2 in d1) or (d1 in d2):
            return True
        return False

    def scan_documents(self, fields: str, from_date_str: str = "", to_date_str: str = "", doc_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Dò quét văn bản theo danh sách lĩnh vực và khoảng thời gian.
        Chỉ tìm kiếm văn bản từ các trang web nguồn đang được kích hoạt (enabled).
        Tuân thủ nghiêm ngặt khoảng thời gian từ ngày đến ngày phát hành.
        """
        # Lấy danh sách website nguồn được kích hoạt và chuẩn hóa tên miền
        sources = ConfigManager.get_sources()
        active_domains_norm = [s.get("domain", "").lower().replace("www.", "").strip() for s in sources if s.get("enabled", True)]

        # Dò quét trực tiếp từ các cổng thông tin trực tuyến nếu được kích hoạt
        now = datetime.datetime.now()
        if not self.last_crawl_time or (now - self.last_crawl_time).total_seconds() > 300:
            if any("congbao" in d for d in active_domains_norm):
                self.crawl_live_congbao_portal(timeout=4)
            if any("gdt" in d for d in active_domains_norm):
                self.crawl_live_gdt_portal(timeout=3)
            if any("vbpl" in d for d in active_domains_norm):
                self.crawl_live_vbpl_portal(timeout=4)
            self.last_crawl_time = now

        # Tự động nạp dữ liệu cập nhật mới nhất từ catalog
        self.cached_documents = self._load_initial_catalog()

        results: List[Dict[str, Any]] = []

        # Chuẩn hóa lĩnh vực nhập vào
        keywords = [k.strip().lower() for k in re.split(r'[,;|\n]', fields) if k.strip()]
        if not keywords:
            keywords = ["thuế", "hộ kinh doanh", "thu nhập cá nhân", "doanh nghiệp", "tổ chức", "giá trị gia tăng", "thu nhập doanh nghiệp", "giao dịch liên kết", "hóa đơn điện tử"]

        from_date = self._parse_date(from_date_str)
        to_date = self._parse_date(to_date_str)

        today = datetime.date.today()
        if not to_date:
            to_date = today
        if not from_date:
            from_date = datetime.date(today.year, 1, 1)

        # Lọc kho dữ liệu văn bản theo Website nguồn, Thời gian và Lĩnh vực
        for doc in self.cached_documents:
            # 1. Chỉ tìm kiếm văn bản từ các trang web nguồn đã chọn (sử dụng _domain_matches)
            doc_source_norm = doc.get("source", "").lower().replace("www.", "").strip()
            match_source = False
            if not active_domains_norm:
                match_source = True
            else:
                for act in active_domains_norm:
                    if self._domain_matches(doc_source_norm, act):
                        match_source = True
                        break
            if not match_source:
                continue

            # 2. Kiểm tra ngày phát hành thực tế
            doc_date = self._parse_date(doc.get("issue_date", ""))
            if not doc_date:
                continue

            if not (from_date <= doc_date <= to_date):
                continue

            # 3. Kiểm tra loại văn bản nếu có lọc
            if doc_types and doc.get("doc_type") not in doc_types:
                continue

            # 4. Kiểm tra sự trùng khớp lĩnh vực / từ khóa chuyên sâu ngành Thuế
            match_field = False
            doc_text = f"{doc.get('title', '')} {doc.get('summary', '')} {doc.get('field', '')} {doc.get('doc_number', '')} {doc.get('issuing_body', '')} {doc.get('content', '')}".lower()

            for kw in keywords:
                if kw in doc_text:
                    match_field = True
                    break
                # Biến thể chuyên ngành
                if kw in ("thuế", "tax") and any(w in doc_text for w in ["thuế", "hóa đơn", "kê khai", "tổng cục thuế", "cục thuế", "bộ tài chính", "nộp thuế", "hoàn thuế", "gia hạn", "quản lý thu", "lệ phí", "ngân sách", "chính sách tài khóa", "tài chính"]):
                    match_field = True
                    break
                if kw in ("hộ kinh doanh", "kinh doanh cá thể") and any(w in doc_text for w in ["hộ kinh doanh", "cá nhân kinh doanh", "hộ cá thể", "khoán thuế", "thông tư 40", "nghị định 01", "máy tính tiền", "bán lẻ", "ăn uống", "xăng dầu", "kinh doanh vàng"]):
                    match_field = True
                    break
                if kw in ("thu nhập cá nhân", "tncn") and any(w in doc_text for w in ["thu nhập cá nhân", "tncn", "người phụ thuộc", "giảm trừ gia cảnh", "tiền lương", "quyết toán thuế tncn", "vneid", "mst cá nhân", "mã số thuế cá nhân", "thông tư 26/2026", "người có công"]):
                    match_field = True
                    break
                if kw in ("doanh nghiệp", "dn") and any(w in doc_text for w in ["doanh nghiệp", "đăng ký doanh nghiệp", "luật doanh nghiệp", "chi phí doanh nghiệp", "doanh nghiệp fdi", "tổ chức kinh tế", "tiền thuê đất", "tiền sử dụng đất", "tiền đất", "thủ tục hành chính", "kinh doanh vàng", "ngoại hối", "chứng khoán", "điện mặt trời"]):
                    match_field = True
                    break
                if kw in ("tổ chức",) and any(w in doc_text for w in ["tổ chức", "tổ chức chi trả", "đơn vị sự nghiệp", "hợp tác xã", "tổ chức kinh tế", "nghị định 376", "nghị định 373", "ngân hàng", "tổ chức tín dụng"]):
                    match_field = True
                    break
                if kw in ("giá trị gia tăng", "gtgt", "vat") and any(w in doc_text for w in ["giá trị gia tăng", "gtgt", "thuế suất 8%", "thuế suất 10%", "nghị định 72", "hoàn thuế gtgt", "nghị định 64", "khấu trừ", "luật thuế giá trị gia tăng", "48/2026", "11488/btc"]):
                    match_field = True
                    break
                if kw in ("thu nhập doanh nghiệp", "tndn") and any(w in doc_text for w in ["thu nhập doanh nghiệp", "tndn", "chi phí được trừ", "thu nhập chịu thuế", "thu nhập tính thuế", "trụ cột 2", "phúc lợi", "lãi vay", "thông tư 200", "chế độ kế toán"]):
                    match_field = True
                    break
                if kw in ("giao dịch liên kết", "gdlk") and any(w in doc_text for w in ["giao dịch liên kết", "gdlk", "nghị định 132", "chuyển giá", "chi phí lãi vay", "hồ sơ xác định giá", "ebitda"]):
                    match_field = True
                    break
                if kw in ("hóa đơn điện tử", "hđđt") and any(w in doc_text for w in ["hóa đơn điện tử", "hđđt", "nghị định 123", "thông tư 78", "thông tư 91", "máy tính tiền", "mã của cơ quan thuế", "tem điện tử", "nội dung hóa đơn", "390/2026"]):
                    match_field = True
                    break

            if match_field:
                if not any(r["doc_number"] == doc["doc_number"] for r in results):
                    results.append(doc.copy())

        # Sắp xếp mới nhất lên đầu
        results.sort(
            key=lambda d: self._parse_date(d.get("issue_date", "")) or datetime.date(2000, 1, 1),
            reverse=True
        )

        return {
            "success": True,
            "total": len(results),
            "from_date": from_date.strftime("%d/%m/%Y"),
            "to_date": to_date.strftime("%d/%m/%Y"),
            "keywords": keywords,
            "active_sources": active_domains_norm,
            "documents": results
        }

    def _init_fallback_db(self) -> List[Dict[str, Any]]:
        """Dữ liệu dự phòng tối thiểu nếu file catalog chưa tồn tại"""
        return [
            {
                "doc_number": "7815/CT-QLNT",
                "doc_type": "Công văn",
                "issuing_body": "Cục Thuế",
                "issue_date": "16/10/2026",
                "effective_date": "16/10/2026",
                "title": "Công văn số 7815/CT-QLNT ngày 16/10/2026 của Cục Thuế về quản lý thu, nộp khoản thu khác",
                "summary": "Công văn số 7815/CT-QLNT ngày 16/10/2026 của Cục Thuế về quản lý thu, nộp khoản thu khác",
                "field": "Thuế",
                "source": "gdt.gov.vn",
                "source_name": "Tổng cục Thuế",
                "source_url": "https://gdt.gov.vn/wps/portal/?uri=nm:oid:Z6_049IL8VSOR0PF0I1OQQRMV3KU3",
                "signer_title": "Lãnh đạo Cục Thuế",
                "signer_name": "Cục Thuế",
                "content": "Công văn số 7815/CT-QLNT ngày 16/10/2026 của Cục Thuế về quản lý thu, nộp khoản thu khác"
            }
        ]

scanner_service = ScannerService()
