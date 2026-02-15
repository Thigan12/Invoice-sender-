import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from datetime import datetime

class PDFEngine:
    def __init__(self, output_dir=None):
        # All generated PDFs go to ONE consistent local folder
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if output_dir is None:
            self.output_dir = os.path.join(base_dir, "data", "generated_pdfs")
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()

    def generate(self, customer_name, invoice_number, items, total_amount, is_preview=False):
        """
        Generates a professional PDF invoice.
        items: list of tuples (description, quantity, unit_price, subtotal)
        Returns: absolute file path to the generated PDF.
        """
        if is_preview:
            import tempfile
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"preview_{invoice_number}.pdf")
        else:
            # Save to the single local output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            clean_name = "".join(x for x in customer_name if x.isalnum() or x in " -_").strip()
            file_name = f"{clean_name}_{invoice_number}.pdf"
            file_path = os.path.join(self.output_dir, file_name)
           
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        elements = []

        # === HEADER: Company/Brand ===
        brand_style = ParagraphStyle(
            'BrandName',
            parent=self.styles['Heading1'],
            fontSize=28,
            spaceAfter=2,
            textColor=colors.HexColor("#1e293b"),
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("INVOICE", brand_style))
        
        # Divider
        elements.append(HRFlowable(
            width="100%", thickness=2, 
            color=colors.HexColor("#6366f1"), 
            spaceAfter=15, spaceBefore=5
        ))

        # === Customer & Invoice Details ===
        details_style = ParagraphStyle(
            'DetailsStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=18,
            textColor=colors.HexColor("#334155")
        )

        today_str = datetime.now().strftime('%d %B %Y')
        details_text = f"""
        <b>Customer:</b> {customer_name}<br/>
        <b>Invoice #:</b> {invoice_number}<br/>
        <b>Date:</b> {today_str}<br/>
        """
        elements.append(Paragraph(details_text, details_style))
        elements.append(Spacer(1, 20))

        # === Items Table ===
        header_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
        cell_style = ParagraphStyle('TD', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#1e293b"))
        cell_right = ParagraphStyle('TDR', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#1e293b"), alignment=2)

        data = [[
            Paragraph("Description", header_style), 
            Paragraph("Price", header_style)
        ]]
        
        for item in items:
            desc, _, price, sub = item
            data.append([
                Paragraph(str(desc), cell_style), 
                Paragraph(f"${sub:.2f}", cell_right)
            ])
        
        # Delivery Fee
        delivery_fee = 10.0
        fee_style = ParagraphStyle('Fee', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#64748b"))
        fee_right = ParagraphStyle('FeeR', fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#64748b"), alignment=2)
        data.append([
            Paragraph("Delivery Fee", fee_style), 
            Paragraph(f"${delivery_fee:.2f}", fee_right)
        ])
        
        # Total
        final_total = total_amount + delivery_fee
        total_style = ParagraphStyle('Tot', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1e293b"))
        total_right = ParagraphStyle('TotR', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1e293b"), alignment=2)
        data.append([
            Paragraph("TOTAL", total_style), 
            Paragraph(f"${final_total:.2f}", total_right)
        ])

        table = Table(data, colWidths=[390, 120])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
            ('TOPPADDING', (0, 0), (-1, 0), 14),
            
            # Data rows
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            
            # Alternating row colors for data (skip header & total)
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#eef2ff")),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor("#4f46e5")),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#4f46e5")),
        ]))
       
        elements.append(table)

        # === Note ===
        elements.append(Spacer(1, 18))
        note_style = ParagraphStyle(
            'NoteStyle', 
            parent=self.styles['Normal'], 
            fontSize=9, 
            textColor=colors.HexColor("#dc2626"), 
            leading=13,
            backColor=colors.HexColor("#fef2f2"),
            borderPadding=(6, 8, 6, 8),
        )
        note_text = "<b>NOTE:</b> If you have paid beforehand or are self-collecting, please deduct the $10.00 delivery fee from the total amount."
        elements.append(Paragraph(note_text, note_style))
        
        # === Footer ===
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
        footer_style = ParagraphStyle(
            'Footer', 
            parent=self.styles['Normal'], 
            fontSize=8, 
            textColor=colors.HexColor("#94a3b8"), 
            alignment=1,
            leading=12
        )
        elements.append(Paragraph("Software created by Thigan Pvt Ltd<br/>Thank you for buying from us!", footer_style))

        # Build PDF
        doc.build(elements)
        
        # Always return the absolute path for consistent access
        return os.path.abspath(file_path)
