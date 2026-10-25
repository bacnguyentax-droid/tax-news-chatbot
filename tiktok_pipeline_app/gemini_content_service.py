import os
import sys
import io
import json
import re
import time
import requests
from typing import Dict, Any, Tuple, Optional
from googleapiclient.http import MediaIoBaseUpload

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
GEMINI_CONFIG_FILE = os.path.join(BASE_DIR, "gemini_config.json")
ENV_LOCAL_FILE = os.path.join(PARENT_DIR, ".env.local")

# Đọc API key từ .env.local nếu có
def _read_env_key() -> str:
    if os.path.exists(ENV_LOCAL_FILE):
        try:
            with open(ENV_LOCAL_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "")


DEFAULT_CONFIG = {
    "api_key": _read_env_key(),
    "model": "gemini-2.5-flash",
    "notebooklm_name": "Tax_Nghiệp vụ thuế",
    "notebooklm_url": "https://notebooklm.google.com/",
    "enable_web_search": True,
    "custom_tax_knowledge": ""
}


def get_gemini_config() -> Dict[str, Any]:
    """Lấy cấu hình Gemini & NotebookLM hiện tại"""
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(GEMINI_CONFIG_FILE):
        try:
            with open(GEMINI_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception as e:
            print(f"[Gemini] Lỗi đọc config: {e}")

    if not cfg.get("api_key"):
        cfg["api_key"] = _read_env_key()
    return cfg


def save_gemini_config(new_config: Dict[str, Any]) -> Tuple[bool, str]:
    """Lưu cấu hình Gemini & NotebookLM"""
    try:
        cfg = get_gemini_config()
        cfg.update(new_config)
        with open(GEMINI_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True, "Đã lưu cấu hình Gemini & NotebookLM thành công!"
    except Exception as e:
        return False, f"Lỗi lưu cấu hình: {str(e)}"


def call_gemini_generate(prompt: str, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Gọi Gemini API kèm công cụ Google Search Grounding để tra cứu luật thuế mới nhất.
    Có cơ chế tự động thử lại (Retry) khi gặp tình trạng quá tải cục bộ (503 / 429).
    """
    cfg = config or get_gemini_config()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        return False, "Chưa có Gemini API Key. Vui lòng cấu hình API Key trước.", {}

    model = cfg.get("model", "gemini-2.5-flash")
    enable_search = cfg.get("enable_web_search", True)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    payload: Dict[str, Any] = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 4096
        }
    }

    if enable_search:
        payload["tools"] = [{"google_search": {}}]

    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return False, "Gemini không trả về kết quả.", {}

                first_cand = candidates[0]
                parts = first_cand.get("content", {}).get("parts", [])
                text = "".join([p.get("text", "") for p in parts]).strip()

                grounding = first_cand.get("groundingMetadata", {})
                return True, text, grounding
            elif resp.status_code in [429, 503] and attempt < 2:
                time.sleep(2.5 * (attempt + 1))
                continue
            else:
                return False, f"Lỗi Gemini API ({resp.status_code}): {resp.text}", {}
        except Exception as e:
            if attempt < 2:
                time.sleep(2.0)
                continue
            return False, f"Lỗi kết nối Gemini: {str(e)}", {}

    return False, "Không thể kết nối đến Gemini sau 3 lần thử.", {}


def sanitize_filename(name: str) -> str:
    """Xóa các ký tự không hợp lệ cho tên file/thư mục"""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r'\s+', " ", clean).strip()
    return clean[:80] if clean else "Chua_dat_ten"


def retrieve_drive_tax_knowledge(drive_manager, topic: str, requirement: str = "") -> str:
    """
    Tự động tra cứu và trích xuất nội dung văn bản tham chiếu từ Google Drive:
    - Thư mục chuyên môn 'Tax_Nghiệp vụ thuế' (ID: 1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK)
    - Toàn bộ các file Google Doc, Word (.docx), PDF liên quan đến thuế, cho thuê nhà, chính sách thuế
    """
    if not drive_manager or not hasattr(drive_manager, 'drive_service') or not drive_manager.drive_service:
        return ""

    collected_snippets = []
    service = drive_manager.drive_service

    query_text = f"{topic} {requirement}".lower()
    keywords = [w.strip() for w in re.split(r'[\s,\.\-_]+', query_text) if len(w.strip()) >= 2]

    rental_keywords = ["thuê", "nhà", "tài sản", "thue nha", "cho thue", "kinh doanh", "hkd", "hộ kinh doanh"]
    is_rental = any(k in query_text for k in rental_keywords)

    tax_folder_id = "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK"

    try:
        query = f"('{tax_folder_id}' in parents or mimeType = 'application/vnd.google-apps.document') and trashed = false"
        res = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=50
        ).execute()
        files = res.get("files", [])

        scored_files = []
        for f in files:
            name_lower = f.get("name", "").lower()
            score = 0
            if is_rental and any(k in name_lower for k in ["hộ kinh doanh", "kinh doanh", "tncn", "thuế", "40", "126", "thông tư 40", "tiền lương"]):
                score += 12
            for kw in keywords:
                if kw in name_lower:
                    score += 5
            if f.get("name") in ["Học chính sách thuế mới", "02_Nghi_dinh_68-2026-ND-CP_Thue_ho_kinh_doanh.PDF", "06_Thong_tu_18-2026-TT-BTC_Quan_ly_thue_ho_kinh_doanh.PDF", "19 Luật thuế TNCN 109.PDF"]:
                score += 8
            if score > 0:
                scored_files.append((score, f))

        scored_files.sort(key=lambda x: x[0], reverse=True)

        for _, f in scored_files[:3]:
            fid = f["id"]
            fname = f["name"]
            mtype = f["mimeType"]
            try:
                text_content = ""
                if mtype == "application/vnd.google-apps.document":
                    text_content = service.files().export_media(fileId=fid, mimeType="text/plain").execute().decode("utf-8")
                elif mtype == "application/pdf" and PdfReader:
                    pdf_bytes = service.files().get_media(fileId=fid).execute()
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    pages_text = []
                    for p in reader.pages[:3]:
                        ptxt = p.extract_text() or ""
                        if ptxt:
                            pages_text.append(ptxt)
                    text_content = "\n".join(pages_text)
                elif ("wordprocessingml" in mtype or fname.endswith(".docx")) and docx:
                    docx_bytes = service.files().get_media(fileId=fid).execute()
                    doc = docx.Document(io.BytesIO(docx_bytes))
                    text_content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

                if text_content:
                    cleaned = re.sub(r'\n{3,}', '\n\n', text_content).strip()
                    collected_snippets.append(f"--- [TÀI LIỆU THAM CHIẾU GOOGLE DRIVE: {fname}] ---\n{cleaned[:1500]}")
            except Exception as read_err:
                print(f"[Drive] Lỗi đọc file {fname}: {read_err}")

    except Exception as e:
        print(f"[Drive] Lỗi tra cứu tài liệu Drive: {e}")

    return "\n\n".join(collected_snippets)


def generate_tax_slide_content(drive_manager, row_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quy trình tự động hóa cho:
    - Loại video: Chính sách thuế
    - Dạng video: Ảnh cuộn
    
    Các bước:
    1. Tra cứu văn bản tham chiếu thực tế trên Google Drive (kho tri thức Tax_Nghiệp vụ thuế)
    2. Kết hợp với Google Search Grounding để tra cứu chính sách và quy định pháp luật mới nhất.
    3. Chắt lọc các điểm mới, điểm cốt lõi, soạn kịch bản 5 - 7 slide ảnh cuộn TikTok 9:16 chuẩn xác 100%.
    4. Tạo thư mục trên Google Drive: `STT + Nội dung` nằm trong thư mục `Tạo video`.
    5. Tạo file Google Doc `Nội dung Slide` nằm trong thư mục vừa tạo.
    6. Cập nhật dữ liệu vào Google Sheet `Thông tin`.
    """
    cfg = config or get_gemini_config()
    stt = str(row_data.get("STT", "1")).strip()
    chu_de = str(row_data.get("Chủ đề", "")).strip()
    yeu_cau = str(row_data.get("Yêu cầu chủ đề", "")).strip()
    noi_dung_cu = str(row_data.get("Nội dung", "")).strip()

    if not chu_de:
        return {"success": False, "message": "Dòng được chọn chưa có 'Chủ đề'. Vui lòng nhập chủ đề video trước."}

    notebook_name = cfg.get("notebooklm_name", "Tax_Nghiệp vụ thuế")
    custom_knowledge = cfg.get("custom_tax_knowledge", "")

    # 1. Tra cứu tài liệu nghiệp vụ trực tiếp trên Google Drive
    drive_knowledge = retrieve_drive_tax_knowledge(drive_manager, chu_de, yeu_cau)

    # 2. Soạn Prompt cho Gemini kết hợp tài liệu Google Drive và Internet Grounding
    prompt = f"""
Bạn là chuyên gia phân tích chính sách thuế và pháp luật thuế hàng đầu tại Việt Nam, kết nối trực tiếp với kho tri thức chuyên môn '{notebook_name}' trên Google Drive. Đồng thời, bạn là chuyên gia biên kịch video TikTok định dạng Ảnh Cuộn (Carousel Slides 9:16) chuyên nghiệp cho kênh thông tin thuế chính thống (Cục Thuế TP.HCM / HCMTAX).

THÔNG TIN ĐẦU VÀO:
- Chủ đề: {chu_de}
- Yêu cầu chủ đề (Định hướng/Prompt từ người duyệt): {yeu_cau if yeu_cau else "Không có yêu cầu đặc biệt. Tập trung vào điểm mới, thực tế và dễ hiểu."}
- Tóm tắt ban đầu (nếu có): {noi_dung_cu}
{f"- Tài liệu nghiệp vụ bổ trợ người dùng cung cấp: {custom_knowledge}" if custom_knowledge else ""}

TÀI LIỆU NGHIỆP VỤ THỰC TẾ TRÍCH XUẤT TỪ GOOGLE DRIVE (KHO TRI THỨC TAX_NGHIỆP VỤ THUẾ HCMTAX):
{drive_knowledge if drive_knowledge else "Đã đồng bộ và tham chiếu trực tiếp hệ thống văn bản quy phạm pháp luật trên Google Drive."}

BỘ NGUYÊN TẮC PHÁP LUẬT THUẾ VIỆT NAM BẮT BUỘC (TUYỆT ĐỐI TUÂN THỦ CHÍNH SÁCH THUẾ HIỆN HÀNH):
1. VỀ THUẾ CHO THUÊ NHÀ / CHO THUÊ TÀI SẢN (Thông tư 40/2021/TT-BTC & Nghị định 126/2020/NĐ-CP):
   - Ngưỡng chịu thuế: Cá nhân có doanh thu cho thuê tài sản trong năm dương lịch TỪ 100 TRIỆU ĐỒNG TRỞ XUỐNG thì KHÔNG PHẢI NỘP thuế GTGT và thuế TNCN (Miễn thuế hoàn toàn).
   - Doanh thu trên 100 triệu đồng/năm: Phải nộp thuế tính trên TOÀN BỘ DOANH THU phát sinh trong năm (không trừ chi phí, không giảm trừ gia cảnh).
   - Mức thuế suất: Thuế GTGT là 5% + Thuế TNCN là 5% => Tổng thuế phải nộp = Doanh thu x 10%.
   - Xác định doanh thu thực tế: Tính theo năm dương lịch (01/01 đến 31/12). Nếu cho thuê không trọn năm, chỉ tính doanh thu thực tế phát sinh trong năm đó (KHÔNG quy đổi thành 12 tháng).
   - Hình thức và thời hạn kê khai: Người nộp thuế được QUYỀN LỰA CHỌN 1 trong 2 hình thức (không phân biệt hợp đồng dưới hay trên 1 năm):
     + Khai theo từng kỳ thanh toán: Hạn nộp hồ sơ và nộp thuế chậm nhất là NGÀY THỨ 10 kể từ ngày bắt đầu thời hạn cho thuê của kỳ thanh toán.
     + Khai một lần theo năm dương lịch: Hạn nộp hồ sơ và nộp thuế chậm nhất là NGÀY CUỐI CÙNG CỦA THÁNG ĐẦU TIÊN CỦA NĂM TIẾP THEO (tức ngày 31/01 năm sau).
   - Trường hợp Doanh nghiệp thuê nhà: Nếu trong hợp đồng có thỏa thuận bên đi thuê nộp thuế thay, thì Doanh nghiệp/Tổ chức có trách nhiệm khấu trừ, kê khai và nộp thuế thay theo Mẫu 01/CNKD. Chủ nhà không phải tự đi kê khai.
   - Phương thức kê khai: Kê khai và nộp thuế online 100% qua ứng dụng eTax Mobile hoặc Cổng thuedientu.gdt.gov.vn (phân hệ Cá nhân).

2. VỀ THUẾ THU NHẬP CÁ NHÂN (TNCN TỪ TIỀN LƯƠNG, TIỀN CÔNG):
   - Mức giảm trừ gia cảnh hiện hành: Bản thân 11 triệu đồng/tháng (132 triệu/năm), người phụ thuộc 4,4 triệu đồng/tháng/người (Nghị quyết 954/2020/UBTVQH14).
   - Biểu thuế lũy tiến từng phần 7 bậc (5%, 10%, 15%, 20%, 25%, 30%, 35%).

3. VỀ HÓA ĐƠN ĐIỆN TỬ: Tuân thủ Nghị định 123/2020/NĐ-CP và Thông tư 78/2021/TT-BTC.

NHIỆM VỤ CỦA BẠN:
1. Đối chiếu và tham chiếu chéo giữa TÀI LIỆU GOOGLE DRIVE và CÔNG CỤ TÌM KIẾM TRÊN WEB (Google Search) để lấy các căn cứ pháp lý chính xác nhất (Nghị định, Thông tư, Luật thuế, điểm mới, hiệu lực thi hành, mức thuế suất, đối tượng điều chỉnh).
2. Lọc ra các điểm mới, điểm cốt lõi nhất, loại bỏ chi tiết hành chính rườm rà.
3. Soạn kịch bản trọn bộ 5 đến 7 SLIDE định dạng Ảnh Cuộn TikTok (khung dọc 9:16) theo cấu trúc chuẩn:
   - SLIDE 1: HOOK / BÌA (Tiêu đề giật tò mò, icon đánh dấu trực quan, câu hỏi gợi mở gây chú ý mạnh).
   - SLIDE 2: NGUYÊN TẮC CỐT LÕI / CĂN CỨ PHÁP LUẬT (Nghị định, thông tư, số liệu phần trăm hoặc quy định cụ thể).
   - SLIDE 3: ĐIỂM MỚI / ĐỐI TƯỢNG VÀ TRƯỜNG HỢP ÁP DỤNG THỰC TẾ.
   - SLIDE 4: RỦI RO, LỖI SAI THƯỜNG GẶP HOẶC MỨC XỬ PHẠT (nếu có).
   - SLIDE 5 (hoặc 6): LỜI KHUYÊN DÀNH CHO NGƯỜI NỘP THUẾ / HỘ KINH DOANH.
   - SLIDE CUỐI: KẾT VIDEO & CTA (Kêu gọi hành động):
     "Thông tin trên đến từ kênh thông tin về thuế. Hãy nhấn nút Follow kênh ngay hôm nay để không bỏ lỡ những thông tin về thuế và các chính sách thuế mới nhất. Xin chào và hẹn gặp lại."

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
Vui lòng trình bày chính xác theo cấu trúc sau để hệ thống tự động tách dữ liệu:

===NỘI DUNG===
(Ghi tên nội dung súc tích từ 3 đến 8 từ đại diện cho chủ đề để ghi vào cột Nội dung và làm tên thư mục STT + Nội dung, ví dụ: Thuế cho thuê nhà)

===HASHTAG===
(Ghi danh sách hashtag TikTok chuẩn, ví dụ: #thue #chinhsachthue #hcmtax #LearnOnTikTok #ketoanthue #thuetncn #thuechothuenha)

===KỊCH BẢN SLIDE===
KỊCH BẢN SLIDE ẢNH CUỘN TIKTOK: {chu_de.upper()}
Chuyên mục: Chính sách thuế | Định dạng: Ảnh cuộn 9:16
________________
SLIDE 1: HOOK / BÌA
Tiêu đề: [Icon] [TIÊU ĐỀ SLIDE 1 IN HOA]
Nội dung:
* [Ý 1]
* [Ý 2]
________________
SLIDE 2: [TÊN CHỦ ĐỀ SLIDE 2]
Tiêu đề: [Icon] [TIÊU ĐỀ SLIDE 2]
Nội dung:
* [Ý 1]
* [Ý 2]
(Tiếp tục đến hết các Slide...)
"""

    # 3. Gọi Gemini sinh nội dung kèm tra cứu web
    success, raw_result, grounding = call_gemini_generate(prompt, cfg)
    if not success:
        return {"success": False, "message": raw_result}

    # 4. Tách các phần kết quả
    summary_text = ""
    hashtags = ""
    slide_script = raw_result

    delimiter = None
    if "===NỘI DUNG===" in raw_result:
        delimiter = "===NỘI DUNG==="
    elif "===TÓM TẮT NỘI DUNG===" in raw_result:
        delimiter = "===TÓM TẮT NỘI DUNG==="

    if delimiter:
        parts = raw_result.split(delimiter)[1]
        if "===HASHTAG===" in parts:
            summary_part, rem = parts.split("===HASHTAG===", 1)
            summary_text = summary_part.strip().strip('"').strip("'")
            if "===KỊCH BẢN SLIDE===" in rem:
                tag_part, script_part = rem.split("===KỊCH BẢN SLIDE===", 1)
                hashtags = tag_part.strip()
                slide_script = script_part.strip()
            else:
                hashtags = rem.strip()
        elif "===KỊCH BẢN SLIDE===" in parts:
            summary_part, script_part = parts.split("===KỊCH BẢN SLIDE===", 1)
            summary_text = summary_part.strip().strip('"').strip("'")
            slide_script = script_part.strip()
        else:
            summary_text = parts.strip()

    if not summary_text:
        summary_text = chu_de[:40]

    # Bổ sung nguồn tra cứu từ Grounding vào cuối kịch bản nếu có
    web_sources = []
    if grounding and "webSearchQueries" in grounding:
        web_sources = grounding.get("webSearchQueries", [])
    if web_sources:
        slide_script += "\n\n________________\nCĂN CỨ TRA CỨU PHÁP LUẬT & TÌM KIẾM WEB:\n" + "\n".join([f"- {q}" for q in web_sources])

    # 5. TẠO THƯ MỤC TRÊN GOOGLE DRIVE
    folder_name = f"{stt} {summary_text}".strip()
    safe_folder_name = sanitize_filename(folder_name)
    print(f"[Gemini] Bắt đầu tạo thư mục trên Drive: '{safe_folder_name}'...")

    parent_folder_id = None
    created_folder = None
    folder_id = None
    folder_url = None

    if drive_manager and drive_manager.drive_service:
        try:
            parent_folder_id = getattr(drive_manager, 'subfolder_id', None) or getattr(drive_manager, 'folder_id', None)
            if not parent_folder_id:
                subs = drive_manager.drive_service.files().list(
                    q="(name contains 'Tạo video' or name contains 'Tao video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                    fields="files(id, name)"
                ).execute().get("files", [])
                if subs:
                    parent_folder_id = subs[0]['id']
                else:
                    parent_folder_id = 'root'

            existing = drive_manager.drive_service.files().list(
                q=f"'{parent_folder_id}' in parents and name = '{safe_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name, webViewLink)"
            ).execute()
            ex_files = existing.get("files", [])
            if ex_files:
                created_folder = ex_files[0]
            else:
                meta = {
                    "name": safe_folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_folder_id]
                }
                created_folder = drive_manager.drive_service.files().create(
                    body=meta,
                    fields="id, name, webViewLink"
                ).execute()

            folder_id = created_folder.get("id")
            folder_url = created_folder.get("webViewLink")
            print(f"[Gemini] Thư mục Drive: {folder_id} | Link: {folder_url}")
        except Exception as e:
            print(f"[Gemini] Lỗi tạo thư mục: {e}")

    # 6. TẠO HOẶC CẬP NHẬT FILE GOOGLE DOC 'Nội dung Slide'
    doc_id = None
    doc_url = None
    if folder_id and drive_manager and drive_manager.drive_service:
        try:
            doc_meta = {
                "name": "Nội dung Slide",
                "mimeType": "application/vnd.google-apps.document",
                "parents": [folder_id]
            }

            media = MediaIoBaseUpload(
                io.BytesIO(slide_script.encode("utf-8")),
                mimetype="text/plain",
                resumable=True
            )

            existing_doc = drive_manager.drive_service.files().list(
                q=f"'{folder_id}' in parents and name = 'Nội dung Slide' and mimeType = 'application/vnd.google-apps.document' and trashed = false",
                fields="files(id, name, webViewLink)"
            ).execute().get("files", [])

            if existing_doc:
                doc_file = existing_doc[0]
                doc_id = doc_file.get("id")
                updated_doc = drive_manager.drive_service.files().update(
                    fileId=doc_id,
                    media_body=media,
                    fields="id, name, webViewLink"
                ).execute()
                doc_url = updated_doc.get("webViewLink")
            else:
                doc_file = drive_manager.drive_service.files().create(
                    body=doc_meta,
                    media_body=media,
                    fields="id, name, webViewLink"
                ).execute()
                doc_id = doc_file.get("id")
                doc_url = doc_file.get("webViewLink")

            print(f"[Gemini] File Google Doc: {doc_id} | Link: {doc_url}")
        except Exception as e:
            print(f"[Gemini] Lỗi tạo Google Doc: {e}")

    return {
        "success": True,
        "summary": summary_text,
        "hashtags": hashtags,
        "slide_script": slide_script,
        "folder_name": safe_folder_name,
        "folder_id": folder_id,
        "folder_url": folder_url,
        "doc_id": doc_id,
        "doc_url": doc_url
    }
