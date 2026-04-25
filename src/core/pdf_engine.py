import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image
from datetime import datetime
from src.utils.paths import get_pdf_dir
from src.core.template_data import get_template

# Professional color palette
NAVY = colors.HexColor("#1e293b")
INDIGO = colors.HexColor("#4f46e5")
INDIGO_LIGHT = colors.HexColor("#eef2ff")
SLATE = colors.HexColor("#334155")
SLATE_LIGHT = colors.HexColor("#f1f5f9")
GRAY = colors.HexColor("#64748b")
DARK_BG = colors.HexColor("#374151")
WHITE = colors.white


class PDFEngine:
    def __init__(self, output_dir=None):
        if output_dir is None:
            self.output_dir = get_pdf_dir()
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()

    def generate(self, customer_name, invoice_number, items, total_amount, is_preview=False):
        """
        Generates a professional PDF invoice using the saved template.
        items: list of tuples (description, quantity, unit_price, subtotal)
        Returns: absolute file path to the generated PDF.
        """
        t = get_template()

        if is_preview:
            import tempfile
            file_path = os.path.join(tempfile.gettempdir(), f"preview_{invoice_number}.pdf")
        else:
            os.makedirs(self.output_dir, exist_ok=True)
            clean_name = "".join(x for x in customer_name if x.isalnum() or x in " -_").strip()
            file_path = os.path.join(self.output_dir, f"{clean_name}_{invoice_number}.pdf")

        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )
        elements = []
        page_w = A4[0] - 40*mm  # usable width

        # ═══════════════════════════════════════════
        # HEADER BLOCK (dark background)
        # ═══════════════════════════════════════════
        # Branding Block (Logo + Credit + Title)
        from src.utils.paths import get_base_dir
        logo_path = os.path.join(get_base_dir(), "assets", "icons", "logo.png")
        left_content = []
        if os.path.exists(logo_path):
            left_content.append(Image(logo_path, width=18*mm, height=18*mm, kind='proportional'))
            left_content.append(Spacer(1, 2))
            left_content.append(Paragraph("Created by R.Thigan", 
                ParagraphStyle('Credit', fontName='Helvetica-Bold', fontSize=7, textColor=WHITE, alignment=0)))
            left_content.append(Spacer(1, 8))
        
        left_content.append(Paragraph("INVOICE", ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=28, textColor=WHITE)))

        header_data = [[
            left_content,
            Paragraph(
                f"<b>Invoice #:</b> {invoice_number}<br/>"
                f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}",
                ParagraphStyle('HD', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#cbd5e1"), alignment=2, leading=16)
            )
        ]]
        header_table = Table(header_data, colWidths=[page_w * 0.6, page_w * 0.4])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_BG),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 18),
            ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 18))

        # ═══════════════════════════════════════════
        # FROM / BILLED TO
        # ═══════════════════════════════════════════
        label_style = ParagraphStyle('LBL', fontName='Helvetica', fontSize=9, textColor=GRAY, leading=14)
        value_style = ParagraphStyle('VAL', fontName='Helvetica-Bold', fontSize=12, textColor=NAVY, leading=16)
        detail_style = ParagraphStyle('DET', fontName='Helvetica', fontSize=10, textColor=SLATE, leading=14)

        from_text = f"<b>{t.get('business_name', '')}</b>"
        from_details = ""
        if t.get("payment_method") and t.get("payment_number"):
            from_details += f"{t['payment_method']}: {t['payment_number']}<br/>"
        if t.get("business_phone"):
            from_details += f"Contact: {t['business_phone']}"

        addr_data = [[
            [Paragraph("FROM", label_style),
             Paragraph(from_text, value_style),
             Paragraph(from_details, detail_style)],
            [Paragraph("BILLED TO", label_style),
             Paragraph(f"<b>{customer_name}</b>", value_style)]
        ]]
        addr_table = Table(addr_data, colWidths=[page_w * 0.5, page_w * 0.5])
        addr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(addr_table)
        elements.append(Spacer(1, 28))

        # ═══════════════════════════════════════════
        # ITEMS TABLE
        # ═══════════════════════════════════════════
        th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=10, textColor=INDIGO)
        td_style = ParagraphStyle('TD', fontName='Helvetica', fontSize=10, textColor=NAVY)
        td_right = ParagraphStyle('TDR', fontName='Helvetica', fontSize=10, textColor=NAVY, alignment=2)

        data = [[
            Paragraph("DESCRIPTION", th_style),
            Paragraph("AMOUNT", ParagraphStyle('THR', fontName='Helvetica-Bold', fontSize=10, textColor=INDIGO, alignment=2))
        ]]

        for item in items:
            desc, _, price, sub = item
            data.append([
                Paragraph(str(desc), td_style),
                Paragraph(f"${sub:.2f}", td_right)
            ])

        # Delivery Fee
        delivery_fee = float(t.get("delivery_fee", 10.0))
        fee_style = ParagraphStyle('Fee', fontName='Helvetica', fontSize=10, textColor=GRAY)
        fee_right = ParagraphStyle('FeeR', fontName='Helvetica', fontSize=10, textColor=GRAY, alignment=2)
        data.append([
            Paragraph("Delivery Fee", fee_style),
            Paragraph(f"${delivery_fee:.2f}", fee_right)
        ])

        # Total
        final_total = total_amount + delivery_fee
        tot_style = ParagraphStyle('Tot', fontName='Helvetica-Bold', fontSize=13, textColor=INDIGO)
        tot_right = ParagraphStyle('TotR', fontName='Helvetica-Bold', fontSize=13, textColor=INDIGO, alignment=2)
        data.append([
            Paragraph("TOTAL", tot_style),
            Paragraph(f"${final_total:.2f}", tot_right)
        ])

        table = Table(data, colWidths=[page_w * 0.7, page_w * 0.3])
        num_items = len(items)
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), INDIGO_LIGHT),
            ('LINEBELOW', (0, 0), (-1, 0), 2, INDIGO),
            ('TOPPADDING', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),

            # Data rows
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),

            # Alternating rows (items only)
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, SLATE_LIGHT]),

            # Total row highlight
            ('BACKGROUND', (0, -1), (-1, -1), INDIGO_LIGHT),
            ('LINEABOVE', (0, -1), (-1, -1), 2, INDIGO),

            # Outer border
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#e2e8f0")),
            ('LINEBELOW', (0, 1), (-1, -3), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(table)

        # ═══════════════════════════════════════════
        # NOTE
        # ═══════════════════════════════════════════
        note = t.get("self_collect_note", "").strip()
        if note:
            note = note.replace("${fee}", f"${delivery_fee:.2f}")
            elements.append(Spacer(1, 16))
            note_style = ParagraphStyle(
                'Note', parent=self.styles['Normal'],
                fontSize=9, textColor=SLATE, leading=13,
                backColor=SLATE_LIGHT,
                borderPadding=(8, 10, 8, 10),
            )
            elements.append(Paragraph(f"<b>NOTE</b><br/>{note}", note_style))

        # ═══════════════════════════════════════════
        # PAYMENT METHOD + AFTER PAYMENT (side by side)
        # ═══════════════════════════════════════════
        elements.append(Spacer(1, 14))

        pay_label = ParagraphStyle('PL', fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#9ca3af"), leading=12)
        pay_value = ParagraphStyle('PV', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE, leading=16)
        pay_detail = ParagraphStyle('PD', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#d1d5db"), leading=14)

        after_label = ParagraphStyle('AL', fontName='Helvetica', fontSize=8, textColor=GRAY, leading=12)
        after_value = ParagraphStyle('AV', fontName='Helvetica-Bold', fontSize=11, textColor=NAVY, leading=16)

        method = t.get("payment_method", "")
        number = t.get("payment_number", "")
        name = t.get("payment_name", "")
        receipt = t.get("receipt_contact", "")

        pay_data = [[
            [Paragraph("PAYMENT METHOD", pay_label),
             Paragraph(method, pay_value),
             Paragraph(f"{number}  ·  {name}" if number else "", pay_detail)],
            [Paragraph("AFTER PAYMENT", after_label),
             Paragraph("Send receipt to:", ParagraphStyle('AT', fontName='Helvetica', fontSize=10, textColor=SLATE, leading=14)),
             Paragraph(f"<b>{receipt}</b>", after_value)]
        ]]
        pay_table = Table(pay_data, colWidths=[page_w * 0.48, page_w * 0.48], spaceBefore=4)
        pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), DARK_BG),
            ('BACKGROUND', (1, 0), (1, 0), SLATE_LIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        elements.append(pay_table)

        # ═══════════════════════════════════════════
        # FOOTER
        # ═══════════════════════════════════════════
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        footer_style = ParagraphStyle(
            'Footer', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor("#94a3b8"),
            alignment=1, leading=12
        )
        phone = t.get("business_phone", "")
        closing = t.get("closing_message", "")
        footer = t.get("footer_text", "")

        footer_parts = []
        if phone:
            footer_parts.append(f"For enquiries: {phone}")
        if closing:
            footer_parts.append(closing)
        if footer:
            footer_parts.append(footer)

        footer_data = [[Paragraph(p, footer_style) for p in footer_parts]]
        if footer_parts:
            cols = [page_w / len(footer_parts)] * len(footer_parts)
            ft = Table(footer_data, colWidths=cols)
            ft.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, 0), 'RIGHT'),
            ]))
            elements.append(ft)

        # Build PDF
        doc.build(elements)
        return os.path.abspath(file_path)
