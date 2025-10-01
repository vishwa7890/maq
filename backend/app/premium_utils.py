"""
Utility functions for premium user features.
"""
import os
import uuid
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import logging
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

# Ensure the exports directory exists
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

class PremiumQuotationGenerator:
    """Generate professional quotations with detailed breakdowns."""
    
    @staticmethod
    def generate_quotation(quotation_data: Dict, user_data: Dict) -> Dict:
        """
        Generate a professional quotation with detailed breakdowns.
        
        Args:
            quotation_data: Dictionary containing quotation details
            user_data: Dictionary containing user information
            
        Returns:
            Dict containing the formatted quotation
        """
        try:
            # Basic quotation details
            quotation_id = f"QUO-{uuid.uuid4().hex[:8].upper()}"
            date_created = datetime.now().strftime("%Y-%m-%d")
            
            # Prepare line items with detailed breakdown
            line_items = []
            total = 0
            
            for item in quotation_data.get('items', []):
                item_total = item.get('quantity', 0) * item.get('unit_price', 0)
                line_items.append({
                    'description': item.get('description', ''),
                    'quantity': item.get('quantity', 0),
                    'unit': item.get('unit', 'hours'),
                    'unit_price': f"{item.get('unit_price', 0):.2f}",
                    'total': f"{item_total:.2f}"
                })
                total += item_total
            
            # Calculate taxes and discounts
            tax_rate = quotation_data.get('tax_rate', 0.18)  # Default 18% tax
            tax_amount = total * tax_rate
            discount = quotation_data.get('discount', 0)
            grand_total = (total + tax_amount) - discount
            
            # Format the quotation
            quotation = {
                'quotation_id': quotation_id,
                'date_created': date_created,
                'client': {
                    'name': quotation_data.get('client_name', 'Client Name'),
                    'email': quotation_data.get('client_email', ''),
                    'company': quotation_data.get('client_company', '')
                },
                'project': {
                    'name': quotation_data.get('project_name', 'Project Name'),
                    'description': quotation_data.get('project_description', ''),
                    'timeline': quotation_data.get('timeline', 'To be discussed')
                },
                'line_items': line_items,
                'summary': {
                    'subtotal': f"{total:.2f}",
                    'tax_rate': f"{tax_rate*100}%",
                    'tax_amount': f"{tax_amount:.2f}",
                    'discount': f"{discount:.2f}",
                    'total': f"{grand_total:.2f}",
                    'currency': quotation_data.get('currency', 'INR')
                },
                'terms': [
                    "50% advance payment required to begin work",
                    "Balance payment due upon project completion",
                    "Prices valid for 30 days",
                    "Additional revisions may incur extra charges"
                ],
                'notes': quotation_data.get('notes', '')
            }
            
            return quotation
            
        except Exception as e:
            logger.error(f"Error generating quotation: {str(e)}")
            raise

    @staticmethod
    def export_to_pdf(quotation: Dict, include_watermark: bool = False) -> str:
        """
        Export quotation to a professionally formatted PDF.
        
        Args:
            quotation: The quotation data to export
            include_watermark: Whether to include a watermark (for non-premium users)
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create a unique filename
            filename = f"quotation_{quotation['quotation_id']}.pdf"
            filepath = EXPORTS_DIR / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Create content
            content = []
            
            # Add header
            content.append(Paragraph("PROFESSIONAL QUOTATION", title_style))
            content.append(Spacer(1, 12))
            
            # Add quotation details
            details = [
                ["Quotation ID:", quotation['quotation_id']],
                ["Date:", quotation['date_created']],
                ["Client:", quotation['client']['name']],
                ["Project:", quotation['project']['name']]
            ]
            
            details_table = Table(details, colWidths=[100, 300])
            details_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            content.append(details_table)
            content.append(Spacer(1, 24))
            
            # Add line items
            content.append(Paragraph("DETAILED BREAKDOWN", heading_style))
            content.append(Spacer(1, 12))
            
            # Prepare line items table
            line_items = [
                ["Description", "Qty", "Unit", "Unit Price", "Total"]
            ]
            
            for item in quotation['line_items']:
                line_items.append([
                    item['description'],
                    str(item['quantity']),
                    item['unit'],
                    item['unit_price'],
                    item['total']
                ])
            
            # Add summary
            summary = [
                ["", "", "", "Subtotal:", quotation['summary']['subtotal']],
                ["", "", "", f"Tax ({quotation['summary']['tax_rate']}):", quotation['summary']['tax_amount']],
                ["", "", "", "Discount:", f"-{quotation['summary']['discount']}"],
                ["", "", "", "<b>TOTAL:</b>", f"<b>{quotation['summary']['total']} {quotation['summary']['currency']}</b>"]
            ]
            
            line_items_table = Table(line_items + [[''] * 5] + summary, colWidths=[250, 50, 50, 80, 80])
            line_items_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('LINEABOVE', (0, -4), (-1, -1), 1, colors.black),
                ('LINEABOVE', (3, -1), (4, -1), 1, colors.black),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -4), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ]))
            
            content.append(line_items_table)
            content.append(Spacer(1, 24))
            
            # Add terms and conditions
            content.append(Paragraph("TERMS & CONDITIONS", heading_style))
            content.append(Spacer(1, 6))
            
            for term in quotation.get('terms', []):
                content.append(Paragraph(f"• {term}", normal_style))
            
            # Add notes if any
            if quotation.get('notes'):
                content.append(Spacer(1, 12))
                content.append(Paragraph("NOTES", heading_style))
                content.append(Spacer(1, 6))
                content.append(Paragraph(quotation['notes'], normal_style))
            
            # Build the PDF
            doc.build(content)
            
            # Add watermark if needed (for non-premium users)
            if include_watermark:
                from PyPDF2 import PdfReader, PdfWriter
                
                # Create a watermark
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=letter)
                c.setFont('Helvetica-Bold', 40)
                c.setFillColor(colors.grey, alpha=0.2)
                c.saveState()
                c.translate(300, 400)
                c.rotate(45)
                c.drawCentredString(0, 0, "SAMPLE")
                c.restoreState()
                c.save()
                
                # Move to the beginning of the StringIO buffer
                packet.seek(0)
                watermark = PdfReader(packet)
                
                # Read the existing PDF
                existing_pdf = PdfReader(open(filepath, "rb"))
                output = PdfWriter()
                
                # Add the watermark to each page
                for page in existing_pdf.pages:
                    page.merge_page(watermark.pages[0])
                    output.add_page(page)
                
                # Write the watermarked file
                with open(filepath, "wb") as output_file:
                    output.write(output_file)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise

    @classmethod
    def generate_and_export_quotation(
        cls, 
        quotation_data: Dict, 
        user_data: Dict, 
        include_watermark: bool = False
    ) -> Dict:
        """
        Generate a quotation and export it to PDF.
        
        Args:
            quotation_data: The quotation data
            user_data: The user data
            include_watermark: Whether to include a watermark
            
        Returns:
            Dict containing the quotation and PDF path
        """
        try:
            # Generate the quotation
            quotation = cls.generate_quotation(quotation_data, user_data)
            
            # Export to PDF
            pdf_path = cls.export_to_pdf(quotation, include_watermark)
            
            return {
                'success': True,
                'quotation': quotation,
                'pdf_path': pdf_path,
                'download_url': f"/api/exports/{os.path.basename(pdf_path)}"
            }
            
        except Exception as e:
            logger.error(f"Error in generate_and_export_quotation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
