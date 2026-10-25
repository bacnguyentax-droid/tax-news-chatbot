#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trình tạo ảnh Slide / Infographic bằng Python (Pillow)
Định dạng xuất chuẩn Full HD (1080 x 1920) tỷ lệ 9:16 hoặc tùy biến
Tương thích 100% với mẫu Slide Thuế & Tin tức mạng xã hội
"""

import os
import re
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_font(font_name="segoe", size=32, bold=False):
    """Tìm font tiếng Việt trên hệ thống Windows hoặc fallback"""
    windows_fonts = "C:/Windows/Fonts"
    candidates = []
    
    if bold:
        candidates = [
            os.path.join(windows_fonts, "segoeuib.ttf"),
            os.path.join(windows_fonts, "arialbd.ttf"),
            os.path.join(windows_fonts, "calibrib.ttf"),
            os.path.join(windows_fonts, "tahomabd.ttf")
        ]
    else:
        candidates = [
            os.path.join(windows_fonts, "segoeui.ttf"),
            os.path.join(windows_fonts, "arial.ttf"),
            os.path.join(windows_fonts, "calibri.ttf"),
            os.path.join(windows_fonts, "tahoma.ttf")
        ]
        
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
                
    return ImageFont.load_default()


def draw_pill_badge(draw, text, x, y, font, text_color, bg_color, border_color, padding_x=28, padding_y=12):
    """Vẽ huy hiệu bo tròn (Pill Badge)"""
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    total_w = text_w + padding_x * 2
    total_h = text_h + padding_y * 2
    
    rect_x0 = x - total_w // 2
    rect_y0 = y - total_h // 2
    rect_x1 = rect_x0 + total_w
    rect_y1 = rect_y0 + total_h
    
    radius = total_h // 2
    
    # Vẽ nền pill
    draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=radius, fill=bg_color, outline=border_color, width=2)
    
    # Vẽ chữ
    text_x = rect_x0 + padding_x - bbox[0]
    text_y = rect_y0 + padding_y - bbox[1]
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return total_h


def draw_prohibition_icon(draw, cx, cy, radius=24, color=(143, 21, 43), width=6):
    """Vẽ biểu tượng cấm 🚫 dạng vector sắc nét"""
    import math
    # Đường tròn ngoài
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=color, width=width)
    # Đường gạch chéo 45 độ
    offset = int(radius * 0.707)  # cos(45)
    draw.line([cx - offset, cy - offset, cx + offset, cy + offset], fill=color, width=width)


def draw_bullet_paragraph(draw, lines_tokens, x, y, max_w, font_normal, font_bold, normal_color, bold_color, bullet_color, line_spacing=18):
    """Vẽ gạch đầu dòng có chứa từ khóa in đậm màu đỏ"""
    bullet_r = 6
    bullet_cx = x + 10
    bullet_cy = y + 18
    draw.ellipse([bullet_cx - bullet_r, bullet_cy - bullet_r, bullet_cx + bullet_r, bullet_cy + bullet_r], fill=bullet_color)
    
    text_start_x = x + 36
    curr_x = text_start_x
    curr_y = y
    
    # Token format: list of (word, is_bold)
    for line in lines_tokens:
        for word, is_bold in line:
            f = font_bold if is_bold else font_normal
            c = bold_color if is_bold else normal_color
            draw.text((curr_x, curr_y), word + " ", fill=c, font=f)
            w = draw.textlength(word + " ", font=f)
            curr_x += w
        curr_x = text_start_x
        curr_y += font_normal.size + line_spacing
        
    return curr_y


def wrap_tokens(tokens, max_w, font_normal, font_bold):
    """Gói dòng các tokens (từ khóa) vừa vặn với chiều rộng card"""
    lines = []
    current_line = []
    current_line_w = 0
    
    for word, is_bold in tokens:
        f = font_bold if is_bold else font_normal
        word_w = f.getlength(word + " ")
        if current_line_w + word_w > max_w and current_line:
            lines.append(current_line)
            current_line = [(word, is_bold)]
            current_line_w = word_w
        else:
            current_line.append((word, is_bold))
            current_line_w += word_w
            
    if current_line:
        lines.append(current_line)
        
    return lines


def parse_bullet_tokens(text):
    """Tách chuỗi thành các tokens (chữ thường hoặc in đậm **)"""
    tokens = []
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            inner = p[2:-2]
            for w in inner.split():
                tokens.append((w, True))
        else:
            for w in p.split():
                tokens.append((w, False))
    return tokens


def auto_highlight_keywords(text):
    """Tự động phát hiện và đánh dấu từ khóa nếu người dùng chưa dùng **...**"""
    if "**" in text:
        return text
    keywords = [
        "thuế khoán định mức",
        "thuế khoán",
        "tự khai - tự tính - tự nộp thuế",
        "tự khai, tự nộp",
        "hóa đơn điện tử và dòng tiền ngân hàng",
        "hóa đơn điện tử",
        "dòng tiền ngân hàng",
        "khoán tượng trưng",
        "truy cứu trách nhiệm hình sự",
        "máy tính tiền",
        "doanh thu thực tế",
        "giảm trừ gia cảnh",
        "trốn thuế"
    ]
    res = text
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        res = pattern.sub(f"**{kw}**", res)
    return res


def parse_raw_slide_text(raw_text):
    """Phân tích đoạn văn bản thô thành các trường dữ liệu"""
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    header_tag = "CHÍNH SÁCH THUẾ HỘ KINH DOANH • SLIDE 02/08"
    has_prohibition_icon = False
    title = ""
    footer_tag = "THÔNG TIN VỀ THUẾ • CHÍNH THỨC"
    bullets = []
    
    for line in lines:
        if re.match(r"^SLIDE\s*\d+[:.\s]", line, re.IGNORECASE):
            match = re.search(r"^SLIDE\s*(\d+)[:.\s]*(.*)", line, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                topic = match.group(2).strip() or "CHÍNH SÁCH THUẾ"
                header_tag = f"{topic.upper()} • SLIDE {num:02d}/08"
            continue
            
        if re.match(r"^(?:Tiêu đề|Title|TIÊU ĐỀ)[:.\s]", line, re.IGNORECASE):
            raw_title = re.sub(r"^(?:Tiêu đề|Title|TIÊU ĐỀ)[:.\s]*", "", line, flags=re.IGNORECASE).strip()
            if "🚫" in raw_title:
                has_prohibition_icon = True
                raw_title = raw_title.replace("🚫", "").strip()
            # Chia dòng tại dấu phẩy nếu hợp lý
            if "," in raw_title and "\n" not in raw_title:
                parts = raw_title.split(",")
                title = parts[0].strip() + ",\n" + parts[1].strip()
            else:
                title = raw_title
            continue
            
        if re.match(r"^(?:Nội dung|Content|NỘI DUNG)[:.\s]*$", line, flags=re.IGNORECASE):
            continue
            
        # Dòng nội dung
        clean_line = re.sub(r"^[-•*+–—]\s*", "", line)
        clean_line = re.sub(r"^\d+[\.\)]\s*", "", clean_line).strip()
        if clean_line:
            clean_line = auto_highlight_keywords(clean_line)
            bullets.append(clean_line)
            
    if not title and lines:
        title = lines[0]
        
    return {
        "header_tag": header_tag,
        "title": title or "XÓA BỎ THUẾ KHOÁN,\nCHUYỂN SANG TỰ KÊ KHAI",
        "has_prohibition_icon": has_prohibition_icon or True,
        "footer_tag": footer_tag,
        "bullets": bullets if bullets else [
            "Bãi bỏ hoàn toàn hình thức **thuế khoán định mức** cố định hàng năm.",
            "Hộ kinh doanh chuyển sang **tự khai - tự tính - tự nộp thuế** theo doanh thu thực tế.",
            "Dữ liệu kinh doanh được kiểm soát chặt qua **hóa đơn điện tử và dòng tiền ngân hàng**.",
            "Chấm dứt tình trạng \"khoán tượng trưng\" đối với các cơ sở kinh doanh quy mô lớn."
        ]
    }


def create_slide_image(
    header_tag="CHÍNH SÁCH THUẾ HỘ KINH DOANH • SLIDE 02/08",
    title="XÓA BỎ THUẾ KHOÁN,\nCHUYỂN SANG TỰ KÊ KHAI",
    has_prohibition_icon=True,
    bullets=None,
    footer_tag="THÔNG TIN VỀ THUẾ • CHÍNH THỨC",
    output_path="output_slide.png",
    width=1080,
    height=1920
):
    if bullets is None:
        bullets = [
            "Bãi bỏ hoàn toàn hình thức **thuế khoán định mức** cố định hàng năm.",
            "Hộ kinh doanh chuyển sang **tự khai - tự tính - tự nộp thuế** theo doanh thu thực tế.",
            "Dữ liệu kinh doanh được kiểm soát chặt qua **hóa đơn điện tử và dòng tiền ngân hàng**.",
            "Chấm dứt tình trạng \"khoán tượng trưng\" đối với các cơ sở kinh doanh quy mô lớn."
        ]
        
    # Tạo ảnh nền
    base_color = (252, 249, 249)
    img = Image.new("RGB", (width, height), base_color)
    
    # Tạo vầng hào quang hồng phấn (Ambient glows)
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    
    # Glow góc trên bên phải
    glow_draw.ellipse([width - 500, -200, width + 500, 800], fill=(255, 195, 205, 110))
    # Glow góc dưới bên phải
    glow_draw.ellipse([width - 450, height - 700, width + 450, height + 200], fill=(255, 205, 215, 95))
    # Glow góc trái
    glow_draw.ellipse([-300, 200, 400, 900], fill=(255, 240, 245, 80))
    
    # Làm mờ hào quang
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(120))
    img.paste(glow_layer, (0, 0), glow_layer)
    
    draw = ImageDraw.Draw(img)
    
    # Bảng màu chuẩn
    primary_color = (143, 21, 43)      # #8f152b - Đỏ rượu vang
    primary_light = (255, 240, 243)    # Nền pill badge
    primary_border = (225, 175, 185)   # Viền pill badge
    card_bg = (255, 255, 255)          # Trắng tinh
    text_dark = (44, 48, 56)           # Xám than đậm
    
    # 1. Huy hiệu đầu trang (Header Badge)
    font_badge = get_font("segoe", size=26, bold=True)
    badge_y = 280
    draw_pill_badge(
        draw, header_tag, 
        x=width // 2, y=badge_y, 
        font=font_badge, 
        text_color=primary_color, 
        bg_color=primary_light, 
        border_color=primary_border, 
        padding_x=36, padding_y=14
    )
    
    # 2. Tiêu đề chính & Icon cấm 🚫
    font_title = get_font("segoe", size=48, bold=True)
    title_lines = [l.strip() for l in title.split("\n") if l.strip()]
    title_y = badge_y + 75
    
    # Tính toán căn giữa nếu có icon 🚫
    icon_radius = 24
    icon_gap = 16
    
    first_line = title_lines[0] if title_lines else ""
    first_line_w = draw.textlength(first_line, font=font_title)
    
    if has_prohibition_icon:
        total_first_line_w = (icon_radius * 2) + icon_gap + first_line_w
        start_x = (width - total_first_line_w) // 2
        
        # Vẽ icon cấm
        icon_cx = start_x + icon_radius
        icon_cy = title_y + (font_title.size // 2) + 2
        draw_prohibition_icon(draw, icon_cx, icon_cy, radius=icon_radius, color=primary_color, width=6)
        
        # Vẽ dòng đầu
        text_x = start_x + (icon_radius * 2) + icon_gap
        draw.text((text_x, title_y), first_line, fill=primary_color, font=font_title)
    else:
        draw.text(((width - first_line_w) // 2, title_y), first_line, fill=primary_color, font=font_title)
        
    title_y += font_title.size + 14
    
    # Vẽ các dòng tiêu đề còn lại
    for line in title_lines[1:]:
        line_w = draw.textlength(line, font=font_title)
        draw.text(((width - line_w) // 2, title_y), line, fill=primary_color, font=font_title)
        title_y += font_title.size + 14
        
    # 3. Thẻ trắng (White Card)
    card_w = int(width * 0.88)
    card_x0 = (width - card_w) // 2
    card_x1 = card_x0 + card_w
    card_y0 = title_y + 40
    card_y1 = card_y0 + 740
    
    # Tạo bóng đổ cho thẻ trắng
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        [card_x0, card_y0 + 15, card_x1, card_y1 + 25], 
        radius=50, 
        fill=(170, 30, 50, 25)
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(30))
    img.paste(shadow_layer, (0, 0), shadow_layer)
    
    # Vẽ thẻ trắng
    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1], 
        radius=50, 
        fill=card_bg, 
        outline=(245, 230, 235), 
        width=2
    )
    
    # 4. Nội dung gạch đầu dòng bên trong thẻ
    font_body = get_font("segoe", size=33, bold=False)
    font_body_bold = get_font("segoe", size=33, bold=True)
    
    content_padding_x = 55
    content_max_w = card_w - (content_padding_x * 2) - 45
    
    # Tính toán chiều cao các ý để căn giữa trong thẻ
    bullet_blocks = []
    total_content_h = 0
    spacing_between_bullets = 40
    
    for b_text in bullets:
        tokens = parse_bullet_tokens(b_text)
        lines = wrap_tokens(tokens, content_max_w, font_body, font_body_bold)
        h = len(lines) * (font_body.size + 18)
        bullet_blocks.append((lines, h))
        total_content_h += h
        
    total_content_h += spacing_between_bullets * (len(bullets) - 1)
    
    # Bắt đầu vẽ từ trên xuống
    start_content_y = card_y0 + (card_y1 - card_y0 - total_content_h) // 2
    curr_y = start_content_y
    
    for lines, block_h in bullet_blocks:
        draw_bullet_paragraph(
            draw, lines, 
            x=card_x0 + content_padding_x, 
            y=curr_y, 
            max_w=content_max_w, 
            font_normal=font_body, 
            font_bold=font_body_bold, 
            normal_color=text_dark, 
            bold_color=primary_color, 
            bullet_color=primary_color, 
            line_spacing=18
        )
        curr_y += block_h + spacing_between_bullets
        
    # 5. Nút chân trang (Footer Pill)
    footer_y = card_y1 + 65
    font_footer = get_font("segoe", size=26, bold=True)
    draw_pill_badge(
        draw, footer_tag, 
        x=width // 2, y=footer_y, 
        font=font_footer, 
        text_color=(255, 255, 255), 
        bg_color=primary_color, 
        border_color=(125, 16, 37), 
        padding_x=45, padding_y=16
    )
    
    # Lưu file
    img.save(output_path, quality=95)
    print(f"✅ Đã tạo ảnh slide thành công: {output_path} ({width}x{height})")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Tạo ảnh Infographic / Slide")
    parser.add_argument("--raw", type=str, default=None, help="Nội dung thô của slide (tiêu đề, nội dung...)")
    parser.add_argument("--file", type=str, default=None, help="Đường dẫn file văn bản chứa nội dung")
    parser.add_argument("--header", default="CHÍNH SÁCH THUẾ HỘ KINH DOANH • SLIDE 02/08", help="Huy hiệu đầu trang")
    parser.add_argument("--title", default="XÓA BỎ THUẾ KHOÁN,\nCHUYỂN SANG TỰ KÊ KHAI", help="Tiêu đề slide")
    parser.add_argument("--footer", default="THÔNG TIN VỀ THUẾ • CHÍNH THỨC", help="Thẻ chân trang")
    parser.add_argument("--output", default="slide_output.png", help="Đường dẫn file ảnh đầu ra")
    
    args = parser.parse_args()
    
    raw_content = None
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            raw_content = f.read()
    elif args.raw:
        raw_content = args.raw
        
    if raw_content:
        parsed = parse_raw_slide_text(raw_content)
        create_slide_image(
            header_tag=parsed["header_tag"],
            title=parsed["title"],
            has_prohibition_icon=parsed["has_prohibition_icon"],
            bullets=parsed["bullets"],
            footer_tag=parsed["footer_tag"],
            output_path=args.output
        )
    else:
        create_slide_image(
            header_tag=args.header,
            title=args.title,
            bullets=None,
            footer_tag=args.footer,
            output_path=args.output
        )


if __name__ == "__main__":
    main()
