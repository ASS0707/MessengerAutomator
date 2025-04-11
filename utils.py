import io
import os
import logging
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

def setup_arabic_fonts():
    """Register Arabic fonts for PDF generation"""
    try:
        # Register a basic Arabic font
        pdfmetrics.registerFont(TTFont('Arabic', 'static/fonts/NotoSansArabic-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('ArabicBold', 'static/fonts/NotoSansArabic-Bold.ttf'))
        return True
    except Exception as e:
        logging.error(f"Error registering Arabic fonts: {str(e)}")
        return False

def generate_pdf_invoice(order, customer, items, business_name, business_address, business_phone, business_email):
    """Generate a PDF invoice for an order"""
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    ))
    styles.add(ParagraphStyle(
        name='CenterAlign',
        parent=styles['Normal'],
        alignment=TA_CENTER
    ))
    
    # Try to set up Arabic fonts, if available
    has_arabic = setup_arabic_fonts()
    if has_arabic:
        styles.add(ParagraphStyle(
            name='Arabic',
            fontName='Arabic',
            alignment=TA_RIGHT,
            fontSize=12,
            leading=14
        ))
    
    # Create story (list of elements to build the PDF)
    story = []
    
    # Add invoice title
    story.append(Paragraph(f"INVOICE #{order.id}", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Add date
    story.append(Paragraph(f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Add business info
    story.append(Paragraph(f"From:", styles['Heading4']))
    story.append(Paragraph(business_name, styles['Normal']))
    if business_address:
        story.append(Paragraph(business_address, styles['Normal']))
    if business_phone:
        story.append(Paragraph(f"Phone: {business_phone}", styles['Normal']))
    if business_email:
        story.append(Paragraph(f"Email: {business_email}", styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Add customer info
    story.append(Paragraph(f"Bill To:", styles['Heading4']))
    story.append(Paragraph(customer.full_name or customer.messenger_name, styles['Normal']))
    if customer.address:
        story.append(Paragraph(customer.address, styles['Normal']))
    if customer.phone:
        story.append(Paragraph(f"Phone: {customer.phone}", styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Add order items table
    data = [["Item", "Quantity", "Price", "Total"]]
    
    # Add each item to the table
    total = 0
    for item in items:
        from models import Product
        product = Product.query.get(item.product_id)
        if product:
            item_total = item.quantity * item.price
            total += item_total
            data.append([
                product.name,
                str(item.quantity),
                f"{item.price:.2f}",
                f"{item_total:.2f}"
            ])
    
    # Add total row
    data.append(["", "", "Grand Total", f"{total:.2f}"])
    
    # Create table
    table = Table(data, colWidths=[doc.width * 0.4, doc.width * 0.2, doc.width * 0.2, doc.width * 0.2])
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(table_style)
    
    story.append(table)
    story.append(Spacer(1, 24))
    
    # Add order notes if any
    if order.notes:
        story.append(Paragraph("Order Notes:", styles['Heading4']))
        story.append(Paragraph(order.notes, styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Add thank you message
    story.append(Paragraph("Thank you for your business!", styles['CenterAlign']))
    
    # Build PDF
    doc.build(story)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def backup_database(db_path, backup_dir):
    """Create a backup of the SQLite database"""
    try:
        import shutil
        import time
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Create backup filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Clean up old backups (keep only last 10)
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
                          if f.startswith("backup_") and f.endswith(".db")])
        
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(old_backup)
        
        logging.info(f"Database backup created: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Database backup failed: {str(e)}")
        return False
