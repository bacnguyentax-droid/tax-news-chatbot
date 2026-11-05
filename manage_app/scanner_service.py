import os
import sys
import re
import json
import hashlib
import datetime
import urllib.request
import urllib.parse
import ssl
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

from config_manager import ConfigManager


class ScannerService:
    def __init__(self):
        self.catalog_file = os.path.join(os.path.dirname(__file__), "full_catalog.json")
        self.cached_documents = self._load_initial_catalog()
        self.last_crawl_time = None
        self.last_crawl_keywords: List[str] = []

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

        if not docs:
            docs = self._init_fallback_db()

        self._normalize_docs_metadata(docs)
        return docs

    def _save_catalog(self) -> None:
        """Lưu danh sách cached_documents xuống full_catalog.json"""
        self._normalize_docs_metadata(self.cached_documents)
        try:
            with open(self.catalog_file, "w", encoding="utf-8") as f:
                json.dump(self.cached_documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ScannerService] Error saving full_catalog.json: {e}")

    def _normalize_docs_metadata(self, docs: List[Dict[str, Any]]) -> None:
        """Đảm bảo mọi văn bản có đầy đủ ID, file_name, folder_id và status"""
        config = ConfigManager.load_config()
        default_fid = config.get("google_drive", {}).get("default_folder_id", "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK")

        for doc in docs:
            num = doc.get("doc_number", "VB")
            date_s = doc.get("issue_date", "2026")
            if doc.get("source") == "quochoi.vn":
                doc["field"] = self._infer_field(doc.get("title", ""), num, doc.get("summary", ""))
            field = doc.get("field", "Khác")
            raw_id = f"{num}_{date_s}_{doc.get('source', '')}"

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

            clean_num = re.sub(r'[/\\:*?"<>|\s]+', '_', num).strip('_')
            doc["file_name"] = f"{clean_num}_{field}.pdf"

    def _infer_field(self, title: str, doc_number: str = "", summary: str = "") -> str:
        """Tự động phân loại lĩnh vực của văn bản dựa theo tiêu đề và số hiệu"""
        t_lower = f"{title} {doc_number} {summary}".lower()
        if any(k in t_lower for k in ['hóa đơn', 'hđđt', 'máy tính tiền', 'tem điện tử', 'chứng từ điện tử']):
            return "Hóa đơn điện tử"
        if any(k in t_lower for k in ['gtgt', 'giá trị gia tăng', 'hoàn thuế']):
            return "Giá trị gia tăng"
        if any(k in t_lower for k in ['tndn', 'thu nhập doanh nghiệp']):
            return "Thu nhập doanh nghiệp"
        if any(k in t_lower for k in ['tncn', 'thu nhập cá nhân', 'tiền lương', 'giảm trừ gia cảnh', 'người phụ thuộc', 'vneid']):
            return "Thu nhập cá nhân"
        if any(k in t_lower for k in ['hộ kinh doanh', 'khoán thuế', 'doanh nghiệp siêu nhỏ', 'cá nhân kinh doanh']):
            return "Hộ kinh doanh"
        if any(k in t_lower for k in ['giao dịch liên kết', 'chuyển giá', '132/2020']):
            return "Giao dịch liên kết"
        if any(k in t_lower for k in ['vị trí việc làm', 'công chức', 'viên chức', 'tổ chức cán bộ', 'chức năng, nhiệm vụ', 'thủ tục hành chính']):
            return "Vị trí việc làm"
        if any(k in t_lower for k in ['thuế', 'lệ phí', 'ngân sách', 'tt-btc', 'qđ-btc', 'tài sản mã hóa', 'kế toán', 'quyết toán']):
            return "Thuế"
        if any(k in t_lower for k in ['doanh nghiệp', 'đầu tư', 'kinh tế', 'thương mại', 'ngân hàng', 'tín dụng']):
            return "Doanh nghiệp"
        return "Khác"

    # ==================== 1. CỔNG THÔNG TIN TỔNG CỤC THUẾ (GDT.GOV.VN) ====================
    def crawl_live_gdt_portal(self, timeout: int = 6) -> List[Dict[str, Any]]:
        """
        Dò quét trực tiếp từ Cổng Thông tin Điện tử Tổng cục Thuế (gdt.gov.vn).
        Bao gồm cả bảng Văn bản quy phạm/Công văn, mục 'VĂN BẢN MỚI' và mục 'THÔNG BÁO' trên trang chủ.
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
        collected: List[Dict[str, Any]] = []
        seen_nums = set()
        seen_titles = set()

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        today_str = datetime.date.today().strftime("%d/%m/%Y")

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
                        detail_url = f"https://gdt.gov.vn{detail_href}" if detail_href.startswith('/') else (
                            f"https://gdt.gov.vn/wps/portal/{detail_href}" if detail_href.startswith('?') else (detail_href or url)
                        )

                        att_url = ''
                        for a in tds[3].find_all('a'):
                            h = a.get('href', '')
                            if 'tải về' in a.get_text(strip=True).lower() or '/wps/wcm/connect/' in h or '.pdf' in h.lower():
                                att_url = f"https://gdt.gov.vn{h}" if h.startswith('/') else h
                                break

                        if not doc_number or doc_number in seen_nums:
                            continue

                        doc_type = "Công văn"
                        t_lower = title.lower()
                        if "thông báo" in t_lower or "tb-" in doc_number.lower():
                            doc_type = "Thông báo"
                        elif "quyết định" in t_lower or "qđ" in doc_number.lower():
                            doc_type = "Quyết định"
                        elif "thông tư" in t_lower or "tt" in doc_number.lower():
                            doc_type = "Thông tư"
                        elif "nghị định" in t_lower or "nđ" in doc_number.lower():
                            doc_type = "Nghị định"
                        elif "nghị quyết" in t_lower or "nq" in doc_number.lower():
                            doc_type = "Nghị quyết"

                        issuing_body = "Cục Thuế"
                        if "bộ tài chính" in t_lower or "btc" in doc_number.lower():
                            issuing_body = "Bộ Tài chính"
                        elif "tổng cục thuế" in t_lower or "tct" in doc_number.lower():
                            issuing_body = "Tổng cục Thuế"
                        elif "chính phủ" in t_lower:
                            issuing_body = "Chính phủ"

                        field = self._infer_field(title, doc_number)

                        collected.append({
                            "doc_number": doc_number,
                            "doc_type": doc_type,
                            "issuing_body": issuing_body,
                            "issue_date": issue_date,
                            "effective_date": issue_date,
                            "title": title,
                            "summary": title,
                            "field": field,
                            "source": "gdt.gov.vn",
                            "source_name": "Cổng Thông tin Điện tử Cục Thuế (gdt.gov.vn)",
                            "source_url": detail_url,
                            "attachment_url": att_url,
                            "signer_title": "Lãnh đạo cơ quan ban hành",
                            "signer_name": issuing_body,
                            "content": f"{title}\n\nVăn bản được phát hành chính thức ngày {issue_date} trên Cổng thông tin Điện tử ngành Thuế (gdt.gov.vn)."
                        })
                        seen_nums.add(doc_number)
                        seen_titles.add(title.strip().lower())

                # 2. Quét các liên kết 'VĂN BẢN MỚI', 'THÔNG BÁO', 'LẤY Ý KIẾN DỰ THẢO' trên trang chủ gdt.gov.vn
                for a in soup.find_all('a'):
                    text = re.sub(r'\s+', ' ', a.get_text(" ", strip=True)).strip()
                    href = a.get('href', '')
                    if not href or len(text) < 18:
                        continue

                    t_lower = text.lower()
                    doc_type = None
                    if 'công văn' in t_lower:
                        doc_type = 'Công văn'
                    elif 'thông báo' in t_lower:
                        doc_type = 'Thông báo'
                    elif 'quyết định' in t_lower:
                        doc_type = 'Quyết định'
                    elif 'thông tư' in t_lower:
                        doc_type = 'Thông tư'
                    elif 'nghị định' in t_lower:
                        doc_type = 'Nghị định'
                    elif 'dự thảo' in t_lower:
                        doc_type = 'Dự thảo'

                    if not doc_type:
                        continue

                    parent_el = a.parent
                    parent_text = re.sub(r'\s+', ' ', parent_el.get_text(" ", strip=True)) if parent_el else text
                    if parent_el and parent_el.parent:
                        parent_text = re.sub(r'\s+', ' ', parent_el.parent.get_text(" ", strip=True))

                    date_match = re.search(r'ngày\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})|\((\d{1,2}[/-]\d{1,2}[/-]\d{4})\)', parent_text)
                    issue_date = today_str
                    if date_match:
                        d_str = (date_match.group(1) or date_match.group(2)).replace('-', '/')
                        parts = d_str.split('/')
                        if len(parts) == 3:
                            issue_date = f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"

                    doc_number = None
                    m = re.search(r'([0-9]+/[0-9]{4}/[A-Z0-9_\-\.À-ỹ\u0400-\u04FF]+)', text, re.IGNORECASE)
                    if m:
                        doc_number = m.group(1).replace('С', 'C').replace('Р', 'P')
                    else:
                        m2 = re.search(r'(?:số|số:)\s*([0-9]+/[A-Z0-9_\-\.À-ỹ]+)', text, re.IGNORECASE)
                        if m2:
                            doc_number = m2.group(1).strip()

                    if not doc_number:
                        if doc_type in ('Thông báo', 'Dự thảo'):
                            short_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:4].upper()
                            d_compact = issue_date.replace('/', '')[:4]
                            prefix = "TB" if doc_type == "Thông báo" else "DT"
                            doc_number = f"{prefix}-{d_compact}-{short_hash}/CT"
                        else:
                            continue

                    if doc_number in seen_nums or text.lower() in seen_titles:
                        continue

                    issuing_body = "Cục Thuế"
                    if 'bộ tài chính' in t_lower:
                        issuing_body = 'Bộ Tài chính'
                    elif 'tổng cục thuế' in t_lower:
                        issuing_body = 'Tổng cục Thuế'
                    elif 'chính phủ' in t_lower:
                        issuing_body = 'Chính phủ'

                    if href.startswith('/'):
                        full_url = f"https://gdt.gov.vn{href}"
                    elif href.startswith('?'):
                        full_url = f"https://gdt.gov.vn/wps/portal/{href}"
                    else:
                        full_url = href

                    field = self._infer_field(text, doc_number)

                    collected.append({
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": issue_date,
                        "effective_date": issue_date,
                        "title": text,
                        "summary": f"{text} (Đăng tải ngày {issue_date} trên Cổng thông tin Cục Thuế - gdt.gov.vn).",
                        "field": field,
                        "source": "gdt.gov.vn",
                        "source_name": "Cổng Thông tin Điện tử Cục Thuế (gdt.gov.vn)",
                        "source_url": full_url,
                        "attachment_url": "",
                        "signer_title": "Lãnh đạo cơ quan ban hành",
                        "signer_name": issuing_body,
                        "content": f"{text}\n\nNgày đăng tải/ban hành: {issue_date}.\nNguồn: Cổng thông tin Điện tử Cục Thuế (gdt.gov.vn)."
                    })
                    seen_nums.add(doc_number)
                    seen_titles.add(text.lower())
            except Exception as e:
                print(f"[ScannerService] GDT crawl warning ({url}): {e}")

        return collected

    # ==================== 2. CỔNG CÔNG BÁO CHÍNH PHỦ (CONGBAO.CHINHPHU.VN) ====================
    def crawl_live_congbao_portal(self, timeout: int = 6) -> List[Dict[str, Any]]:
        """
        Dò quét trực tiếp từ Cổng Công báo Nước CHXHCN Việt Nam (congbao.chinhphu.vn).
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
        collected: List[Dict[str, Any]] = []
        seen_nums = set()

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

                    doc_number = None
                    m = re.search(r'(?:số|số:)\s*([0-9]+/[0-9]{4}/[A-Z0-9_\-\.À-ỹ]+)', title, re.IGNORECASE)
                    if not m:
                        m = re.search(r'([0-9]+/[0-9]{4}/[A-Z0-9_\-\.À-ỹ]+)', title)
                    if not m:
                        m = re.search(r'(?:số|số:)\s*([0-9]+/[A-Z0-9_\-\.À-ỹ]+)', title, re.IGNORECASE)

                    if m:
                        doc_number = m.group(1).strip()
                    else:
                        continue

                    if doc_number in seen_nums:
                        continue

                    text_all = it.get_text(" ", strip=True)
                    dm = re.search(r'ngày\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4})', text_all)
                    date_s = datetime.date.today().strftime("%d/%m/%Y")
                    if dm:
                        d_val = dm.group(1)
                        if '-' in d_val:
                            p = d_val.split('-')
                            if len(p) == 3:
                                date_s = f"{p[2]}/{p[1]}/{p[0]}"
                        else:
                            date_s = d_val

                    issuing_body = "Chính phủ"
                    if "nhnn" in doc_number.lower() or "ngân hàng" in t_lower:
                        issuing_body = "Ngân hàng Nhà nước"
                    elif "btc" in doc_number.lower() or "tài chính" in t_lower:
                        issuing_body = "Bộ Tài chính"
                    elif "ttg" in doc_number.lower() or "thủ tướng" in t_lower:
                        issuing_body = "Thủ tướng Chính phủ"
                    elif "bca" in doc_number.lower():
                        issuing_body = "Bộ Công an"

                    field = self._infer_field(title, doc_number)

                    collected.append({
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
                        "content": f"{title}\n\nVăn bản được đăng tải chính thức trên Cổng Công báo Nước CHXHCN Việt Nam ngày {date_s}."
                    })
                    seen_nums.add(doc_number)
            except Exception as e:
                print(f"[ScannerService] CongBao crawl warning ({url}): {e}")

        return collected

    # ==================== 3. CSDL QUỐC GIA VỀ PHÁP LUẬT (VBPL.VN) ====================
    def crawl_live_vbpl_portal(self, keywords: Optional[List[str]] = None, timeout: int = 8) -> List[Dict[str, Any]]:
        """
        Dò quét trực tiếp từ CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn).
        - Quét danh sách văn bản mới nhất trên trang chủ (isNew=True, sortBy=issueDate desc)
        - Quét theo danh sách từ khóa động từ giao diện Web App của người dùng (sortBy=issueDate desc)
        """
        action_id = "c529d164f28418e5898a834422629e64c6816af1"
        url = "https://vbpl.vn"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Next-Action': action_id,
            'Content-Type': 'text/plain;charset=UTF-8',
            'Accept': 'text/x-component'
        }

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        def make_vbpl_slug(title_str: str) -> str:
            text = title_str.lower()
            text = text.replace('đ', 'd').replace('Đ', 'd')
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
            text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
            return text

        payload_list = [
            {"sortDirection": "desc", "sortBy": "issueDate", "pageSize": 25, "pageNumber": 1, "isNew": True}
        ]
        user_kws = [k.strip() for k in (keywords or []) if k.strip()]
        for kw in user_kws[:4]:
            payload_list.append({
                "keyword": kw,
                "sortDirection": "desc",
                "sortBy": "issueDate",
                "score": False,
                "groupVbpl": True,
                "pageSize": 15,
                "pageNumber": 1
            })

        collected: List[Dict[str, Any]] = []
        seen_nums = set()

        for query_obj in payload_list:
            try:
                payload = json.dumps([query_obj]).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as res:
                    data = res.read().decode('utf-8', errors='ignore')

                items = []
                for line in data.splitlines():
                    line_s = line.strip()
                    idx = line_s.find('{"total":')
                    if idx != -1:
                        try:
                            parsed = json.loads(line_s[idx:])
                            items = parsed.get("items") or []
                            break
                        except Exception:
                            pass

                for it in items:
                    doc_number = (it.get("docNum") or "").strip().replace('С', 'C').replace('Р', 'P')
                    title = (it.get("title") or "").strip()
                    if not doc_number or not title or doc_number in ("Số hiệu", "Số ký hiệu") or doc_number in seen_nums:
                        continue

                    slug = make_vbpl_slug(title)
                    detail_url = f"https://vbpl.vn/van-ban/chi-tiet/{slug}"
                    rel_files = [f.get("fileName") for f in (it.get("documentRelatedList") or []) if isinstance(f, dict) and f.get("fileName")]
                    pdf_files = [f for f in rel_files if f.lower().endswith(".pdf")]
                    chosen_file = pdf_files[0] if pdf_files else (rel_files[0] if rel_files else "")

                    issue_date_raw = it.get("issueDate") or it.get("effFrom")
                    issue_date = datetime.date.today().strftime("%d/%m/%Y")
                    if issue_date_raw:
                        dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(issue_date_raw))
                        if dm:
                            issue_date = f"{dm.group(3)}/{dm.group(2)}/{dm.group(1)}"

                    eff_date_raw = it.get("effFrom") or issue_date_raw
                    effective_date = issue_date
                    if eff_date_raw:
                        dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(eff_date_raw))
                        if dm:
                            effective_date = f"{dm.group(3)}/{dm.group(2)}/{dm.group(1)}"

                    doc_type_obj = it.get("docType") or {}
                    doc_type = doc_type_obj.get("name") or "Văn bản"
                    t_lower = title.lower()
                    if "thông tư" in t_lower or "/tt-" in doc_number.lower():
                        doc_type = "Thông tư"
                    elif "nghị định" in t_lower or "/nđ-" in doc_number.lower():
                        doc_type = "Nghị định"
                    elif "nghị quyết" in t_lower or "/nq-" in doc_number.lower():
                        doc_type = "Nghị quyết"
                    elif "quyết định" in t_lower or "/qđ-" in doc_number.lower():
                        doc_type = "Quyết định"
                    elif "luật" in t_lower or "/qh" in doc_number.lower():
                        doc_type = "Luật"

                    issuing_body = it.get("agencyName") or "Chính phủ"
                    if "btc" in doc_number.lower() or "bộ tài chính" in t_lower:
                        issuing_body = "Bộ Tài chính"
                    elif "quốc hội" in t_lower or "ubtvqh" in doc_number.lower() or "qh" in doc_number.lower():
                        issuing_body = "Quốc hội"
                    elif "ttg" in doc_number.lower() or "thủ tướng" in t_lower:
                        issuing_body = "Thủ tướng Chính phủ"
                    elif "nhnn" in doc_number.lower():
                        issuing_body = "Ngân hàng Nhà nước"

                    field = self._infer_field(title, doc_number)

                    collected.append({
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
                        "signer_title": "Lãnh đạo cơ quan ban hành",
                        "signer_name": issuing_body,
                        "content": f"{title}\n\nVăn bản số {doc_number} do {issuing_body} ban hành ngày {issue_date}, đăng tải chính thức trên CSDL Quốc gia về Văn bản Pháp luật (vbpl.vn)."
                    })
                    seen_nums.add(doc_number)
            except Exception as e:
                print(f"[ScannerService] VBPL crawl warning: {e}")

        return collected

    # ==================== 4. CỔNG VĂN BẢN PHÁP QUY BỘ TÀI CHÍNH (VBPQ.MOF.GOV.VN) ====================
    def crawl_live_mof_portal(self, keywords: Optional[List[str]] = None, timeout: int = 12) -> List[Dict[str, Any]]:
        """
        Dò quét trực tiếp từ Cơ sở dữ liệu Văn bản Pháp quy Bộ Tài chính (https://vbpq.mof.gov.vn/).
        Lấy đầy đủ các văn bản mới ban hành (như 65/2026/TT-BTC, 59/2026/TT-BTC, 58/2026/TT-BTC...)
        kèm link tải PDF gốc từ hệ thống FileStorage của Bộ Tài chính.
        """
        api_urls = [
            "https://vbpq.mof.gov.vn/api/legaldoc/LegalDocs/GETAllDocument?Page=1&PageSize=15&contentType=LegalDocument",
            "https://vbpq.mof.gov.vn/api/legaldoc/LegalDocs/GETAllDocument?Page=2&PageSize=15&contentType=LegalDocument"
        ]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        }

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        collected: List[Dict[str, Any]] = []
        seen_nums = set()

        for api_url in api_urls:
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as res:
                    data = json.loads(res.read().decode('utf-8', errors='ignore'))

                documents = data.get("documents") or []
                for doc in documents:
                    doc_number = (doc.get("no") or "").strip().replace('С', 'C').replace('Р', 'P')
                    summary = (doc.get("summary") or "").strip()
                    doc_id = doc.get("id")
                    if not doc_number or not summary or doc_number in seen_nums:
                        continue

                    doc_type = (doc.get("documentTypeRecordName") or "Thông tư").strip()
                    title = f"{doc_type} số {doc_number} {summary}" if doc_number not in summary else summary

                    files = doc.get("filePathCurrent") or []
                    att_url = ""
                    if files and isinstance(files, list) and files[0].get("id"):
                        file_id = files[0].get("id")
                        clean_no = re.sub(r'[^A-Za-z0-9_\-]', '_', doc_number)
                        att_url = f"https://vbpq.mof.gov.vn/DKC.FileManagement/FileStorage/File/{file_id}?file={clean_no}.pdf"

                    detail_url = f"https://vbpq.mof.gov.vn/Detail?contentType={doc.get('contentType', 'LegalDocument')}&id={doc_id}&tab=99"

                    pub_raw = doc.get("legalPublishDate") or doc.get("publishedUtc") or ""
                    issue_date = datetime.date.today().strftime("%d/%m/%Y")
                    dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(pub_raw))
                    if dm:
                        issue_date = f"{dm.group(3)}/{dm.group(2)}/{dm.group(1)}"

                    apply_raw = doc.get("legalApplyDate") or pub_raw
                    effective_date = issue_date
                    dm_eff = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(apply_raw))
                    if dm_eff:
                        effective_date = f"{dm_eff.group(3)}/{dm_eff.group(2)}/{dm_eff.group(1)}"

                    orgs = doc.get("organizations") or []
                    issuing_body = orgs[0].get("name") if (orgs and orgs[0].get("name")) else "Bộ Tài chính"

                    editors = doc.get("editors") or []
                    editor_name = editors[0].get("name") if (editors and editors[0].get("name")) else ""

                    signers = doc.get("signers") or []
                    signer_name = signers[0].get("name") if (signers and signers[0].get("name")) else ""

                    field = self._infer_field(title, doc_number, f"{summary} {editor_name}")

                    collected.append({
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": issue_date,
                        "effective_date": effective_date,
                        "title": title,
                        "summary": f"{summary} (Chủ trì soạn thảo: {editor_name or issuing_body}).",
                        "field": field,
                        "source": "mof.gov.vn",
                        "source_name": "CSDL Văn bản Pháp quy Bộ Tài chính (vbpq.mof.gov.vn)",
                        "source_url": detail_url,
                        "attachment_url": att_url,
                        "signer_title": "Lãnh đạo Bộ Tài chính",
                        "signer_name": signer_name,
                        "content": f"{title}\n\nNgày ban hành: {issue_date} | Ngày có hiệu lực: {effective_date}.\nĐơn vị chủ trì soạn thảo: {editor_name or 'Bộ Tài chính'}.\nNgười ký: {signer_name or 'Lãnh đạo Bộ Tài chính'}."
                    })
                    seen_nums.add(doc_number)
            except Exception as e:
                print(f"[ScannerService] MOF crawl warning ({api_url}): {e}")

        return collected

    # ==================== 5. CỔNG THÔNG TIN ĐIỆN TỬ QUỐC HỘI (QUOCHOI.VN) ====================
    def crawl_live_quochoi_portal(self, keywords: Optional[List[str]] = None, timeout: int = 8) -> List[Dict[str, Any]]:
        """
        Dò quét trực tiếp từ Cổng Thông tin Điện tử Quốc hội (https://quochoi.vn/Pages/default.aspx).
        Bao gồm cả 3 chuyên mục:
        1. Văn bản Quốc hội ban hành (Luật, Nghị quyết QH)
        2. Văn bản UBTVQH ban hành (Nghị quyết UBTVQH)
        3. Dự thảo Luật đang lấy ý kiến (Luật Quản lý thuế sửa đổi, Luật Thuế TNDN, TNCN...)
        """
        url = "https://quochoi.vn/Pages/default.aspx"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        from bs4 import BeautifulSoup
        collected: List[Dict[str, Any]] = []
        seen_nums = set()
        seen_titles = set()

        try:
            req1 = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req1, context=ssl_ctx, timeout=timeout) as r1:
                html = r1.read().decode('utf-8', errors='ignore')

            m_cookie = re.search(r'document\.cookie\s*=\s*"([^"]+)"', html)
            if m_cookie and len(html) < 500:
                h_cookie = dict(headers)
                h_cookie['Cookie'] = m_cookie.group(1)
                req2 = urllib.request.Request(url, headers=h_cookie)
                with urllib.request.urlopen(req2, context=ssl_ctx, timeout=timeout) as r2:
                    html = r2.read().decode('utf-8', errors='ignore')

            soup = BeautifulSoup(html, "html.parser")
            today_str = datetime.date.today().strftime("%d/%m/%Y")

            for a in soup.find_all("a"):
                href = (a.get("href") or "").strip()
                link_text = re.sub(r'\s+', ' ', a.get_text(" ", strip=True)).strip()
                if not href or not link_text:
                    continue

                if "vietlaw.quochoi.vn/Pages/vbpq-toan-van.aspx" in href:
                    parent = a.find_parent(["div", "li", "td"])
                    gparent = parent.find_parent(["div", "li", "td"]) if parent else None
                    block_text = re.sub(r'\s+', ' ', (gparent or parent or a).get_text(" ", strip=True)).strip()

                    m_num = re.search(r'([0-9]+\s*/\s*(?:[0-9]{4}\s*/\s*)?[A-Z0-9\-]+)', link_text, re.IGNORECASE)
                    doc_number = re.sub(r'\s+', '', m_num.group(1)) if m_num else link_text

                    if doc_number in seen_nums:
                        continue

                    m_date = re.search(r'Ngày ban hành:\s*(\d{1,2}/\d{1,2}/\d{4})', block_text)
                    issue_date = m_date.group(1) if m_date else today_str

                    desc = block_text
                    idx_nbh = desc.find("Ngày ban hành:")
                    if idx_nbh != -1:
                        desc = desc[:idx_nbh].strip()
                    if desc.startswith(link_text):
                        desc_after = desc[len(link_text):].strip(" |-:")
                        if desc_after:
                            desc = desc_after

                    is_ubtvqh = "UBTVQH" in doc_number.upper() or "ỦY BAN THƯỜNG VỤ QUỐC HỘI" in desc.upper()
                    issuing_body = "Ủy ban Thường vụ Quốc hội" if is_ubtvqh else "Quốc hội"
                    doc_type = "Luật" if "luật" in link_text.lower() else "Nghị quyết"
                    field = self._infer_field(desc, doc_number)

                    collected.append({
                        "doc_number": doc_number,
                        "doc_type": doc_type,
                        "issuing_body": issuing_body,
                        "issue_date": issue_date,
                        "effective_date": issue_date,
                        "title": desc,
                        "summary": f"{desc} (Cơ quan ban hành: {issuing_body}, ngày {issue_date}).",
                        "field": field,
                        "source": "quochoi.vn",
                        "source_name": f"Cổng Thông tin Điện tử Quốc hội ({issuing_body})",
                        "source_url": href,
                        "attachment_url": "",
                        "signer_title": "Chủ tịch Quốc hội",
                        "signer_name": issuing_body,
                        "content": f"{desc}\n\nSố hiệu: {doc_number}\nCơ quan ban hành: {issuing_body}\nNgày ban hành: {issue_date}\nNguồn: Cổng Thông tin Điện tử Quốc hội (quochoi.vn)."
                    })
                    seen_nums.add(doc_number)
                    seen_titles.add(desc.lower())

                elif "duthaoonline.quochoi.vn/dt/" in href and len(link_text) > 10:
                    if link_text.lower() in seen_titles:
                        continue
                    short_hash = hashlib.md5(link_text.encode('utf-8')).hexdigest()[:4].upper()
                    doc_number = f"DT-QH16-{short_hash}"
                    if doc_number in seen_nums:
                        continue

                    title = f"Dự thảo {link_text}" if not link_text.lower().startswith("dự thảo") else link_text
                    field = self._infer_field(title, doc_number)

                    collected.append({
                        "doc_number": doc_number,
                        "doc_type": "Dự thảo Luật",
                        "issuing_body": "Quốc hội",
                        "issue_date": today_str,
                        "effective_date": today_str,
                        "title": title,
                        "summary": f"{title} - Dự thảo Luật đang trình Quốc hội và lấy ý kiến trên Cổng Thông tin Điện tử Quốc hội (quochoi.vn).",
                        "field": field,
                        "source": "quochoi.vn",
                        "source_name": "Cổng Thông tin Điện tử Quốc hội (Dự thảo Luật)",
                        "source_url": href,
                        "attachment_url": "",
                        "signer_title": "Ủy ban Kinh tế và Tài chính / Quốc hội",
                        "signer_name": "Quốc hội",
                        "content": f"{title}\n\nChuyên mục: Dự thảo Luật trên Cổng Thông tin Điện tử Quốc hội (quochoi.vn).\nLiên kết gốc: {href}"
                    })
                    seen_nums.add(doc_number)
                    seen_titles.add(link_text.lower())
        except Exception as e:
            print(f"[ScannerService] QuocHoi crawl warning: {e}")

        return collected

    def _merge_crawled_docs(self, new_docs: List[Dict[str, Any]]) -> int:
        """Gộp danh sách văn bản mới quét được vào cached_documents theo cặp (doc_number, source)"""
        if not new_docs:
            return 0
        existing_map = {
            (d.get("doc_number"), d.get("source")): d
            for d in self.cached_documents
            if d.get("doc_number")
        }
        added = 0
        for nd in reversed(new_docs):
            key = (nd.get("doc_number"), nd.get("source"))
            if key in existing_map:
                ex = existing_map[key]
                if nd.get("attachment_url") and not ex.get("attachment_url"):
                    ex["attachment_url"] = nd["attachment_url"]
                if nd.get("source_url") and "http" in nd["source_url"]:
                    ex["source_url"] = nd["source_url"]
                if nd.get("vbpl_id") and not ex.get("vbpl_id"):
                    ex["vbpl_id"] = nd["vbpl_id"]
                if nd.get("vbpl_file_name") and not ex.get("vbpl_file_name"):
                    ex["vbpl_file_name"] = nd["vbpl_file_name"]
                    ex["vbpl_files"] = nd.get("vbpl_files", [])
                if ex.get("issue_date") == "2026" and nd.get("issue_date") != "2026":
                    ex["issue_date"] = nd["issue_date"]
                    ex["effective_date"] = nd.get("effective_date", nd["issue_date"])
            else:
                self.cached_documents.insert(0, nd)
                existing_map[key] = nd
                added += 1
        return added

    def _domain_matches(self, doc_source: str, active_domain: str) -> bool:
        """Kiểm tra nguồn văn bản có khớp với nguồn website người dùng chọn hay không"""
        d1 = (doc_source or "").lower().replace("www.", "").strip()
        d2 = (active_domain or "").lower().replace("www.", "").strip()
        if not d1 or not d2:
            return False
        if d1 == d2:
            return True
        if "congbao" in d1 and "congbao" in d2:
            return True
        if "quochoi" in d1 and "quochoi" in d2:
            return True
        if "mof" in d1 and "mof" in d2:
            return True
        if "gdt" in d1 and "gdt" in d2:
            return True
        if "vbpl" in d1 and "vbpl" in d2:
            return True
        if d1.endswith("." + d2) or d2.endswith("." + d1) or (d2 in d1) or (d1 in d2):
            return True
        return False

    def _matches_user_keywords(self, doc: Dict[str, Any], keywords: List[str]) -> bool:
        """
        Kiểm tra văn bản có khớp với danh sách từ khóa người dùng nhập trên Web App hay không.
        Tuân thủ chặt chẽ danh sách từ khóa từ giao diện Web App.
        """
        doc_text = (
            f"{doc.get('title', '')} {doc.get('summary', '')} {doc.get('field', '')} "
            f"{doc.get('doc_number', '')} {doc.get('issuing_body', '')} {doc.get('content', '')}"
        ).lower()

        for kw in keywords:
            if not kw:
                continue
            if kw in doc_text:
                return True

            if kw in ("thuế", "tax"):
                if any(w in doc_text for w in [
                    "thuế", "hóa đơn", "kê khai", "tổng cục thuế", "cục thuế", "bộ tài chính",
                    "tt-btc", "qđ-btc", "vbhn-btc", "nộp thuế", "hoàn thuế", "gia hạn",
                    "quản lý thu", "lệ phí", "ngân sách", "chính sách tài khóa", "tài chính",
                    "tài sản mã hóa", "kế toán", "quyết toán", "tiêu thụ đặc biệt"
                ]):
                    return True
            elif kw in ("hộ kinh doanh", "kinh doanh cá thể"):
                if any(w in doc_text for w in [
                    "hộ kinh doanh", "cá nhân kinh doanh", "hộ cá thể", "khoán thuế",
                    "doanh nghiệp siêu nhỏ", "máy tính tiền", "bán lẻ", "ăn uống", "xăng dầu", "kinh doanh vàng"
                ]):
                    return True
            elif kw in ("thu nhập cá nhân", "tncn"):
                if any(w in doc_text for w in [
                    "thu nhập cá nhân", "tncn", "người phụ thuộc", "giảm trừ gia cảnh",
                    "tiền lương", "quyết toán thuế tncn", "vneid", "mst cá nhân", "mã số thuế cá nhân"
                ]):
                    return True
            elif kw in ("doanh nghiệp", "dn"):
                if any(w in doc_text for w in [
                    "doanh nghiệp", "đăng ký doanh nghiệp", "luật doanh nghiệp", "chi phí doanh nghiệp",
                    "doanh nghiệp fdi", "tổ chức kinh tế", "tiền thuê đất", "tiền sử dụng đất", "tiền đất",
                    "thủ tục hành chính", "kinh doanh vàng", "ngoại hối", "chứng khoán", "tài sản mã hóa",
                    "kinh tế nhà nước", "kinh tế tư nhân", "đầu tư"
                ]):
                    return True
            elif kw in ("tổ chức",):
                if any(w in doc_text for w in [
                    "tổ chức", "tổ chức chi trả", "đơn vị sự nghiệp", "hợp tác xã", "tổ chức kinh tế",
                    "ngân hàng", "tổ chức tín dụng", "quốc hội", "ủy ban thường vụ quốc hội", "ubtvqh"
                ]):
                    return True
            elif kw in ("giá trị gia tăng", "gtgt", "vat"):
                if any(w in doc_text for w in [
                    "giá trị gia tăng", "gtgt", "thuế suất 8%", "thuế suất 10%",
                    "hoàn thuế gtgt", "khấu trừ", "luật thuế giá trị gia tăng"
                ]):
                    return True
            elif kw in ("thu nhập doanh nghiệp", "tndn"):
                if any(w in doc_text for w in [
                    "thu nhập doanh nghiệp", "tndn", "chi phí được trừ", "thu nhập chịu thuế",
                    "thu nhập tính thuế", "trụ cột 2", "phúc lợi", "lãi vay", "chế độ kế toán",
                    "chế độ báo cáo", "công bố thông tin"
                ]):
                    return True
            elif kw in ("giao dịch liên kết", "gdlk"):
                if any(w in doc_text for w in [
                    "giao dịch liên kết", "gdlk", "nghị định 132", "chuyển giá",
                    "chi phí lãi vay", "hồ sơ xác định giá", "ebitda"
                ]):
                    return True
            elif kw in ("hóa đơn điện tử", "hđđt"):
                if any(w in doc_text for w in [
                    "hóa đơn điện tử", "hđđt", "nghị định 123", "thông tư 78",
                    "máy tính tiền", "mã của cơ quan thuế", "tem điện tử", "chứng từ điện tử", "nội dung hóa đơn"
                ]):
                    return True
            elif kw in ("vị trí việc làm",):
                if any(w in doc_text for w in [
                    "vị trí việc làm", "công chức", "viên chức", "tổ chức bộ máy",
                    "chức năng, nhiệm vụ", "thủ tục hành chính", "chương trình lập pháp"
                ]):
                    return True

        return False

    def scan_documents(self, fields: str, from_date_str: str = "", to_date_str: str = "", doc_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Dò quét văn bản theo danh sách lĩnh vực (từ khóa trên Web App) và khoảng thời gian.
        Chạy song song cả 5 bộ thu thập trực tuyến từ các cổng thông tin đang được bật.
        """
        keywords = [k.strip().lower() for k in re.split(r'[,;|\n]', fields) if k.strip()]
        if not keywords:
            keywords = [
                "thuế", "hộ kinh doanh", "thu nhập cá nhân", "doanh nghiệp",
                "tổ chức", "giá trị gia tăng", "thu nhập doanh nghiệp",
                "giao dịch liên kết", "hóa đơn điện tử"
            ]

        sources = ConfigManager.get_sources()
        active_domains_norm = [s.get("domain", "").lower().replace("www.", "").strip() for s in sources if s.get("enabled", True)]

        now = datetime.datetime.now()
        keywords_changed = (keywords != self.last_crawl_keywords)
        if not self.last_crawl_time or (now - self.last_crawl_time).total_seconds() > 180 or keywords_changed:
            tasks = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                if any("congbao" in d for d in active_domains_norm):
                    tasks.append(executor.submit(self.crawl_live_congbao_portal, 6))
                if any("gdt" in d for d in active_domains_norm):
                    tasks.append(executor.submit(self.crawl_live_gdt_portal, 6))
                if any("vbpl" in d for d in active_domains_norm):
                    tasks.append(executor.submit(self.crawl_live_vbpl_portal, keywords, 8))
                if any("mof" in d for d in active_domains_norm):
                    tasks.append(executor.submit(self.crawl_live_mof_portal, keywords, 12))
                if any("quochoi" in d for d in active_domains_norm):
                    tasks.append(executor.submit(self.crawl_live_quochoi_portal, keywords, 8))

                total_added = 0
                for fut in tasks:
                    try:
                        docs_batch = fut.result()
                        total_added += self._merge_crawled_docs(docs_batch)
                    except Exception as e:
                        print(f"[ScannerService] Concurrent crawl error: {e}")

                if total_added > 0:
                    self._save_catalog()

            self.last_crawl_time = now
            self.last_crawl_keywords = list(keywords)

        self.cached_documents = self._load_initial_catalog()

        results: List[Dict[str, Any]] = []

        from_date = self._parse_date(from_date_str)
        to_date = self._parse_date(to_date_str)

        today = datetime.date.today()
        if not to_date:
            to_date = today
        if not from_date:
            from_date = datetime.date(today.year, 1, 1)

        seen_keys = set()
        for doc in self.cached_documents:
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

            doc_date = self._parse_date(doc.get("issue_date", ""))
            if not doc_date:
                continue

            if not (from_date <= doc_date <= to_date):
                continue

            if doc_types and doc.get("doc_type") not in doc_types:
                continue

            if self._matches_user_keywords(doc, keywords):
                dedup_key = f"{doc.get('doc_number', '')}_{doc.get('source', '')}"
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    results.append(doc.copy())

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
