from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
import os

def create_interview_guide():
    output_path = os.path.join(os.getcwd(), "Technical_Interview_Guide.pdf")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
        alignment=1
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#4f46e5"),
        spaceBefore=15,
        spaceAfter=8,
        borderPadding=(0, 0, 2, 0)
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )

    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    # 1. Header
    elements.append(Paragraph("Invoice Sender Pro: Technical Deep Dive", title_style))
    elements.append(Paragraph("Essential Preparation Guide for Technical Interviews", ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=1, textColor=colors.grey, spaceAfter=20)))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=20))

    # 2. Project Overview
    elements.append(Paragraph("1. Project Overview", section_style))
    elements.append(Paragraph(
        "Invoice Sender Pro is a specialized Desktop Application designed to automate the 'Last Mile' of business billing. "
        "It solves the problem of manual data entry by extracting customer invoices from messy spreadsheets, "
        "generating professional PDFs, and automating the delivery via WhatsApp. It focuses on User Experience (UX) "
        "and data integrity using a modern local-first architecture.",
        body_style
    ))

    # 3. The Tech Stack (The "Why")
    elements.append(Paragraph("2. The Tech Stack", section_style))
    
    tech_data = [
        ["Technology", "Usage in Project", "Why this was chosen?"],
        ["Python 3.x", "Core Logic", "Versatility and rich ecosystem for data science and automation."],
        ["PySide6 (Qt)", "GUI Framework", "Industry standard for high-performance, cross-platform desktop UI."],
        ["PostgreSQL/SQLite", "Data Persistence", "SQLite was used for local-first, zero-configuration storage."],
        ["Pandas", "Data Wrangling", "Efficient parsing and grouping of large Excel datasets."],
        ["ReportLab", "PDF Generation", "Low-level PDF control for pixel-perfect branding and dynamic layouts."],
        ["RapidFuzz", "Intelligence", "Fuzzy string matching to link inconsistent customer names across files."],
        ["PyAutoGUI", "Automation", "Automating keyboard/mouse actions to bridge interactions with WhatsApp Web."]
    ]
    
    t = Table(tech_data, colWidths=[100, 150, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # 4. Key Architectural Concepts
    elements.append(Paragraph("3. Key Architectural Concepts", section_style))
    elements.append(Paragraph("<b>Repository Pattern:</b> I used a 'DataRepository' layer to separate the database logic from the UI views. This means if we ever want to switch from SQLite to a Cloud Database (like Supabase), we only need to change one file.", body_style))
    elements.append(Paragraph("<b>State Management:</b> The app tracks complex states like 'Draft' vs 'Sent' invoices, ensuring businesses don't accidentally double-bill a client.", body_style))
    elements.append(Paragraph("<b>Modular UI:</b> Each screen (Dashboard, Invoices, Customers) is built as a separate component, making the code maintainable and easy to scale.", body_style))

    # 5. Potential Interview Questions
    elements.append(Paragraph("4. Common Interview Questions", section_style))
    
    q_and_a = [
        ("Q: Why didn't you build this as a Website?", 
         "A: Desktop apps offer better access to the local file system (Excel) and hardware automation (PyAutoGUI) which browsers restrict for security reasons. It's also 'local-first', meaning it works without internet."),
        ("Q: How does the app handle 'bad' data in Excel?", 
         "A: I used Pandas and custom 'ffill' (forward-fill) logic to handle merged cells or missing names, which are common in real-world business spreadsheets."),
        ("Q: What was the biggest technical challenge?", 
         "A: Handling DPI scaling on Windows. Different monitors have different pixel densities. I solved this by setting the QT_AUTO_SCREEN_SCALE_FACTOR environment variable before initializing the engine.")
    ]
    
    for q, a in q_and_a:
        elements.append(Paragraph(q, bold_body))
        elements.append(Paragraph(a, body_style))

    # Build PDF
    doc.build(elements)
    print(f"Guide generated at: {output_path}")

if __name__ == "__main__":
    create_interview_guide()
