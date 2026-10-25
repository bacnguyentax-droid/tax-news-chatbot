# -*- coding: utf-8 -*-

"""

Dịch vụ Thư Ký AI Tin Tức (AI News Secretary Service)

- Quản lý các Thư ký AI thu thập tin tức thời gian thực trên Internet qua Gemini.

- Danh sách 10 nhân vật đại diện lấy từ truyện cổ tích Việt Nam.

- Thiết lập giờ thực hiện nhiệm vụ trong ngày và chạy tự động định kỳ.

- Nút 'Yêu cầu báo cáo' thực hiện thu thập và xuất báo cáo tức thời.

- Xuất file Word (.docx) lưu trữ tại:

  1. manage_app/Thư ký tin tức

  2. ____Manage App____/Thư ký tin tức

- Định dạng tên file: (tên thư ký + ngày giờ tạo).docx

- Hỗ trợ xem trực tiếp báo cáo trên Web và tải file Word về máy.

"""



import os

import sys

import io

import re

import json

import time

import shutil

import datetime

import threading

from typing import Dict, Any, List, Optional, Tuple



CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:

    sys.path.insert(0, CURRENT_DIR)



ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))



# Thư mục lưu trữ file Word theo yêu cầu người dùng

REPORTS_DIR = os.path.join(CURRENT_DIR, "Thư ký tin tức")

ALT_REPORTS_DIR = os.path.join(ROOT_DIR, "____Manage App____", "Thư ký tin tức")



for d in [REPORTS_DIR, ALT_REPORTS_DIR]:

    try:

        os.makedirs(d, exist_ok=True)

    except Exception as ex:

        print(f"[SecretaryService] Không thể tạo thư mục {d}: {ex}")



from config_manager import ConfigManager

from assistant_service import AssistantService

from drive_service import drive_service

from chief_secretary_service import ChiefSecretaryService



# Thư mục Google Drive: Drive của tôi > ____Manage App____ > Thư ký Tin tức

DRIVE_NEWS_FOLDER_ID = "1XLygH0FnnwF0XsgUSHfNlrDkcf-yqxwp" 



# Thư viện tạo file Word .docx

try:

    import docx

    from docx.shared import Inches, Pt, RGBColor

    from docx.enum.text import WD_ALIGN_PARAGRAPH

    from docx.enum.table import WD_TABLE_ALIGNMENT

    from docx.oxml import parse_xml, OxmlElement

    from docx.oxml.ns import nsdecls, qn

    DOCX_AVAILABLE = True

except ImportError:

    DOCX_AVAILABLE = False





# Danh sách 10 nhân vật truyện cổ tích Việt Nam

VIETNAMESE_FAIRY_TALE_CHARACTERS = [

    {

        "id": "thach_sanh",

        "name": "Thạch Sanh",

        "title": "Dũng sĩ Thạch Sanh",

        "description": "Chân thật, dũng cảm, diệt chằn tinh, bắn đại bàng, tiếng đàn nhân nghĩa cảm hóa quân thù.",

        "avatar": "🏹",

        "color": 0x854d0e,

        "default_role": "Thư ký Tổng hợp Tin tức & Cảnh báo Rủi ro Pháp lý",

        "default_appearance": "Dũng sĩ vạm vỡ, áo nâu thắt đai vàng, đeo rìu chiến dũng mãnh sau lưng, mắt sáng kiên nghị"

    },

    {

        "id": "thanh_giong",

        "name": "Thánh Gióng",

        "title": "Phù Đổng Thiên Vương",

        "description": "Ý chí kiên cường, sức mạnh phi thường, nhổ tre đuổi giặc, tượng trưng cho sức bật thời đại.",

        "avatar": "🐎",

        "color": 0xdc2626,

        "default_role": "Thư ký Tin tức Đột phá Công nghệ & Chuyển đổi số",

        "default_appearance": "Tráng sĩ uy phong, giáp đỏ rực rỡ, búi tóc cao dũng mãnh, mang bụi tre ngà vàng sau lưng"

    },

    {

        "id": "mai_an_tiem",

        "name": "Mai An Tiêm",

        "title": "Mai An Tiêm",

        "description": "Ý chí tự lực cánh sinh, khai hoang đảo cát, gieo mầm dưa hấu, biểu tượng khởi nghiệp kiến quốc.",

        "avatar": "🍉",

        "color": 0x059669,

        "default_role": "Thư ký Tin tức Kinh tế Nông nghiệp, Ngoại thương & Khởi nghiệp",

        "default_appearance": "Tự lực cánh sinh kiên định, áo xanh lục tươi sáng, đầu đội quả dưa hấu sọc đỏ xanh tươi mát"

    },

    {

        "id": "chu_dong_tu",

        "name": "Chử Đồng Tử",

        "title": "Chử Đồng Tử",

        "description": "Hiếu nghĩa, nhân ái, kết duyên Tiên Dung, khai mở bến sông giao thương, ông tổ ngành thương mại.",

        "avatar": "🛶",

        "color": 0xca8a04,

        "default_role": "Thư ký Tin tức Thương mại Điện tử, Logistics & Thị trường",

        "default_appearance": "Áo vàng óng màu phù sa sông, nụ cười đôn hậu, tay cầm gậy thần và nón kỳ diệu, túi gấm thương mại"

    },

    {

        "id": "co_tam",

        "name": "Cô Tấm",

        "title": "Cô Tấm dịu hiền",

        "description": "Cần cù, hiền hậu, kiên trì vượt gian nan, hóa thân vàng anh, xoan đào, quả thị ngát hương.",

        "avatar": "🌸",

        "color": 0xec4899,

        "default_role": "Thư ký Tin tức Chính sách An sinh Xã hội, Lao động & Thuế TNCN",

        "default_appearance": "Nữ thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao"

    },

    {

        "id": "cam",

        "name": "Cám",

        "title": "Cám",

        "description": "Nhanh nhẹn, sắc sảo, thích khám phá, am hiểu sự đời và xu hướng thời cuộc mới.",

        "avatar": "🪞",

        "color": 0x9333ea,

        "default_role": "Thư ký Điểm tin Nhanh, Xu hướng Mạng xã hội & Truyền thông",

        "default_appearance": "Nhanh nhẹn sắc sảo, áo yếm tím hoa cà, tóc đuôi ngựa thắt nơ đỏ thời trang"

    },

    {

        "id": "son_tinh",

        "name": "Sơn Tinh",

        "title": "Sơn Tinh (Tản Viên)",

        "description": "Chúa sơn lâm đại ngàn, dời non lấp biển, ngăn lũ bảo vệ mùa màng, biểu tượng vững chãi.",

        "avatar": "⛰️",

        "color": 0x15803d,

        "default_role": "Thư ký Tin tức Quy hoạch Đất đai, Môi trường & Bất động sản",

        "default_appearance": "Chúa non cao uy nghi, áo xanh rừng thẳm, vương miện thần núi, vóc dáng rắn rỏi vững chãi"

    },

    {

        "id": "thuy_tinh",

        "name": "Thủy Tinh",

        "title": "Thủy Tinh",

        "description": "Chúa tể biển khơi mênh mông, hô mưa gọi gió, quyết liệt, am tường dòng chảy kinh tế biển.",

        "avatar": "🌊",

        "color": 0x1d4ed8,

        "default_role": "Thư ký Tin tức Vận tải Biển, Hải quan & Xuất nhập khẩu",

        "default_appearance": "Chúa tể biển khơi quyết đoán, áo choàng xanh dương sóng nước đại dương, vương miện thần biển"

    },

    {

        "id": "an_duong_vuong",

        "name": "An Dương Vương",

        "title": "An Dương Vương (Thục Phán)",

        "description": "Xây thành Cổ Loa kiên cố, chế tạo nỏ thần giữ gìn non sông, phong thái quân vương quyết đoán.",

        "avatar": "👑",

        "color": 0x991b1b,

        "default_role": "Thư ký Tin tức Quản trị Doanh nghiệp, Chính sách Vĩ mô & Đầu tư",

        "default_appearance": "Phong thái đế vương, hoàng bào đỏ thêu chỉ vàng, đầu đội mão vương miện, nỏ thần sau lưng"

    },

    {

        "id": "chu_cuoi",

        "name": "Chú Cuội",

        "title": "Chú Cuội",

        "description": "Thông minh, dí dỏm, ngồi gốc cây đa cung trăng nhìn ngắm nhân gian, giàu góc nhìn độc đáo.",

        "avatar": "🌙",

        "color": 0xa16207,

        "default_role": "Thư ký Bình luận Tin tức, Góc nhìn Chuyên gia & Phân tích Đa chiều",

        "default_appearance": "Thông minh hóm hỉnh, áo gấm nâu trầm dân dã, đội nón lá tre, tay cầm cành đa xanh, tóc búi củ tỏi ngộ nghĩnh"

    }

]





def sanitize_filename(name: str) -> str:

    """Loại bỏ ký tự không hợp lệ trong tên tệp trên Windows"""

    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()





def add_hyperlink(paragraph, url: str, text: str, color="0284C7", underline=True):

    """Thêm liên kết siêu văn bản thật (clickable hyperlink) vào file Word .docx để mở được trên Google Docs/Drive"""

    if not url or not text:

        return

    part = paragraph.part

    try:

        r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

        u_val = "single" if underline else "none"

        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        hyperlink_xml = f'<w:hyperlink {nsdecls("w")} {nsdecls("r")} r:id="{r_id}"><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:color w:val="{color}"/><w:u w:val="{u_val}"/></w:rPr><w:t xml:space="preserve">{safe_text}</w:t></w:r></w:hyperlink>'

        hyperlink = parse_xml(hyperlink_xml)

        paragraph._p.append(hyperlink)

    except Exception as e:

        r = paragraph.add_run(text)

        r.font.name = "Times New Roman"

        r.font.color.rgb = RGBColor(2, 132, 199)

        r.underline = True



def _add_styled_chunk(paragraph, chunk: str, font_size=11, default_bold=False, default_italic=False, text_color=None):

    """Xử lý bold **...** và italic *...* trong chunk văn bản"""

    parts = re.split(r'(\*\*[^*]+\*\*)', chunk)

    for p in parts:

        if not p:

            continue

        if p.startswith('**') and p.endswith('**'):

            b_text = p[2:-2]

            run = paragraph.add_run(b_text)

            run.bold = True

            run.font.name = "Times New Roman"

            run.font.size = Pt(font_size)

            if text_color:

                run.font.color.rgb = text_color

        else:

            run = paragraph.add_run(p)

            run.bold = default_bold

            run.italic = default_italic

            run.font.name = "Times New Roman"

            run.font.size = Pt(font_size)

            if text_color:

                run.font.color.rgb = text_color



def add_line_with_hyperlinks(paragraph, line_text: str, default_font_size=11, is_bold=False, is_italic=False, text_color=None):

    """Phân tích các URL trong văn bản và biến chúng thành Hyperlink thật trong file Word"""

    pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)|(?<=\()?(https?://[^\s\)]+)(?=\))?|`((?:https?://)[^\s`]+)`')

    pos = 0

    for match in pattern.finditer(line_text):

        start, end = match.span()

        if start > pos:

            chunk = line_text[pos:start]

            _add_styled_chunk(paragraph, chunk, default_font_size, is_bold, is_italic, text_color)

        

        if match.group(1) and match.group(2):

            link_text = match.group(1)

            link_url = match.group(2)

        elif match.group(4):

            link_text = match.group(4)

            link_url = match.group(4)

        else:

            raw_url = match.group(3) or match.group(0)

            clean_url = raw_url.strip("()[]`'\",")

            link_text = clean_url

            link_url = clean_url

            

        add_hyperlink(paragraph, link_url, link_text, color="0284C7", underline=True)

        pos = end

        

    if pos < len(line_text):

        chunk = line_text[pos:]

        _add_styled_chunk(paragraph, chunk, default_font_size, is_bold, is_italic, text_color)



def generate_smart_search_queries(role: str, instruction: str, time_range: str = "1_week") -> List[str]:
    """Tạo ra 2-3 câu truy vấn tìm kiếm Internet tối ưu và sắc bén nhất cho từng thư ký theo đúng vai trò và nội dung huấn luyện"""
    role_lower = role.lower()
    inst_lower = instruction.lower()

    queries = []

    # 1. Nếu là Thư ký Thuế / Chính sách thuế / Hóa đơn / Quản lý thuế
    if any(k in role_lower for k in ["thuế", "hóa đơn", "kê khai", "chính sách thuế", "tổng cục thuế"]):
        queries.append("tin tức chính sách thuế mới nhất cá nhân hộ kinh doanh doanh nghiệp")
        queries.append("văn bản chính sách thuế mới ban hành tổng cục thuế bộ tài chính")
        queries.append("chính sách thuế mới nhất báo chính phủ")

    # 2. Nếu là Thư ký AI / Công nghệ thế giới (Phân tích công nghệ & AI)
    # Lưu ý: Tuyệt đối dùng regex word boundary để tránh trùng chữ 'ai' trong tiếng Việt ('phân loại', 'tại', 'phải')
    elif any(k in role_lower for k in ["công nghệ", "trí tuệ nhân tạo"]) or re.search(r'\bai\b', role_lower):
        queries.append("OpenAI Anthropic Google DeepMind AI latest news breakthroughs")
        queries.append("TechCrunch The Verge MIT Technology Review AI product updates")
        queries.append("tin tức trí tuệ nhân tạo thế giới công nghệ AI mới nhất")

    # 3. Phân tích nội dung huấn luyện nếu vai trò chung chung
    elif any(k in inst_lower for k in ["thuế", "chính sách thuế", "hộ kinh doanh"]):
        queries.append("tin tức chính sách thuế mới nhất cá nhân hộ kinh doanh doanh nghiệp")
        queries.append("văn bản chính sách thuế mới ban hành tổng cục thuế bộ tài chính")

    elif re.search(r'\b(openai|deepmind|anthropic|mô hình ai)\b', inst_lower):
        queries.append("OpenAI Anthropic Google DeepMind AI latest news breakthroughs")
        queries.append("TechCrunch The Verge MIT Technology Review AI product updates")

    # 4. Mặc định: Bóc tách từ khóa nghiệp vụ từ vai trò và chỉ thị huấn luyện
    else:
        clean_text = re.sub(r'#.*', '', instruction)
        words = [w for w in clean_text.split() if len(w) > 3 and w.lower() not in ["người", "dùng", "yêu", "cầu", "bạn", "hãy", "thực", "hiện", "trong", "theo", "được"]][:12]
        if words:
            queries.append(f"{role} {' '.join(words[:5])}")
            queries.append(f"{' '.join(words[5:10])}")
        else:
            queries.append(role)

    return queries


class SecretaryService:

    """Dịch vụ vận hành Thư ký AI tin tức"""



    _scheduler_started = False

    _scheduler_lock = threading.Lock()



    @classmethod

    def get_characters(cls) -> List[Dict[str, Any]]:

        """Lấy danh sách 10 nhân vật truyện cổ tích Việt Nam"""

        return VIETNAMESE_FAIRY_TALE_CHARACTERS



    @classmethod
    def get_character_by_name(cls, char_name: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin nhân vật cổ tích theo tên"""
        for c in VIETNAMESE_FAIRY_TALE_CHARACTERS:
            if c["name"].lower() == char_name.lower():
                return c
        return None

    @classmethod
    def generate_training_instruction(cls, role: str, name: str = "", character: str = "") -> Dict[str, Any]:
        """
        Sử dụng Gemini AI để tự động sinh Nội dung huấn luyện thư ký (Chỉ thị tìm kiếm Internet qua Gemini)
        dựa trên nội dung Vai trò của thư ký (role).
        """
        role_clean = (role or "").strip()
        if not role_clean:
            return {
                "success": False,
                "message": "Vui lòng nhập 'Vai Trò Của Thư Ký' trước khi bấm nút AI Prompt."
            }

        name_clean = (name or f"Thư ký {character}" or "Thư ký AI").strip()
        system_instruction = (
            "Bạn là Chuyên gia Thiết kế Prompt (Prompt Engineer) cao cấp chuyên huấn luyện các Thư ký AI Tin tức & Phân tích Chính sách. "
            "Nhiệm vụ của bạn là dựa vào 'Vai trò của thư ký' do người dùng cung cấp để viết ra một bản 'Nội dung huấn luyện thư ký "
            "(Chỉ thị tìm kiếm Internet qua Gemini)' thật chi tiết, sắc bén, thực chiến và có tính ứng dụng cao. "
            "Trả về trực tiếp nội dung chỉ thị huấn luyện (không viết lời chào rườm rà, không bọc trong dấu ngoặc kép)."
        )
        prompt = f"""Hãy viết một bản 'Nội dung huấn luyện thư ký (Chỉ thị tìm kiếm Internet qua Gemini)' chuyên sâu cho:
- Tên thư ký: {name_clean}
- Vai trò của thư ký: {role_clean}

Yêu cầu bản chỉ thị huấn luyện phải ngắn gọn, súc tích (khoảng 120 - 220 từ), rõ ràng theo 4 ý cốt lõi:
1. Mục tiêu & Từ khóa trọng tâm cần dò quét hằng ngày trên Internet gắn sát với vai trò "{role_clean}".
2. Các nguồn thông tin, cơ quan ban hành hoặc trang tin chính thống cần ưu tiên thu thập.
3. Yêu cầu phân tích: Tổng hợp bối cảnh, trích dẫn số hiệu văn bản/sự kiện, làm rõ các điểm mới, thời hạn áp dụng và đánh giá tác động thực tiễn.
4. Đề xuất khuyến nghị hành động cụ thể, thiết thực tham mưu cho Lãnh đạo / Ban Giám đốc."""

        try:
            from admin_doc_service import admin_doc_service
            ai_text = admin_doc_service.call_gemini(prompt, system_instruction=system_instruction)
            if ai_text and ai_text.strip():
                cleaned = ai_text.strip().strip('"').strip("'")
                return {
                    "success": True,
                    "status": "success",
                    "instruction": cleaned,
                    "message": "Đã tạo nội dung huấn luyện thư ký bằng Gemini AI thành công!"
                }
        except Exception as e:
            print(f"[SecretaryService] Lỗi gọi Gemini tạo AI Prompt, sử dụng mẫu thông minh: {e}")

        # Fallback thông minh bám sát vai trò nếu Gemini API bận
        fallback_instruction = (
            f"Đóng vai trò là {role_clean}, hằng ngày chủ động tìm kiếm, rà soát các tin tức thời sự, văn bản quy phạm pháp luật, "
            f"chính sách điều hành và xu hướng mới nhất trên Internet thuộc lĩnh vực phụ trách ({role_clean}).\n"
            f"- Nguồn ưu tiên: Cổng thông tin Chính phủ, Bộ Tài chính, Cục Thuế, các cơ quan quản lý chuyên ngành và báo chí kinh tế - pháp luật chính thống.\n"
            f"- Yêu cầu tổng hợp: Phân tích rõ bối cảnh ban hành, trích dẫn chính xác số hiệu văn bản/nguồn tin, làm nổi bật các điểm mới cốt lõi, "
            f"thời hạn có hiệu lực và đối tượng chịu tác động.\n"
            f"- Tham mưu điều hành: Đánh giá rủi ro/cơ hội thực tiễn và đề xuất các khuyến nghị hành động cụ thể trình Lãnh đạo / Ban Giám đốc."
        )
        return {
            "success": True,
            "status": "success",
            "instruction": fallback_instruction,
            "message": "Đã tạo nội dung huấn luyện thư ký theo vai trò thành công!"
        }




    @classmethod

    def list_reports(cls, secretary_id: str) -> List[Dict[str, Any]]:

        """Lấy danh sách tất cả các báo cáo đã thực hiện của một thư ký kèm thông tin Google Drive"""

        reports = []

        if not os.path.exists(REPORTS_DIR):

            return reports



        prefix = f"{secretary_id}__"

        for fname in os.listdir(REPORTS_DIR):

            if fname.lower().endswith(".docx"):

                full_path = os.path.join(REPORTS_DIR, fname)

                mtime = os.path.getmtime(full_path)

                dt_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")

                size_kb = round(os.path.getsize(full_path) / 1024, 1)



                # Kiểm tra xem file có thuộc thư ký này không

                belongs = False

                display_name = fname

                if fname.startswith(prefix):

                    belongs = True

                    display_name = fname[len(prefix):]

                else:

                    sec = ConfigManager.get_secretary_by_id(secretary_id)

                    if sec and sec.get("name") and sanitize_filename(sec["name"]) in fname:

                        belongs = True



                if belongs:

                    # Trích xuất metadata bổ sung từ file JSON nếu có

                    json_path = os.path.splitext(full_path)[0] + ".json"

                    drive_file_id = ""

                    drive_web_link = ""

                    created_at = dt_str

                    if os.path.exists(json_path):

                        try:

                            with open(json_path, "r", encoding="utf-8") as jf:

                                j_data = json.load(jf)

                                drive_file_id = j_data.get("drive_file_id", "")

                                drive_web_link = j_data.get("drive_web_link", "")

                                if j_data.get("created_at"):

                                    created_at = j_data.get("created_at")

                        except Exception:

                            pass



                    reports.append({

                        "filename": fname,

                        "display_name": display_name,

                        "created_at": created_at,

                        "timestamp": mtime,

                        "size_kb": size_kb,

                        "download_url": f"/api/secretaries/{secretary_id}/download-report/{fname}",

                        "drive_file_id": drive_file_id,

                        "drive_web_link": drive_web_link

                    })



        reports.sort(key=lambda x: x["timestamp"], reverse=True)

        return reports



    @classmethod

    def get_report(cls, secretary_id: str, filename: str) -> Optional[Dict[str, Any]]:

        """Lấy chi tiết một báo cáo lịch sử theo tên file"""

        clean_fn = os.path.basename(filename)

        docx_path = os.path.join(REPORTS_DIR, clean_fn)

        if not os.path.exists(docx_path):

            return None



        json_path = os.path.splitext(docx_path)[0] + ".json"

        display_name = clean_fn

        prefix = f"{secretary_id}__"

        if clean_fn.startswith(prefix):

            display_name = clean_fn[len(prefix):]



        mtime = os.path.getmtime(docx_path)

        dt_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")



        meta = {

            "filename": clean_fn,

            "display_name": display_name,

            "created_at": dt_str,

            "timestamp": mtime,

            "size_kb": round(os.path.getsize(docx_path) / 1024, 1),

            "download_url": f"/api/secretaries/{secretary_id}/download-report/{clean_fn}",

            "drive_file_id": "",

            "drive_web_link": ""

        }



        if os.path.exists(json_path):

            try:

                with open(json_path, "r", encoding="utf-8") as f:

                    cached_data = json.load(f)

                    meta["drive_file_id"] = cached_data.get("drive_file_id", "")

                    meta["drive_web_link"] = cached_data.get("drive_web_link", "")

                    if cached_data.get("created_at"):

                        meta["created_at"] = cached_data["created_at"]

                    cached_data["meta"] = meta

                    return cached_data

            except Exception as e:

                print(f"[SecretaryService] Lỗi đọc JSON báo cáo {json_path}: {e}")



        # Fallback đọc từ .docx

        if DOCX_AVAILABLE:

            try:

                doc = docx.Document(docx_path)

                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

                return {

                    "meta": meta,

                    "title": display_name,

                    "content_markdown": "\n\n".join(paragraphs),

                    "web_sources": []

                }

            except Exception as e:

                print(f"[SecretaryService] Lỗi đọc docx {docx_path}: {e}")



        return None



    @classmethod

    def get_latest_report(cls, secretary_id: str) -> Optional[Dict[str, Any]]:

        """Lấy nội dung file Word sau cùng của thư ký"""

        reports = cls.list_reports(secretary_id)

        if not reports:

            return None

        return cls.get_report(secretary_id, reports[0]["filename"])



    @classmethod

    def delete_report(cls, secretary_id: str, filename: str) -> Dict[str, Any]:

        """

        Xóa báo cáo đã chọn:

        - Xóa file .docx và .json trong manage_app/Thư ký tin tức

        - Xóa file phụ trong ____Manage App____/Thư ký tin tức (nếu có)

        - Xóa file tương ứng trên Google Drive (thư mục Thư ký Tin tức)

        - Cập nhật lại thông tin latest_report của thư ký

        """

        clean_fn = os.path.basename(filename)

        docx_path = os.path.join(REPORTS_DIR, clean_fn)

        json_path = os.path.splitext(docx_path)[0] + ".json"



        prefix = f"{secretary_id}__"

        display_name = clean_fn[len(prefix):] if clean_fn.startswith(prefix) else clean_fn

        alt_docx_path = os.path.join(ALT_REPORTS_DIR, display_name)



        drive_file_id = ""

        drive_deleted = False



        # Đọc drive_file_id từ file json trước khi xóa

        if os.path.exists(json_path):

            try:

                with open(json_path, "r", encoding="utf-8") as f:

                    j_data = json.load(f)

                    drive_file_id = j_data.get("drive_file_id", "")

            except Exception:

                pass



        # 1. Xóa trên Google Drive

        if drive_file_id:

            try:

                d_res = drive_service.delete_file(drive_file_id)

                drive_deleted = d_res.get("success", False)

                print(f"[SecretaryService] Xóa Google Drive {drive_file_id}: {d_res}")

            except Exception as ex_d:

                print(f"[SecretaryService] Lỗi xóa file Drive: {ex_d}")

        else:

            # Thử tìm và xóa theo tên file display_name trong thư mục Google Drive

            try:

                d_res = drive_service.delete_file_by_name(display_name, folder_id=DRIVE_NEWS_FOLDER_ID)

                if d_res.get("deleted_count", 0) > 0:

                    drive_deleted = True

                    print(f"[SecretaryService] Đã xóa {d_res.get('deleted_count')} file trên Drive theo tên")

            except Exception as ex_d2:

                print(f"[SecretaryService] Lỗi tìm & xóa file Drive theo tên: {ex_d2}")



        # 2. Xóa file cục bộ

        local_deleted = False

        if os.path.exists(docx_path):

            try:

                os.remove(docx_path)

                local_deleted = True

            except Exception as e:

                print(f"[SecretaryService] Lỗi xóa docx cục bộ: {e}")



        if os.path.exists(json_path):

            try:

                os.remove(json_path)

            except Exception:

                pass



        if os.path.exists(alt_docx_path):

            try:

                os.remove(alt_docx_path)

            except Exception:

                pass



        # 3. Cập nhật latest_report của thư ký nếu xóa đúng file mới nhất

        sec = ConfigManager.get_secretary_by_id(secretary_id)

        if sec:

            latest = sec.get("latest_report")

            if latest and latest.get("filename") == clean_fn:

                remaining = cls.list_reports(secretary_id)

                if remaining:

                    sec["latest_report"] = remaining[0]

                else:

                    sec["latest_report"] = None

                ConfigManager.save_secretary(sec)



        return {

            "success": True,

            "message": f"Đã xóa báo cáo '{display_name}' thành công" + (" và đã đồng bộ xóa trên Google Drive!" if drive_deleted else "."),

            "local_deleted": local_deleted,

            "drive_deleted": drive_deleted

        }



    @classmethod

    def generate_report(cls, secretary_id: str) -> Dict[str, Any]:

        """

        Thực hiện tìm kiếm thông tin trên Internet qua Gemini và lưu trữ nội dung tìm kiếm

        thành một file word (.docx) lưu trữ trong thư mục:

        - manage_app/Thư ký tin tức

        - ____Manage App____/Thư ký tin tức

        Tên file: (tên thư ký + ngày giờ tạo).docx

        """

        sec = ConfigManager.get_secretary_by_id(secretary_id)

        if not sec:

            return {"success": False, "error": f"Không tìm thấy thư ký có ID: {secretary_id}"}



        sec_name = sec.get("name", "Thư ký Tin tức")

        char_name = sec.get("character", "Thạch Sanh")

        role = sec.get("role", "Thư ký tổng hợp tin tức")

        instruction = sec.get("instruction", "Tìm kiếm các tin tức và chính sách mới nhất trên Internet.")

        time_range = sec.get("search_time_range", "1_week")

        from_date = sec.get("search_from_date", "")

        to_date = sec.get("search_to_date", "")



        now = datetime.datetime.now()

        now_str = now.strftime("%Y%m%d_%H%M%S")

        now_display = now.strftime("%d/%m/%Y %H:%M:%S")



        # Xác định phạm vi thời gian tìm kiếm

        if time_range == "today_yesterday":

            time_desc = "trong 24 giờ đến 48 giờ qua (từ hôm qua đến hôm nay)"

        elif time_range == "1_week":

            time_desc = "trong vòng 7 ngày qua (1 tuần trước đến nay)"

        elif time_range == "2_weeks":

            time_desc = "trong vòng 14 ngày qua (2 tuần trước đến nay)"

        elif time_range == "custom" and from_date and to_date:

            time_desc = f"từ ngày {from_date} đến ngày {to_date}"

        else:

            time_desc = "trong 7 ngày gần nhất"



        # 1. Tra cứu thông tin trên Internet thời gian thực bằng Multi-Queries thông minh

        search_queries = generate_smart_search_queries(role, instruction, time_range)

        all_web_sources = []

        context_parts = []

        seen_uris = set()



        for q in search_queries:

            ctx, srcs, _ = AssistantService.search_web_realtime(q, max_results=5)

            if ctx:

                context_parts.append(ctx)

            for s in srcs:

                uri = s.get("uri", "")

                if uri and uri not in seen_uris:

                    seen_uris.add(uri)

                    all_web_sources.append(s)



        web_context = "\n\n".join(context_parts)

        web_sources = all_web_sources[:12] # Lấy tối đa 12 nguồn tin cậy nhất



        # 2. Xây dựng prompt tổng hợp tin tức cho Gemini (TUÂN THỦ 100% ĐỊNH DẠNG HUẤN LUYỆN)

        config = ConfigManager.load_config()

        api_key = config.get("gemini", {}).get("api_key", "").strip()

        if not api_key:

            return {

                "success": False,

                "error": "Chưa cấu hình Gemini API Key. Vui lòng cài đặt API Key trong 'Thiết lập chung'."

            }



        prompt = f"""Bạn là {sec_name} (Hình tượng nhân vật: {char_name}), đảm nhận vai trò: "{role}".



NHIỆM VỤ HUẤN LUYỆN & QUY TRÌNH THỰC HIỆN CỦA BẠN:

{instruction}



THỜI GIAN THỰC HIỆN: {now_display}

PHẠM VI THỜI GIAN CẦN QUÉT VÀ BÁO CÁO: {time_desc}



DỮ LIỆU TÌM KIẾM TRÊN INTERNET MỚI NHẤT ({time_desc}):

{web_context if web_context else "Dữ liệu tra cứu tự động đang được làm mới, hãy vận dụng tri thức công nghệ cập nhật mới nhất để lập báo cáo."}



YÊU CẦU QUAN TRỌNG KHI LẬP BÁO CÁO:

1. TUÂN THỦ ĐỊNH DẠNG ĐẦU RA:

   - Nếu trong nội dung huấn luyện có quy định cấu trúc (ví dụ "# ĐỊNH DẠNG ĐẦU RA (OUTPUT FORMAT)", các mục ### [Số thứ tự], Tóm tắt sự kiện, Phân tích tác động, Nguồn & Thời gian, Tổng kết xu hướng), bạn BẮT BUỘC PHẢI TRÌNH BÀY ĐÚNG THEO CẤU TRÚC ĐÓ, KHÔNG được tự ý đổi sang cấu trúc khác!

   - Nếu bạn là Thư ký AI/Công nghệ thế giới, nội dung báo cáo 100% PHẢI TẬP TRUNG VÀO CÁC CÔNG NGHỆ, MÔ HÌNH VÀ SẢN PHẨM AI TRÊN THẾ GIỚI (OpenAI, Google DeepMind, Anthropic, Meta, NVIDIA, v.v.), TUYỆT ĐỐI KHÔNG đưa tin việc làm hay mức lương ở Việt Nam!

2. DẪN LINK NGUỒN CỤ THỂ VÀ CHÍNH XÁC:

   - Tại mỗi tin tức (mục Nguồn & Thời gian), BẮT BUỘC phải dẫn đường link URL đầy đủ (dạng Markdown link [Tên nguồn](URL) hoặc (URL) với URL đầy đủ bắt đầu bằng https://...) lấy từ dữ liệu tìm kiếm bên trên.

   - Tuyệt đối KHÔNG chỉ ghi tên miền chung chung như 'thanhnien.vn' hay 'TechCrunch' mà không có link URL cụ thể.

3. Trình bày bằng tiếng Việt chuyên nghiệp, sắc sảo, logic, chuẩn định dạng Markdown."""



        # Gọi Gemini API

        selected_model = config.get("gemini", {}).get("model", "gemini-2.5-flash")

        candidate_models = [selected_model, "gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]

        generated_text = ""

        last_error = ""



        for model_cand in candidate_models:

            if not model_cand:

                continue

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_cand}:generateContent?key={api_key}"

            payload = {

                "contents": [{"role": "user", "parts": [{"text": prompt}]}],

                "generationConfig": {

                    "temperature": 0.25,

                    "topP": 0.95,

                    "maxOutputTokens": 8192

                }

            }

            try:

                import requests

                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=55)

                if resp.status_code == 200:

                    r_json = resp.json()

                    candidates = r_json.get("candidates", [])

                    if candidates:

                        parts = candidates[0].get("content", {}).get("parts", [])

                        generated_text = "".join([p.get("text", "") for p in parts if "text" in p])

                        if generated_text.strip():

                            break

                else:

                    last_error = f"{resp.status_code}: {resp.text[:200]}"

            except Exception as ex_m:

                last_error = str(ex_m)



        if not generated_text.strip():

            return {

                "success": False,

                "error": f"Không thể tạo nội dung báo cáo từ AI: {last_error or 'Lỗi phản hồi rỗng'}"

            }



        # 3. Tạo file Word (.docx) theo đúng tên quy định: (tên thư ký + ngày giờ tạo).docx

        clean_name = sanitize_filename(sec_name)

        file_basename = f"{clean_name} - {now_str}.docx"

        internal_filename = f"{secretary_id}__{file_basename}"



        docx_path = os.path.join(REPORTS_DIR, internal_filename)

        alt_docx_path = os.path.join(ALT_REPORTS_DIR, file_basename)

        json_path = os.path.splitext(docx_path)[0] + ".json"



        # Xuất file Word với True Hyperlinks

        if DOCX_AVAILABLE:

            try:

                doc = docx.Document()



                # Căn lề chuẩn A4 hành chính

                for section in doc.sections:

                    section.top_margin = Inches(0.8)

                    section.bottom_margin = Inches(0.8)

                    section.left_margin = Inches(1.0)

                    section.right_margin = Inches(0.8)



                # Header báo cáo

                title_p = doc.add_paragraph()

                title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                run_title = title_p.add_run("BÁO CÁO TIN TỨC TỔNG HỢP & PHÂN TÍCH CHUYÊN MÔN")

                run_title.bold = True

                run_title.font.name = "Times New Roman"

                run_title.font.size = Pt(16)

                run_title.font.color.rgb = RGBColor(0, 40, 85)



                sub_p = doc.add_paragraph()

                sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                run_sub = sub_p.add_run(f"Hệ thống Thư Ký AI Tin Tức — Trực thuộc Ban Điều hành HB MIND")

                run_sub.italic = True

                run_sub.font.name = "Times New Roman"

                run_sub.font.size = Pt(11)

                run_sub.font.color.rgb = RGBColor(100, 116, 139)



                # Bảng thông tin thư ký

                table = doc.add_table(rows=5, cols=2)

                table.alignment = WD_TABLE_ALIGNMENT.CENTER

                table.autofit = False



                info_rows = [

                    ("Thư ký phụ trách:", f"{sec_name} (Hình tượng cổ tích: {char_name})"),

                    ("Vai trò chức năng:", role),

                    ("Phạm vi thời gian:", time_desc),

                    ("Thời gian thực hiện:", now_display),

                    ("Phương thức tra cứu:", "Gemini AI Search Grounding & Realtime Multi-Query Web Crawler")

                ]



                for idx, (label, val) in enumerate(info_rows):

                    row = table.rows[idx]

                    cell_lbl = row.cells[0]

                    cell_val = row.cells[1]

                    cell_lbl.width = Inches(1.8)

                    cell_val.width = Inches(4.8)



                    p_lbl = cell_lbl.paragraphs[0]

                    r_lbl = p_lbl.add_run(label)

                    r_lbl.bold = True

                    r_lbl.font.name = "Times New Roman"

                    r_lbl.font.size = Pt(10.5)



                    p_val = cell_val.paragraphs[0]

                    r_val = p_val.add_run(val)

                    r_val.font.name = "Times New Roman"

                    r_val.font.size = Pt(10.5)



                doc.add_paragraph()



                # Nội dung chi tiết báo cáo kèm TRUE HYPERLINKS

                for line in generated_text.splitlines():

                    line_s = line.strip()

                    if not line_s:

                        continue

                    p = doc.add_paragraph()

                    if line_s.startswith("# "):

                        run = p.add_run(line_s[2:])

                        run.bold = True

                        run.font.name = "Times New Roman"

                        run.font.size = Pt(14)

                        run.font.color.rgb = RGBColor(0, 40, 85)

                    elif line_s.startswith("## "):

                        run = p.add_run(line_s[3:])

                        run.bold = True

                        run.font.name = "Times New Roman"

                        run.font.size = Pt(12.5)

                        run.font.color.rgb = RGBColor(2, 132, 199)

                    elif line_s.startswith("### "):

                        run = p.add_run(line_s[4:])

                        run.bold = True

                        run.font.name = "Times New Roman"

                        run.font.size = Pt(11.5)

                    elif line_s.startswith("- ") or line_s.startswith("* "):

                        p.paragraph_format.left_indent = Inches(0.25)

                        bullet_content = line_s[2:]

                        add_line_with_hyperlinks(p, "• " + bullet_content, default_font_size=11)

                    else:

                        add_line_with_hyperlinks(p, line_s, default_font_size=11)



                # Nguồn tham khảo với CLICKABLE HYPERLINKS

                if web_sources:

                    doc.add_paragraph()

                    src_h = doc.add_paragraph()

                    r_sh = src_h.add_run("DANH MỤC NGUỒN THAM KHẢO INTERNET:")

                    r_sh.bold = True

                    r_sh.font.name = "Times New Roman"

                    r_sh.font.size = Pt(11)

                    r_sh.font.color.rgb = RGBColor(0, 40, 85)



                    for src in web_sources:

                        sp = doc.add_paragraph()

                        sp.paragraph_format.left_indent = Inches(0.25)

                        r_t = sp.add_run(f"- {src.get('title', 'Nguồn')}: ")

                        r_t.bold = True

                        r_t.font.name = "Times New Roman"

                        r_t.font.size = Pt(10)



                        uri_str = src.get('uri', '')

                        if uri_str:

                            add_hyperlink(sp, uri_str, uri_str, color="0284C7", underline=True)



                doc.save(docx_path)



                try:

                    shutil.copy2(docx_path, alt_docx_path)

                except Exception as ex_sync:

                    print(f"[SecretaryService] Lỗi đồng bộ sang thư mục phụ: {ex_sync}")



            except Exception as ex_docx:

                print(f"[SecretaryService] Lỗi tạo file Word: {ex_docx}")



        # 4. Tải file Word (.docx) lên thư mục Google Drive: Drive của tôi > ____Manage App____ > Thư ký Tin tức

        drive_file_id = ""

        drive_web_link = ""

        try:

            if os.path.exists(docx_path):

                with open(docx_path, "rb") as f_docx:

                    docx_bytes = f_docx.read()

                d_res = drive_service.upload_file(

                    file_content=docx_bytes,

                    filename=file_basename,

                    folder_id=DRIVE_NEWS_FOLDER_ID,

                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                )

                if d_res and d_res.get("success"):

                    drive_file_id = d_res.get("id", "")

                    drive_web_link = d_res.get("webViewLink", "")

                    print(f"[SecretaryService] Đã tải lên Google Drive thành công: {file_basename} (id={drive_file_id})")

                else:

                    print(f"[SecretaryService] Cảnh báo tải file lên Google Drive: {d_res.get('message')}")

        except Exception as ex_drive:

            print(f"[SecretaryService] Lỗi upload Google Drive: {ex_drive}")



        # 5. Lưu file JSON hỗ trợ render Web tức thời

        report_data = {

            "secretary_id": secretary_id,

            "secretary_name": sec_name,

            "character": char_name,

            "role": role,

            "search_time_range": time_range,

            "time_desc": time_desc,

            "created_at": now_display,

            "filename": internal_filename,

            "display_filename": file_basename,

            "download_url": f"/api/secretaries/{secretary_id}/download-report/{internal_filename}",

            "content_markdown": generated_text,

            "web_sources": web_sources,

            "alt_file_path": alt_docx_path,

            "drive_file_id": drive_file_id,

            "drive_web_link": drive_web_link

        }



        try:

            with open(json_path, "w", encoding="utf-8") as f:

                json.dump(report_data, f, ensure_ascii=False, indent=2)

        except Exception as ex_json:

            print(f"[SecretaryService] Lỗi lưu cache JSON: {ex_json}")



        # Cập nhật thông tin thư ký (last_run, latest_report)

        sec["last_run"] = now_display

        sec["latest_report"] = {

            "filename": internal_filename,

            "display_filename": file_basename,

            "created_at": now_display,

            "download_url": f"/api/secretaries/{secretary_id}/download-report/{internal_filename}",

            "drive_file_id": drive_file_id,

            "drive_web_link": drive_web_link

        }

        ConfigManager.save_secretary(sec)



        # 6. Gửi thông báo đến quả chuông thông báo trên thanh tiêu đề (Header Notification Bell)

        try:

            ChiefSecretaryService.add_notification({

                "id": f"sec_{secretary_id}_{int(time.time() * 1000)}",

                "type": "secretary_report",

                "title": f"{(sec_name if sec_name.lower().startswith('thư ký') else f'Thư ký {sec_name}')} đã hoàn thành báo cáo!",

                "content": f"Báo cáo: {file_basename}",

                "secretary_id": secretary_id,

                "report_filename": internal_filename,

                "time": now.strftime("%H:%M"),

                "created_at": now.strftime("%d/%m %H:%M"),

                "is_read": False

            })

            print(f"[SecretaryService] Đã gửi thông báo quả chuông cho thư ký {sec_name}")

        except Exception as ex_notif:

            print(f"[SecretaryService] Lỗi gửi thông báo quả chuông: {ex_notif}")



        return {

            "success": True,

            "message": f"Thư ký {sec_name} đã hoàn thành báo cáo tin tức thành công!",

            "report": report_data

        }

    @classmethod

    def start_scheduler(cls):

        """Khởi động Background Scheduler để tự động chạy báo cáo theo giờ thiết lập"""

        with cls._scheduler_lock:

            if cls._scheduler_started:

                return

            cls._scheduler_started = True



        def scheduler_worker():

            print("[SecretaryService] Bộ lập lịch tự động báo cáo Thư Ký AI đã khởi động.")

            while True:

                try:

                    now = datetime.datetime.now()

                    current_hm = now.strftime("%H:%M")

                    today_ymd = now.strftime("%Y-%m-%d")



                    secretaries = ConfigManager.get_secretaries()

                    for sec in secretaries:

                        sched_time = sec.get("scheduled_time", "").strip()

                        if sched_time and sched_time == current_hm:

                            last_run = sec.get("last_run", "")

                            # Kiểm tra xem hôm nay đã chạy chưa

                            if not last_run or not last_run.startswith(now.strftime("%d/%m/%Y")):

                                sec_id = sec.get("id")

                                sec_name = sec.get("name")

                                print(f"[SecretaryService] Đang tự động chạy nhiệm vụ cho Thư ký: {sec_name} (Giờ hẹn: {sched_time})")

                                try:

                                    cls.generate_report(sec_id)

                                    print(f"[SecretaryService] Hoàn thành báo cáo tự động cho Thư ký: {sec_name}")

                                except Exception as ex_task:

                                    print(f"[SecretaryService] Lỗi chạy báo cáo tự động cho {sec_name}: {ex_task}")

                except Exception as ex_loop:

                    print(f"[SecretaryService] Lỗi Scheduler loop: {ex_loop}")



                # Chờ 30 giây trước khi kiểm tra lại

                time.sleep(30)



        t = threading.Thread(target=scheduler_worker, daemon=True)

        t.start()





# Khởi động scheduler khi import

SecretaryService.start_scheduler()

