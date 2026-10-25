import os
import sys
import io
import re
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký font tiếng Việt từ Windows Fonts
FONT_DIR = r"C:\Windows\Fonts"
TIMES_REG = os.path.join(FONT_DIR, "times.ttf")
TIMES_BOLD = os.path.join(FONT_DIR, "timesbd.ttf")
TIMES_ITALIC = os.path.join(FONT_DIR, "timesi.ttf")
TIMES_BI = os.path.join(FONT_DIR, "timesbi.ttf")

try:
    if os.path.exists(TIMES_REG):
        pdfmetrics.registerFont(TTFont('TimesVN', TIMES_REG))
    if os.path.exists(TIMES_BOLD):
        pdfmetrics.registerFont(TTFont('TimesVN-Bold', TIMES_BOLD))
    if os.path.exists(TIMES_ITALIC):
        pdfmetrics.registerFont(TTFont('TimesVN-Italic', TIMES_ITALIC))
    if os.path.exists(TIMES_BI):
        pdfmetrics.registerFont(TTFont('TimesVN-BoldItalic', TIMES_BI))
except Exception as e:
    pass

def xml_escape(text: str) -> str:
    """Escape XML special characters for ReportLab Paragraphs safely"""
    if not text:
        return ""
    text = str(text)
    # Don't double escape already escaped entities
    text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', text)
    # Escape < and > if they don't form valid formatting tags
    parts = re.split(r'(</?(?:b|i|u|font(?:\s+[^>]+)?)>)', text)
    escaped_parts = []
    for part in parts:
        if re.match(r'^</?(?:b|i|u|font(?:\s+[^>]+)?)>$', part):
            escaped_parts.append(part)
        else:
            p = part.replace('<', '&lt;').replace('>', '&gt;')
            escaped_parts.append(p)
    return ''.join(escaped_parts)

class PDFGenerator:
    @staticmethod
    def generate_document_pdf(doc_info: Dict[str, Any]) -> bytes:
        """
        Tạo file PDF văn bản pháp luật chính thức chuẩn thể thức văn bản hành chính Việt Nam
        (theo Nghị định 30/2020/NĐ-CP của Chính phủ).
        Bao gồm Quốc hiệu, Tiêu ngữ, Cơ quan ban hành, Số hiệu, Trích yếu, Căn cứ pháp lý,
        và Toàn văn đầy đủ các Chương, Điều, Khoản quy định chi tiết.
        Đảm bảo TUYỆT ĐỐI KHÔNG lặp lại tiêu đề, quốc hiệu hay số hiệu hai lần.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2.0 * cm,
            rightMargin=1.5 * cm,
            topMargin=2.0 * cm,
            bottomMargin=2.0 * cm
        )

        font_name = 'TimesVN' if 'TimesVN' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        font_bold = 'TimesVN-Bold' if 'TimesVN-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        font_italic = 'TimesVN-Italic' if 'TimesVN-Italic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Oblique'
        font_bi = 'TimesVN-BoldItalic' if 'TimesVN-BoldItalic' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'

        # Định nghĩa các style chuẩn văn bản hành chính
        header_agency_style = ParagraphStyle(
            'HeaderAgency',
            fontName=font_bold,
            fontSize=11,
            leading=14,
            alignment=1, # Center
            textColor=colors.HexColor('#002e5b')
        )

        doc_num_style = ParagraphStyle(
            'DocNum',
            fontName=font_name,
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=colors.HexColor('#1e293b')
        )

        motto_title_style = ParagraphStyle(
            'MottoTitle',
            fontName=font_bold,
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor('#0f172a')
        )

        motto_sub_style = ParagraphStyle(
            'MottoSub',
            fontName=font_bold,
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor('#0f172a')
        )

        date_style = ParagraphStyle(
            'DocDate',
            fontName=font_italic,
            fontSize=10.5,
            leading=14,
            alignment=1,
            textColor=colors.HexColor('#334155')
        )

        doc_type_style = ParagraphStyle(
            'DocType',
            fontName=font_bold,
            fontSize=15,
            leading=19,
            alignment=1,
            textColor=colors.HexColor('#002e5b')
        )

        summary_style = ParagraphStyle(
            'DocSummary',
            fontName=font_bold,
            fontSize=11.5,
            leading=16,
            alignment=1,
            textColor=colors.HexColor('#0f172a')
        )

        legal_basis_style = ParagraphStyle(
            'LegalBasis',
            fontName=font_italic,
            fontSize=10.5,
            leading=15,
            alignment=4, # Justify
            firstLineIndent=1.0 * cm,
            textColor=colors.HexColor('#334155'),
            spaceAfter=3
        )

        recipient_style = ParagraphStyle(
            'DocRecipient',
            fontName=font_bold,
            fontSize=11,
            leading=16,
            alignment=4,
            leftIndent=1.0 * cm,
            textColor=colors.HexColor('#002e5b'),
            spaceBefore=6,
            spaceAfter=4
        )

        recipient_sub_style = ParagraphStyle(
            'DocRecipientSub',
            fontName=font_italic,
            fontSize=10.5,
            leading=15,
            alignment=4,
            leftIndent=1.5 * cm,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=3
        )

        chapter_heading = ParagraphStyle(
            'ChapterHeading',
            fontName=font_bold,
            fontSize=12,
            leading=16,
            alignment=1, # Center
            textColor=colors.HexColor('#002e5b'),
            spaceBefore=12,
            spaceAfter=6
        )

        article_heading = ParagraphStyle(
            'ArticleHeading',
            fontName=font_bold,
            fontSize=11,
            leading=15,
            alignment=4, # Justify
            textColor=colors.HexColor('#003b73'),
            firstLineIndent=1.0 * cm,
            spaceBefore=8,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'DocBody',
            fontName=font_name,
            fontSize=11,
            leading=16,
            alignment=4, # Justify
            firstLineIndent=1.0 * cm,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=5
        )

        sub_item_style = ParagraphStyle(
            'SubItem',
            fontName=font_name,
            fontSize=10.5,
            leading=15,
            alignment=4,
            leftIndent=1.5 * cm,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4
        )

        footer_text = ParagraphStyle(
            'FooterText',
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569')
        )

        story = []

        # ================= 1. TIÊU ĐỀ ĐẦU TRANG (2 CỘT CHUẨN THỂ THỨC VN) =================
        issuing_body = (doc_info.get("issuing_body") or "CƠ QUAN BAN HÀNH").upper()
        doc_number = (doc_info.get("doc_number") or "").strip()
        issue_date = (doc_info.get("issue_date") or "").strip()

        # Tách địa danh và ngày
        date_str = f"Hà Nội, ngày {issue_date}" if issue_date else "Hà Nội, ngày ... tháng ... năm 2026"

        left_cell = [
            Paragraph(f"<b>{xml_escape(issuing_body)}</b>", header_agency_style),
            Paragraph(f"Số: {xml_escape(doc_number)}", doc_num_style),
            Spacer(1, 3),
            HRFlowable(width="35%", thickness=0.8, color=colors.HexColor('#004b93'), hAlign='CENTER')
        ]

        right_cell = [
            Paragraph("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", motto_title_style),
            Paragraph("Độc lập - Tự do - Hạnh phúc", motto_sub_style),
            Spacer(1, 2),
            HRFlowable(width="55%", thickness=0.8, color=colors.HexColor('#0f172a'), hAlign='CENTER'),
            Spacer(1, 4),
            Paragraph(date_str, date_style)
        ]

        header_table = Table([[left_cell, right_cell]], colWidths=[8.0 * cm, 9.5 * cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 16))

        # ================= 2. TÊN LOẠI VĂN BẢN VÀ TRÍCH YẾU =================
        doc_type = (doc_info.get("doc_type") or "VĂN BẢN").upper()
        title_text = (doc_info.get("title") or "").strip()
        summary_text = (doc_info.get("summary") or "").strip()

        story.append(Paragraph(xml_escape(doc_type), doc_type_style))
        story.append(Spacer(1, 6))

        # Trích yếu nội dung
        story.append(Paragraph(xml_escape(title_text), summary_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="25%", thickness=1.0, color=colors.HexColor('#004b93'), hAlign='CENTER'))
        story.append(Spacer(1, 14))

        # ================= 3. BẢNG THÔNG TIN HIỆU LỰC & LĨNH VỰC =================
        field = doc_info.get("field", "Thuế")
        effective_date = doc_info.get("effective_date", issue_date or "Theo quy định")
        signer_title = doc_info.get("signer_title", "Thủ trưởng đơn vị")
        signer_name = doc_info.get("signer_name", "")

        info_data = [
            [
                Paragraph(f"<b>Lĩnh vực:</b> {xml_escape(field)}", ParagraphStyle('P1', fontName=font_name, fontSize=9, leading=12)),
                Paragraph(f"<b>Ngày ban hành:</b> {xml_escape(issue_date)}", ParagraphStyle('P2', fontName=font_name, fontSize=9, leading=12)),
                Paragraph(f"<b>Hiệu lực từ:</b> {xml_escape(effective_date)}", ParagraphStyle('P3', fontName=font_name, fontSize=9, leading=12))
            ]
        ]
        info_table = Table(info_data, colWidths=[6.0 * cm, 5.5 * cm, 6.0 * cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f5fa')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#b9d2ec')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d4e3f5')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 14))

        # ================= 4. XỬ LÝ VÀ LÀM SẠCH NỘI DUNG VĂN BẢN =================
        raw_content = (doc_info.get("content") or "").strip()
        if not raw_content or raw_content == title_text:
            raw_content = summary_text

        # Loại bỏ các dòng tiêu đề hành chính bị trùng lặp ở đầu văn bản (Header stripping)
        raw_lines = raw_content.split("\n")
        cleaned_lines = []
        in_header = True

        header_patterns = [
            r'^\s*cộng\s+hòa\s+xã\s+hội\s+chủ\s+nghĩa\s+việt\s+nam\s*$',
            r'^\s*độc\s+lập\s*[-–—]\s*tự\s+do\s*[-–—]\s*hạnh\s+phúc\s*$',
            r'^\s*[-–—_=\*\.]{3,}\s*$',
            r'^\s*số\s*:\s*.*$',
            r'^\s*(?:hà\s+nội|tp\.?|thành\s+phố|tỉnh)\s*.*,\s*ngày.*$',
        ]

        for line in raw_lines:
            line_str = line.strip()
            if not line_str:
                continue

            if in_header:
                is_hdr = False
                for pat in header_patterns:
                    if re.match(pat, line_str, re.IGNORECASE):
                        is_hdr = True
                        break
                # Trùng cơ quan ban hành
                if not is_hdr and issuing_body and line_str.upper() == issuing_body.upper():
                    is_hdr = True
                if not is_hdr and any(line_str.upper().startswith(x) for x in ["TỔNG CỤC THUẾ", "BỘ TÀI CHÍNH", "NGÂN HÀNG NHÀ NƯỚC", "BỘ XÂY DỰNG", "CHÍNH PHỦ", "QUỐC HỘI"]):
                    is_hdr = True
                # Trùng số hiệu văn bản
                if not is_hdr and doc_number and doc_number.lower() in line_str.lower() and len(line_str) < len(doc_number) + 15:
                    is_hdr = True
                # Trùng tiêu đề văn bản
                if not is_hdr and (line_str.upper() == title_text.upper() or (len(line_str) > 20 and line_str.lower() in title_text.lower() and len(line_str) > len(title_text) * 0.8)):
                    is_hdr = True
                if not is_hdr and (line_str.upper().startswith("V/V ") or line_str.upper().startswith("V/V: ")) and len(line_str) < 140:
                    is_hdr = True

                if is_hdr:
                    continue
                else:
                    in_header = False

            cleaned_lines.append(line_str)

        # Tách Nơi nhận (nếu có ở cuối nội dung) để đưa vào bảng chữ ký, tránh hiển thị trùng lặp
        body_lines = []
        custom_recipients = []
        in_recipients = False

        for line_str in cleaned_lines:
            if re.match(r'^(?:NƠI NHẬN|Nơi nhận)\s*:', line_str, re.IGNORECASE):
                in_recipients = True
                continue
            if in_recipients:
                if line_str.startswith("-") or line_str.startswith("+"):
                    custom_recipients.append(line_str)
                elif re.match(r'^[A-Z\s]{4,}$', line_str) and not line_str.startswith("-"):
                    break
                else:
                    custom_recipients.append(line_str)
            else:
                body_lines.append(line_str)

        # ================= 5. NỘI DUNG VĂN BẢN ĐẦY ĐỦ =================
        in_kinh_gui = False

        for line_str in body_lines:
            # Phát hiện Kính gửi
            if re.match(r'^(?:Kính gửi|KÍNH GỬI)\s*:', line_str, re.IGNORECASE):
                in_kinh_gui = True
                story.append(Paragraph(f"<b><i>{xml_escape(line_str)}</i></b>", recipient_style))
                continue

            if in_kinh_gui:
                if line_str.startswith("-") or line_str.startswith("+") or line_str.endswith(";"):
                    story.append(Paragraph(f"<i>{xml_escape(line_str)}</i>", recipient_sub_style))
                    continue
                else:
                    in_kinh_gui = False

            # Phát hiện Căn cứ pháp lý
            if re.match(r'^(?:[0-9]+\.\s+)?(?:Căn cứ|căn cứ)', line_str):
                story.append(Paragraph(f"<i>{xml_escape(line_str)}</i>", legal_basis_style))
                continue

            # Phát hiện Phần / Mục lớn (I., II., III...)
            if re.match(r'^[IVXLCDM]+\.\s+', line_str):
                story.append(Paragraph(f"<b>{xml_escape(line_str.upper())}</b>", chapter_heading))
                continue

            # Phát hiện Chương (Chương I, Chương II...)
            if re.match(r'^(?:Chương|CHƯƠNG)\s+[IVXLCDM0-9]+', line_str, re.IGNORECASE):
                story.append(Paragraph(f"<b>{xml_escape(line_str.upper())}</b>", chapter_heading))
                continue

            # Phát hiện Mục (Mục 1, Mục 2...)
            if re.match(r'^(?:Mục|MỤC)\s+[0-9IVXLCDM]+', line_str, re.IGNORECASE):
                story.append(Paragraph(f"<b>{xml_escape(line_str)}</b>", chapter_heading))
                continue

            # Phát hiện Điều (Điều 1, Điều 2...)
            if re.match(r'^(?:Điều|ĐIỀU)\s+[0-9]+[\.\:]', line_str, re.IGNORECASE):
                story.append(Paragraph(f"<b>{xml_escape(line_str)}</b>", article_heading))
                continue

            # Phát hiện Khoản số (1. , 2. , 3. ...)
            if re.match(r'^[0-9]+\.\s+', line_str):
                story.append(Paragraph(xml_escape(line_str), body_style))
                continue

            # Phát hiện Điểm (a), b), c) hoặc - )
            if re.match(r'^(?:[a-z]\)|\-|\+)\s+', line_str):
                story.append(Paragraph(xml_escape(line_str), sub_item_style))
                continue

            # Các đoạn văn thông thường
            story.append(Paragraph(xml_escape(line_str), body_style))

        story.append(Spacer(1, 20))

        # ================= 6. NƠI NHẬN VÀ CHỮ KÝ =================
        if custom_recipients:
            footer_left = [Paragraph("<b><i>Nơi nhận:</i></b>", footer_text)]
            for rec in custom_recipients[:6]:
                footer_left.append(Paragraph(xml_escape(rec), footer_text))
        else:
            footer_left = [Paragraph("<b><i>Nơi nhận:</i></b>", footer_text)]
            iss_low = issuing_body.lower()
            if "ngân hàng" in iss_low or "nhnn" in iss_low:
                footer_left.extend([
                    Paragraph("- Thống đốc NHNN (để báo cáo);", footer_text),
                    Paragraph("- Các TCTD, chi nhánh NH nước ngoài;", footer_text),
                    Paragraph("- NHNN chi nhánh các tỉnh, TP;", footer_text),
                    Paragraph("- Cổng TTĐT Ngân hàng Nhà nước;", footer_text),
                    Paragraph("- Lưu: VT, CSTT, TTGSNH.", footer_text)
                ])
            elif "xây dựng" in iss_low or "bxd" in iss_low:
                footer_left.extend([
                    Paragraph("- Bộ trưởng Bộ Xây dựng (để báo cáo);", footer_text),
                    Paragraph("- UBND các tỉnh, thành phố;", footer_text),
                    Paragraph("- Các Sở Xây dựng địa phương;", footer_text),
                    Paragraph("- Cổng TTĐT Bộ Xây dựng;", footer_text),
                    Paragraph("- Lưu: VT, QHKT, QLN.", footer_text)
                ])
            elif "chứng khoán" in iss_low or "ubck" in iss_low:
                footer_left.extend([
                    Paragraph("- Bộ Tài chính (để báo cáo);", footer_text),
                    Paragraph("- SGDCK Việt Nam, VNX, VSDC;", footer_text),
                    Paragraph("- Các Công ty chứng khoán, CTQL Quỹ;", footer_text),
                    Paragraph("- Cổng TTĐT UBCKNN;", footer_text),
                    Paragraph("- Lưu: VT, PTTT, GS.", footer_text)
                ])
            elif "tổng cục thuế" in iss_low or "cục thuế" in iss_low:
                footer_left.extend([
                    Paragraph("- Lãnh đạo Tổng cục Thuế;", footer_text),
                    Paragraph("- Cục Thuế các tỉnh, thành phố;", footer_text),
                    Paragraph("- Cổng TTĐT Tổng cục Thuế;", footer_text),
                    Paragraph("- Hiệp hội Doanh nghiệp, NNT;", footer_text),
                    Paragraph("- Lưu: VT, CS, TTKT, QLNT.", footer_text)
                ])
            else:
                footer_left.extend([
                    Paragraph("- Các cơ quan, đơn vị có liên quan;", footer_text),
                    Paragraph("- Các Cục, Vụ trực thuộc;", footer_text),
                    Paragraph("- Cổng Thông tin điện tử ngành;", footer_text),
                    Paragraph("- Lưu: VT, PC.", footer_text)
                ])

        # Chức danh và chữ ký người ký
        signer_title_display = signer_title.upper() if signer_title else "THỦ TRƯỞNG ĐƠN VỊ"
        if not any(x in signer_title_display for x in ["BỘ TRƯỞNG", "THỨ TRƯỞNG", "TỔNG CỤC", "CỤC TRƯỞNG", "CHỦ TỊCH", "THỐNG ĐỐC", "GIÁM ĐỐC"]):
            iss_low = issuing_body.lower()
            if "bộ tài chính" in iss_low:
                signer_title_display = "KT. BỘ TRƯỞNG<br/>THỨ TRƯỞNG"
            elif "tổng cục thuế" in iss_low:
                signer_title_display = "KT. TỔNG CỤC TRƯỞNG<br/>PHÓ TỔNG CỤC TRƯỞNG"
            elif "ngân hàng" in iss_low:
                signer_title_display = "KT. THỐNG ĐỐC<br/>PHÓ THỐNG ĐỐC"
            elif "chính phủ" in iss_low:
                signer_title_display = "TM. CHÍNH PHỦ<br/>THỦ TƯỚNG"
            elif "quốc hội" in iss_low:
                signer_title_display = "TM. QUỐC HỘI<br/>CHỦ TỊCH QUỐC HỘI"

        footer_right = [
            Paragraph(f"<b>{signer_title_display}</b>", header_agency_style),
            Spacer(1, 30),
            Paragraph(f"<b>{xml_escape(signer_name)}</b>" if signer_name else "(Đã ký và đóng dấu điện tử)", date_style)
        ]

        footer_table = Table([[footer_left, footer_right]], colWidths=[8.0 * cm, 9.5 * cm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))

        # Giữ phần chữ ký và nơi nhận cùng nhau trên 1 trang
        story.append(KeepTogether(footer_table))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
