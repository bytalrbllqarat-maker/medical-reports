import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from datetime import datetime
import uuid

def generate_qr_code(data: str, size: int = 300) -> Image.Image:
    """
    توليد QR Code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to desired size
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    return img

def generate_share_link(base_url: str, report_id: str) -> str:
    """
    توليد رابط المشاركة
    """
    share_token = str(uuid.uuid4())
    return f"{base_url}/share/{share_token}", share_token

def send_notification(user_email: str, subject: str, body: str) -> bool:
    """
    إرسال إخطار بالبريد الإلكتروني
    """
    # Implementation for sending emails
    # Using libraries like sendgrid, mailgun, or smtplib
    pass

def format_date(dt: datetime) -> str:
    """
    تنسيق التاريخ بصيغة عربية
    """
    months_ar = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    return f"{dt.day} {months_ar[dt.month]} {dt.year}"
