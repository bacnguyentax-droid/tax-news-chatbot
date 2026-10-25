import os
import sys
import io
import re
import json
import time
import urllib.parse
import requests
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.http import MediaIoBaseUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_FILE = os.path.join(BASE_DIR, "carousel_presets.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "generated_slides")

# System fonts for Windows with Unicode Vietnamese support
def get_fonts(title_size=42, body_size=28, badge_size=20, small_size=18, num_size=54):
    font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    font_reg_path = r"C:\Windows\Fonts\arial.ttf"
    if not os.path.exists(font_bold_path):
        font_bold_path = r"C:\Windows\Fonts\segoeuib.ttf"
    if not os.path.exists(font_reg_path):
        font_reg_path = r"C:\Windows\Fonts\segoeui.ttf"

    try:
        num_font = ImageFont.truetype(font_bold_path, num_size)
        title_font = ImageFont.truetype(font_bold_path, title_size)
        body_font = ImageFont.truetype(font_reg_path, body_size)
        body_bold = ImageFont.truetype(font_bold_path, body_size)
        badge_font = ImageFont.truetype(font_bold_path, badge_size)
        small_font = ImageFont.truetype(font_reg_path, small_size)
    except Exception:
        def_font = ImageFont.load_default()
        num_font = title_font = body_font = body_bold = badge_font = small_font = def_font

    return {
        "num": num_font,
        "title": title_font,
        "body": body_font,
        "body_bold": body_bold,
        "badge": badge_font,
        "small": small_font
    }


COLOR_KEYWORDS = {
    "đỏ đô": (143, 16, 32),
    "đỏ": (220, 38, 38),
    "vàng kim": (234, 179, 8),
    "vàng đồng": (184, 134, 11),
    "vàng": (234, 179, 8),
    "cam cháy": (234, 88, 12),
    "cam đất": (223, 138, 90),
    "cam": (249, 115, 22),
    "xanh lá": (22, 163, 74),
    "xanh ngọc": (16, 185, 129),
    "xanh mint": (52, 211, 153),
    "xanh dương": (37, 99, 235),
    "xanh biển": (14, 165, 233),
    "xanh cyan": (6, 182, 212),
    "xanh tím": (79, 70, 229),
    "hồng phấn": (252, 232, 234),
    "hồng": (236, 72, 153),
    "tím than": (30, 27, 75),
    "tím": (124, 58, 237),
    "đen obsidian": (11, 15, 25),
    "đen tuyền": (15, 23, 42),
    "đen than": (28, 28, 28),
    "đen": (24, 24, 27),
    "trắng kem": (250, 248, 247),
    "trắng ngà": (251, 248, 243),
    "trắng": (255, 255, 255),
    "xám nhạt": (238, 240, 242),
    "xám": (100, 116, 139)
}

CONCEPT_MAPPINGS = [
    (r'thuê nhà|nhà đất|bất động sản', 'real estate house rental property'),
    (r'kinh doanh|hộ kinh doanh|bán hàng|thương mại điện tử|shopee|tiktok shop', 'modern ecommerce online shop business'),
    (r'hóa đơn|kê khai|khai thuế|chứng từ', 'tax invoice accounting documents paperwork'),
    (r'lương|thu nhập cá nhân|tncn', 'salary personal income financial growth'),
    (r'phạt|vi phạm|rủi ro|cảnh báo|truy thu', 'urgent warning caution alert risk avoidance'),
    (r'etax|công nghệ|số|app|điện tử', 'digital mobile smartphone app technology finance'),
    (r'luật|nghị định|thông tư|pháp lý', 'official government legal compliance documents'),
    (r'tiết kiệm|tối ưu|chi phí', 'wealth protection investment savings coins gold'),
    (r'đố vui|thử thách|câu hỏi', 'quiz challenge question idea concept'),
]

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_luminance(rgb: Tuple[int, ...]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

def extract_preset_design(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trích xuất toàn diện màu sắc, kiểu dáng bố cục và phong cách nghệ thuật
    trực tiếp từ 'Chỉ dẫn AI tạo ảnh' (instruction) và mô tả của mẫu (preset).
    Đảm bảo ảnh slide tạo ra tuân thủ tuyệt đối chỉ dẫn thiết kế của người dùng.
    """
    pid = str(preset.get("id") or "").lower()
    name = preset.get("name", "")
    desc = preset.get("description", "")
    inst = preset.get("instruction", "")
    combined = f"{name}\n{desc}\n{inst}".lower()

    hexes = [h.upper() for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", inst + " " + desc)]
    hex_rgbs = [hex_to_rgb(h) for h in hexes]

    bg_color = None
    accent_color = None
    tag_bg = None
    border_color = None

    # 1. Trích xuất màu nền (Background)
    bg_m = re.search(r"(?:nền tổng thể|màu nền|nền|background|tông màu)[^\n#]*#([0-9a-fA-F]{6})", inst + " " + desc, re.IGNORECASE)
    if bg_m:
        bg_color = hex_to_rgb(bg_m.group(1))

    # 2. Trích xuất màu nhấn chủ đạo (Accent Color)
    acc_m = re.search(r"(?:nhấn chủ đạo|màu nhấn|chủ đạo|viền|banner|dải)[^\n#]*#([0-9a-fA-F]{6})", inst + " " + desc, re.IGNORECASE)
    if acc_m:
        accent_color = hex_to_rgb(acc_m.group(1))

    # 3. Trích xuất màu thẻ/nhãn phụ (Tag / Sub-card Color)
    tag_m = re.search(r"(?:thẻ thông tin 1.*?hộp bo góc nền|thẻ hộp bo góc màu|hộp bo góc nền|hộp bo góc màu|thẻ thông tin|hồng phấn)[^\n#]*#([0-9a-fA-F]{6})", inst, re.IGNORECASE)
    if tag_m:
        tag_bg = hex_to_rgb(tag_m.group(1))

    # 4. Trích xuất màu viền / thẻ danh sách
    card_m = re.search(r"(?:thẻ danh sách.*?viền|hộp bo góc viền|viền|đường kẻ|khung viền)[^\n#]*#([0-9a-fA-F]{6})", inst, re.IGNORECASE)
    if card_m:
        border_color = hex_to_rgb(card_m.group(1))

    # Fallback dựa trên các mã màu Hex trong chỉ dẫn
    if not bg_color and hex_rgbs:
        if any(w in combined for w in ["dark", "đen", "tối", "obsidian", "neon"]):
            bg_color = min(hex_rgbs, key=get_luminance)
        else:
            bg_color = max(hex_rgbs, key=get_luminance)

    # Fallback theo Preset ID có sẵn nếu không có hex riêng
    if not bg_color:
        if "breaking_news" in pid:
            bg_color = (185, 28, 28)
            accent_color = accent_color or (250, 204, 21)
        elif "warning" in pid:
            bg_color = (69, 10, 10)
            accent_color = accent_color or (251, 191, 36)
        elif "financial" in pid:
            bg_color = (251, 248, 243)
            accent_color = accent_color or (184, 134, 11)
        elif "luxury" in pid or "gold" in pid:
            bg_color = (11, 15, 25)
            accent_color = accent_color or (234, 179, 8)
        elif "neon" in pid or "cyber" in pid:
            bg_color = (9, 13, 22)
            accent_color = accent_color or (6, 182, 212)
        elif "pastel" in pid:
            bg_color = (240, 253, 244)
            accent_color = accent_color or (13, 148, 136)
        elif "vintage" in pid or "newspaper" in pid:
            bg_color = (245, 235, 225)
            accent_color = accent_color or (41, 37, 36)
        elif any(w in combined for w in ["dark", "đen", "tối", "obsidian", "neon"]):
            bg_color = (15, 23, 42)
        else:
            bg_color = (250, 248, 247)

    is_dark = get_luminance(bg_color) < 120

    if not accent_color and hex_rgbs:
        candidates = [c for c in hex_rgbs if abs(get_luminance(c) - get_luminance(bg_color)) > 45]
        if candidates:
            accent_color = candidates[0]

    if not accent_color:
        for kw, rgb in COLOR_KEYWORDS.items():
            if kw in combined and "nền" not in kw and "trắng" not in kw:
                accent_color = rgb
                break

    if not accent_color:
        accent_color = (234, 179, 8) if is_dark else (143, 16, 32)

    if not tag_bg:
        if is_dark:
            tag_bg = (max(20, accent_color[0] // 3), max(25, accent_color[1] // 3), max(35, accent_color[2] // 3))
        else:
            if accent_color[0] > 120 and accent_color[1] < 60:
                tag_bg = (252, 232, 234) # Soft pink for red accents
            else:
                tag_bg = (min(255, accent_color[0] + 120), min(255, accent_color[1] + 140), min(255, accent_color[2] + 140))

    if not border_color:
        border_color = (51, 65, 85) if is_dark else (238, 240, 242)

    if is_dark:
        card_bg = (bg_color[0] + 14, bg_color[1] + 18, bg_color[2] + 25, 245)
        text_title_color = (255, 255, 255)
        text_body_color = (226, 232, 240)
    else:
        card_bg = (255, 255, 255, 250)
        text_title_color = (28, 28, 28)
        text_body_color = (30, 41, 59)

    # Trích xuất phong cách nghệ thuật AI từ Chỉ dẫn AI
    if "3d" in combined or "pixar" in combined:
        art_style = "3D Pixar animation style, friendly 3D character, clean smooth render"
    elif "neon" in combined or "cyber" in combined:
        art_style = "cyberpunk glowing neon tech vector art, futuristic dark background"
    elif "luxury" in combined or "gold" in combined:
        art_style = "luxury royal gold and obsidian black illustration, prestigious financial aesthetic"
    elif "retro" in combined or "vintage" in combined or "báo in" in combined:
        art_style = "vintage retro newspaper print illustration, classic monochrome linocut"
    elif "cảnh báo" in combined or "warning" in combined or "breaking" in combined:
        art_style = "urgent breaking news graphic illustration, bold high contrast design"
    elif "isometric" in combined:
        art_style = "3D isometric vector illustration, clean geometric graphics"
    elif "đỏ - trắng" in combined or "đỏ đô" in combined:
        art_style = "2D flat vector UI design, crimson red (#8F1020) and cream white (#FAF8F7) aesthetic"
    else:
        art_style = "2D modern flat vector UI design illustration, clean minimalist graphic design"

    return {
        "name": name,
        "bg_top": bg_color,
        "bg_bottom": (max(0, bg_color[0] - 8), max(0, bg_color[1] - 8), max(0, bg_color[2] - 8)),
        "accent_color": accent_color,
        "tag_bg": tag_bg,
        "border_color": border_color,
        "card_bg": card_bg,
        "text_title_color": text_title_color,
        "text_body_color": text_body_color,
        "is_dark": is_dark,
        "art_style": art_style
    }


def build_ai_art_prompt(preset: Dict[str, Any], slide_info: Dict[str, Any], chu_de: str = "") -> str:
    """
    Sinh câu lệnh tạo ảnh AI (Prompt) dựa hoàn toàn vào 'Chỉ dẫn AI tạo ảnh' của Preset
    kết hợp với tiêu đề, loại slide và ngữ cảnh nội dung thực tế.
    """
    title = str(slide_info.get("title") or "").strip()
    stype = str(slide_info.get("slide_type") or "").strip()
    bullets = slide_info.get("bullets", [])
    combined_text = f"{chu_de} {title} {stype} " + " ".join(bullets)
    combined_lower = combined_text.lower()

    design = extract_preset_design(preset)
    art_style = design.get("art_style", "2D flat vector UI design")

    concepts = []
    for pat, eng in CONCEPT_MAPPINGS:
        if re.search(pat, combined_lower):
            concepts.append(eng)
    concept_str = ", ".join(concepts[:2]) if concepts else "finance taxation Vietnam economy"

    inst = preset.get("instruction", "")
    hexes = re.findall(r"#[0-9a-fA-F]{6}", inst)
    if hexes:
        hex_str = ", ".join(hexes[:3])
        palette_str = f"color palette ({hex_str})"
    else:
        r, g, b = design.get("accent_color", (143, 16, 32))
        palette_str = f"color accent rgb({r},{g},{b})"

    prompt = (
        f"{art_style}, visual concept of {concept_str}, {palette_str}, "
        f"clean modern graphic design, 4:5 vertical composition, "
        f"no text, no letters, no words, no watermark, professional high quality vector illustration"
    )
    return prompt


def load_presets() -> List[Dict[str, Any]]:
    """Tải danh sách các mẫu thông số ảnh cuộn"""
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SlideGen] Lỗi đọc presets: {e}")
    return []


def save_presets(presets: List[Dict[str, Any]]) -> bool:
    """Lưu danh sách thông số ảnh cuộn"""
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[SlideGen] Lỗi lưu presets: {e}")
        return False


def get_preset_by_id(preset_id: str) -> Optional[Dict[str, Any]]:
    """Lấy preset theo ID"""
    presets = load_presets()
    for p in presets:
        if p.get("id") == preset_id:
            return p
    # Nếu không tìm thấy, trả về preset mặc định đầu tiên
    for p in presets:
        if p.get("is_default"):
            return p
    return presets[0] if presets else None


def parse_script_to_slides(script_text: str) -> List[Dict[str, Any]]:
    """
    Phân tích nội dung kịch bản văn bản thành từng slide có cấu trúc:
    Slide index, Tiêu đề, Loại slide, Các điểm nội dung.
    """
    if not script_text or not script_text.strip():
        return []

    lines = script_text.splitlines()
    slides = []
    current_slide = None
    slide_pattern = re.compile(r'^(?:SLIDE\s+(\d+|CUỐI)|Slide\s+(\d+|cuối))\s*:\s*(.*)', re.IGNORECASE)

    for line in lines:
        raw_line = line.strip()
        if not raw_line or raw_line.startswith("______") or raw_line.startswith("KỊCH BẢN") or raw_line.startswith("Chuyên mục:"):
            continue

        match = slide_pattern.match(raw_line)
        if match:
            if current_slide:
                slides.append(current_slide)
            
            s_num_str = match.group(1) or match.group(2)
            s_type = match.group(3).strip() if len(match.groups()) >= 3 else ""
            current_slide = {
                "slide_num": len(slides) + 1,
                "slide_label": f"SLIDE {s_num_str.upper()}",
                "slide_type": s_type,
                "title": "",
                "bullets": []
            }
            continue

        if current_slide:
            if raw_line.lower().startswith("tiêu đề:") or raw_line.lower().startswith("tiêu đề :"):
                current_slide["title"] = raw_line.split(":", 1)[1].strip().strip("*").strip('"')
            elif raw_line.lower().startswith("nội dung:"):
                continue
            elif raw_line.startswith("*") or raw_line.startswith("-") or raw_line.startswith("•"):
                clean_bullet = re.sub(r'^[\*\-•\s]+', '', raw_line).strip()
                if clean_bullet:
                    current_slide["bullets"].append(clean_bullet)
            elif raw_line.startswith("CĂN CỨ") or raw_line.startswith("http"):
                # Bỏ qua phần căn cứ tra cứu pháp luật ở cuối kịch bản
                break
            else:
                if not current_slide["title"] and not current_slide["bullets"]:
                    current_slide["title"] = raw_line.strip("*")
                else:
                    current_slide["bullets"].append(raw_line)

    if current_slide:
        slides.append(current_slide)

    # Fallback nếu script không có format chuẩn SLIDE 1, SLIDE 2
    if not slides:
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        for idx, p in enumerate(paragraphs[:6], start=1):
            p_lines = [l.strip() for l in p.splitlines() if l.strip()]
            slides.append({
                "slide_num": idx,
                "slide_label": f"SLIDE {idx}",
                "slide_type": "Thông tin thuế",
                "title": p_lines[0] if p_lines else f"Thông Điệp {idx}",
                "bullets": p_lines[1:] if len(p_lines) > 1 else [p_lines[0]]
            })

    return slides


def clean_display_text(text: str) -> str:
    """Loại bỏ emoji và ký tự không hiển thị được trên font hệ thống"""
    if not text:
        return ""
    clean = re.sub(r'[𐀀-􏿿]', '', text)
    clean = re.sub(r'[☀-➿]', '', clean)
    clean = re.sub(r'[︀-️‍]', '', clean)
    return clean.strip()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Tự động ngắt dòng vừa vặn với độ rộng màn hình"""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def generate_slide_image(
    slide_info: Dict[str, Any],
    total_slides: int,
    chu_de: str,
    preset: Dict[str, Any],
    width: int = 1080,
    height: int = 1350
) -> Image.Image:
    """
    Tạo hình ảnh slide 4:5 (1080x1350) chất lượng cao theo chuẩn Infographic phẳng chuyên nghiệp:
    - Bám sát hoàn toàn 'Chỉ dẫn AI tạo ảnh' (bảng màu, cấu trúc thẻ, phông chữ sắc nét)
    - Loại bỏ hoàn toàn hình ảnh nền trừu tượng / banner nhân tạo rườm rà
    - Bố cục 2 Thẻ Card thoáng đãng, dễ đọc, chuẩn Safe Zone TikTok
    """
    design = extract_preset_design(preset)
    fonts = get_fonts(title_size=42, body_size=30, badge_size=20, small_size=18, num_size=54)

    bg_top = design["bg_top"]
    bg_bottom = design["bg_bottom"]
    accent_color = design["accent_color"]
    tag_bg = design["tag_bg"]
    border_color = design["border_color"]
    card_bg = design["card_bg"]
    text_title_color = design["text_title_color"]
    text_body_color = design["text_body_color"]

    # 1. Vẽ Gradient nền mượt mà theo đúng bảng màu chỉ dẫn AI
    base_img = Image.new("RGB", (width, height), bg_top)
    draw = ImageDraw.Draw(base_img)

    for y in range(height):
        ratio = y / height
        r = int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Lớp phủ Card và Typography bằng RGBA
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    slide_num = slide_info.get("slide_num", 1)
    slide_title = clean_display_text(str(slide_info.get("title") or chu_de or "Chính Sách Thuế"))
    margin_x = 55
    content_width = width - (margin_x * 2)

    # 2. HEADER AREA
    # Bên trái: Ô vuông bo góc màu accent chứa số thứ tự slide
    box_w, box_h = 105, 105
    ov_draw.rounded_rectangle([(margin_x, 60), (margin_x + box_w, 60 + box_h)], radius=20, fill=accent_color)
    num_str = f"{slide_num:02d}"
    nb_bbox = ov_draw.textbbox((0, 0), num_str, font=fonts["num"])
    nb_w = nb_bbox[2] - nb_bbox[0]
    ov_draw.text((margin_x + (box_w - nb_w) // 2, 68), num_str, font=fonts["num"], fill=(255, 255, 255))
    ov_draw.text((margin_x + (box_w - 42) // 2, 126), "SLIDE", font=fonts["small"], fill=(255, 255, 255, 220))

    # Tiêu đề chính bên cạnh ô số thứ tự (mở rộng tối đa bề ngang, không còn badge kênh rườm rà)
    title_start_x = margin_x + box_w + 24
    title_max_w = width - margin_x - title_start_x
    title_lines = wrap_text(slide_title.upper(), fonts["title"], title_max_w, ov_draw)
    ty = 60
    for idx, t_line in enumerate(title_lines[:3]):
        line_color = accent_color if idx == 0 else text_title_color
        ov_draw.text((title_start_x, ty), t_line, font=fonts["title"], fill=line_color)
        tb = ov_draw.textbbox((0, 0), t_line, font=fonts["title"])
        ty += (tb[3] - tb[0]) + 8

    # Đường gạch chân mảnh hai màu (Accent + Border)
    line_y = 185
    ov_draw.line([(margin_x, line_y), (margin_x + 220, line_y)], fill=accent_color, width=4)
    ov_draw.line([(margin_x + 230, line_y), (width - margin_x, line_y)], fill=border_color, width=2)

    # 3. THẺ THÔNG TIN NỔI BẬT (Thẻ 1 - Highlight Card)
    card1_top = 205
    card1_h = 215
    ov_draw.rounded_rectangle([(margin_x, card1_top), (width - margin_x, card1_top + card1_h)], radius=24, fill=tag_bg, outline=accent_color, width=2)

    stype = str(slide_info.get("slide_type") or ("HOOK / BÌA" if slide_num == 1 else ("KẾT LUẬN / CTA" if slide_num == total_slides else f"NỘI DUNG {slide_num}"))).strip()
    stype_label = f"● {stype.upper()}"
    sb = ov_draw.textbbox((0, 0), stype_label, font=fonts["badge"])
    stype_w = (sb[2] - sb[0]) + 36
    ov_draw.rounded_rectangle([(margin_x + 24, card1_top + 22), (margin_x + 24 + stype_w, card1_top + 62)], radius=16, fill=accent_color)
    ov_draw.text((margin_x + 42, card1_top + 32), stype_label, font=fonts["badge"], fill=(255, 255, 255))

    bullets = [clean_display_text(b) for b in slide_info.get("bullets", []) if clean_display_text(b)]
    hero_text = bullets[0] if bullets else "Cập nhật chính sách thuế mới nhất có hiệu lực từ năm 2026"
    card1_is_dark = get_luminance(tag_bg) < 128
    card1_text_color = (248, 250, 252) if card1_is_dark else (28, 28, 28)
    card1_note_bg = (min(255, tag_bg[0] + 16), min(255, tag_bg[1] + 18), min(255, tag_bg[2] + 25), 250) if card1_is_dark else (255, 255, 255, 250)

    desc_lines = wrap_text(hero_text, fonts["body_bold"], content_width - 50, ov_draw)
    dy = card1_top + 78
    for d_line in desc_lines[:2]:
        ov_draw.text((margin_x + 24, dy), d_line, font=fonts["body_bold"], fill=card1_text_color)
        bb = ov_draw.textbbox((0, 0), d_line, font=fonts["body_bold"])
        dy += (bb[3] - bb[0]) + 6

    # Khung ghi chú ở đáy Thẻ 1 (tự động điều chỉnh theo nền sáng/tối)
    note_box_y = card1_top + card1_h - 48
    ov_draw.rounded_rectangle([(margin_x + 24, note_box_y), (width - margin_x - 24, note_box_y + 36)], radius=16, fill=card1_note_bg, outline=border_color, width=1)
    sub_note = ">> Căn cứ quy định mới nhất có hiệu lực thi hành từ năm 2026" if slide_num == 1 else (">> Ghi nhớ các mốc thời gian kê khai để tránh bị phạt chậm nộp" if slide_num == total_slides else f">> Chi tiết quy định áp dụng trong kỳ tính thuế {slide_num}")
    ov_draw.text((margin_x + 40, note_box_y + 9), sub_note, font=fonts["small"], fill=accent_color)

    # 4. THẺ DANH SÁCH CHI TIẾT (Thẻ 2 - List Container Card)
    card2_top = card1_top + card1_h + 20
    card2_bottom = height - 120
    ov_draw.rounded_rectangle([(margin_x, card2_top), (width - margin_x, card2_bottom)], radius=26, fill=card_bg, outline=border_color, width=2)

    tag2_text = "● KHUYẾN NGHỊ THỰC HIỆN" if slide_num == total_slides else "● ĐIỂM CỐT LÕI CẦN BIẾT"
    t2_bbox = ov_draw.textbbox((0, 0), tag2_text, font=fonts["badge"])
    tag2_w = (t2_bbox[2] - t2_bbox[0]) + 36
    ov_draw.rounded_rectangle([(margin_x + 28, card2_top + 22), (margin_x + 28 + tag2_w, card2_top + 62)], radius=18, fill=accent_color)
    ov_draw.text((margin_x + 46, card2_top + 32), tag2_text, font=fonts["badge"], fill=(255, 255, 255))

    list_bullets = bullets[1:] if len(bullets) > 1 else bullets
    bullet_y = card2_top + 95
    card_content_w = content_width - 80
    item_gap = 48 if len(list_bullets) <= 2 else (36 if len(list_bullets) <= 4 else 24)

    for idx, bullet in enumerate(list_bullets):
        if bullet_y >= card2_bottom - 60:
            break

        # Chấm tròn hồng phấn với tâm đỏ đô
        circle_r = 16
        c_x, c_y = margin_x + 45, bullet_y + 16
        ov_draw.ellipse([(c_x - circle_r, c_y - circle_r), (c_x + circle_r, c_y + circle_r)], fill=tag_bg, outline=accent_color, width=2)
        ov_draw.ellipse([(c_x - 5, c_y - 5), (c_x + 5, c_y + 5)], fill=accent_color)

        b_lines = wrap_text(bullet, fonts["body"], card_content_w - 55, ov_draw)
        for b_line in b_lines:
            if bullet_y >= card2_bottom - 45:
                break
            ov_draw.text((margin_x + 75, bullet_y), b_line, font=fonts["body"], fill=text_body_color)
            bb = ov_draw.textbbox((0, 0), b_line, font=fonts["body"])
            bullet_y += (bb[3] - bb[0]) + 14

        bullet_y += item_gap

    # 5. FOOTER AREA (Safe Zone TikTok)
    footer_y = height - 85
    if slide_num == total_slides:
        cta_text = "Bấm Follow kênh ngay để cập nhật chính sách thuế mới nhất!"
        ov_draw.rounded_rectangle([(margin_x, footer_y - 10), (width - margin_x, footer_y + 48)], radius=28, fill=accent_color)
        ov_draw.text((margin_x + 60, footer_y + 8), cta_text, font=fonts["badge"], fill=(255, 255, 255))
    else:
        ov_draw.text((margin_x + 10, footer_y + 10), "@thong_tin_ve_thue  ●  Tác nghiệp tự động", font=fonts["small"], fill=(120, 130, 145))
        swipe_text = "Vuốt sang để xem tiếp  >>"
        ov_draw.rounded_rectangle([(width - margin_x - 240, footer_y - 5), (width - margin_x, footer_y + 40)], radius=22, fill=tag_bg, outline=accent_color, width=1)
        ov_draw.text((width - margin_x - 225, footer_y + 7), swipe_text, font=fonts["badge"], fill=accent_color)

    final_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)
    return final_img.convert("RGB")


def generate_and_upload_slides(
    row_data: Dict[str, Any],
    row_index: int,
    preset_id: Optional[str] = None,
    drive_manager = None
) -> Dict[str, Any]:
    """
    Quy trình tạo ảnh slide và lưu trực tiếp lên Google Drive cùng thư mục file 'Nội dung Slide':
    1. Kiểm tra kịch bản & chọn preset
    2. Phân tích kịch bản thành N slide
    3. Tạo N hình ảnh 9:16
    4. Xác định thư mục Google Drive của chủ đề (cùng thư mục 'Nội dung Slide')
    5. Tải toàn bộ ảnh lên Google Drive (Slide_01.jpg, Slide_02.jpg...)
    """
    stt = str(row_data.get("STT") or (row_index + 1)).strip()
    chu_de = str(row_data.get("Chủ đề") or "").strip()
    noi_dung = str(row_data.get("Nội dung") or "").strip()

    if not noi_dung:
        return {"success": False, "message": "Nội dung kịch bản đang trống! Vui lòng tạo nội dung trước."}

    # Preset
    preset = get_preset_by_id(preset_id or "")
    if not preset:
        preset = {
            "name": "Infographic Hiện Đại",
            "description": "Infographic 9:16 tiêu chuẩn",
            "instruction": "Tỷ lệ 9:16, màu sắc cam đất và trắng"
        }

    # Phân tích slides
    slides_info = parse_script_to_slides(noi_dung)
    if not slides_info:
        return {"success": False, "message": "Không thể phân tích nội dung kịch bản thành các slide."}

    total_slides = len(slides_info)
    print(f"[SlideGen] Bắt đầu tạo {total_slides} slides cho chủ đề: '{chu_de}' với preset '{preset.get('name')}'...")

    # Tạo thư mục local lưu ảnh
    safe_topic = re.sub(r'[\\/*?:"<>|]', '_', f"{stt}_{chu_de}").strip().replace(' ', '_')[:60]
    local_topic_dir = os.path.join(OUTPUT_DIR, safe_topic)
    os.makedirs(local_topic_dir, exist_ok=True)

    generated_slides = []
    
    for idx, s_info in enumerate(slides_info, start=1):
        try:
            img = generate_slide_image(
                slide_info=s_info,
                total_slides=total_slides,
                chu_de=chu_de,
                preset=preset,
                width=1080,
                height=1350
            )

            filename = f"Slide_{idx:02d}.jpg"
            local_filepath = os.path.join(local_topic_dir, filename)
            img.save(local_filepath, format="JPEG", quality=92)

            generated_slides.append({
                "slide_num": idx,
                "title": s_info.get("title", f"Slide {idx}"),
                "slide_type": s_info.get("slide_type", ""),
                "filename": filename,
                "local_path": local_filepath,
                "local_url": f"/static/generated_slides/{safe_topic}/{filename}",
                "drive_url": None,
                "drive_file_id": None
            })
            print(f"[SlideGen] Đã tạo xong local slide {idx}/{total_slides}: {filename}")
        except Exception as e:
            print(f"[SlideGen] Lỗi tạo slide {idx}: {e}")

    # 4. TẢI TOÀN BỘ ẢNH LÊN GOOGLE DRIVE TRONG CÙNG THƯ MỤC VỚI FILE 'NỘI DUNG SLIDE'
    folder_id = None
    folder_url = None
    uploaded_count = 0

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

            # Tên thư mục theo quy chuẩn: '{stt} {tóm tắt / chủ đề}'
            # Tìm thư mục chứa file 'Nội dung Slide' của dòng này
            query_folder = f"'{parent_folder_id}' in parents and (name contains '{stt} ') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_folders = drive_manager.drive_service.files().list(
                q=query_folder,
                fields="files(id, name, webViewLink)"
            ).execute().get("files", [])

            if res_folders:
                folder_id = res_folders[0].get("id")
                folder_url = res_folders[0].get("webViewLink")
            else:
                # Nếu chưa có thì tạo thư mục mới
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', f"{stt} {chu_de}").strip()
                meta = {
                    "name": clean_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_folder_id]
                }
                new_f = drive_manager.drive_service.files().create(body=meta, fields="id, name, webViewLink").execute()
                folder_id = new_f.get("id")
                folder_url = new_f.get("webViewLink")

            print(f"[SlideGen] Đang tải {len(generated_slides)} ảnh lên Drive Folder: {folder_id} ({folder_url})...")

            # Upload từng file ảnh vào thư mục Drive này
            for s in generated_slides:
                fname = s["filename"]
                lpath = s["local_path"]

                # Kiểm tra nếu file đã tồn tại trên Drive thì update, nếu chưa thì create
                existing_f = drive_manager.drive_service.files().list(
                    q=f"'{folder_id}' in parents and name = '{fname}' and trashed = false",
                    fields="files(id, name, webViewLink)"
                ).execute().get("files", [])

                with open(lpath, "rb") as img_file:
                    media = MediaIoBaseUpload(io.BytesIO(img_file.read()), mimetype="image/jpeg", resumable=True)

                if existing_f:
                    f_id = existing_f[0]["id"]
                    up_file = drive_manager.drive_service.files().update(
                        fileId=f_id,
                        media_body=media,
                        fields="id, name, webViewLink"
                    ).execute()
                    s["drive_url"] = up_file.get("webViewLink")
                    s["drive_file_id"] = up_file.get("id")
                else:
                    meta = {
                        "name": fname,
                        "parents": [folder_id]
                    }
                    new_file = drive_manager.drive_service.files().create(
                        body=meta,
                        media_body=media,
                        fields="id, name, webViewLink"
                    ).execute()
                    s["drive_url"] = new_file.get("webViewLink")
                    s["drive_file_id"] = new_file.get("id")

                uploaded_count += 1
                print(f"[SlideGen] Đã tải lên Drive: {fname} -> {s.get('drive_url')}")

        except Exception as e:
            print(f"[SlideGen] Lỗi upload Drive: {e}")

    return {
        "success": True,
        "message": f"Đã tạo thành công {len(generated_slides)} slide hình ảnh và lưu vào Google Drive!",
        "total_slides": len(generated_slides),
        "preset_name": preset.get("name"),
        "folder_id": folder_id,
        "folder_url": folder_url,
        "slides": generated_slides
    }
