from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
import uuid
import logging

load_dotenv()

# Import models and schemas
from app.models import Base, ReportModel, User, ShareLink
from app.schemas import ReportCreate, ReportResponse, ShareResponse
from app.database import engine, get_db
from app.auth import create_access_token, get_current_user
from app.utils import generate_qr_code, generate_share_link, send_notification

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 تطبيق منصة التقارير الطبية قيد التشغيل")
    yield
    logger.info("🛑 تطبيق منصة التقارير الطبية توقف")

app = FastAPI(
    title="Medical Reports Platform",
    description="منصة شاملة لإدارة وتحقق من التقارير الطبية",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/qrcodes"):
    os.makedirs("static/qrcodes")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== Health Check ==========
@app.get("/health", tags=["Health"])
async def health_check():
    """فحص صحة التطبيق"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ========== Reports Endpoints ==========

@app.post("/api/reports", response_model=ReportResponse, tags=["Reports"])
async def create_report(
    report: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إنشاء تقرير طبي جديد
    """
    try:
        # Generate report ID and share link
        report_id = str(uuid.uuid4())
        share_token = str(uuid.uuid4())
        share_url = f"{os.getenv('BASE_URL')}/share/{share_token}"
        
        # Generate QR Code
        qr_image = generate_qr_code(share_url)
        qr_filename = f"{report_id}.png"
        qr_path = f"static/qrcodes/{qr_filename}"
        qr_image.save(qr_path)
        
        # Create database record
        db_report = ReportModel(
            id=report_id,
            user_id=current_user.id,
            patient_name=report.patient_name,
            patient_age=report.patient_age,
            patient_blood_type=report.patient_blood_type,
            diagnosis=report.diagnosis,
            medications=report.medications,
            allergies=report.allergies,
            notes=report.notes,
            report_type=report.report_type,
            status="pending",
            share_url=share_url,
            qr_code_path=qr_path,
            share_token=share_token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"✅ تم إنشاء تقرير جديد: {report_id}")
        
        return ReportResponse.from_orm(db_report)
    except Exception as e:
        db.rollback()
        logger.error(f"❌ خطأ في إنشاء التقرير: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/reports", tags=["Reports"])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على قائمة التقارير
    """
    query = db.query(ReportModel).filter(ReportModel.user_id == current_user.id)
    
    if status:
        query = query.filter(ReportModel.status == status)
    
    reports = query.offset(skip).limit(limit).all()
    total = db.query(ReportModel).filter(ReportModel.user_id == current_user.id).count()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "reports": [ReportResponse.from_orm(r) for r in reports]
    }

@app.get("/api/reports/{report_id}", response_model=ReportResponse, tags=["Reports"])
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على تفاصيل تقرير محدد
    """
    report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="التقرير غير موجود")
    
    return ReportResponse.from_orm(report)

@app.put("/api/reports/{report_id}", response_model=ReportResponse, tags=["Reports"])
async def update_report(
    report_id: str,
    report: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحديث تقرير موجود
    """
    db_report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.user_id == current_user.id
    ).first()
    
    if not db_report:
        raise HTTPException(status_code=404, detail="التقرير غير موجود")
    
    for key, value in report.dict().items():
        setattr(db_report, key, value)
    
    db_report.updated_at = datetime.now()
    db.commit()
    db.refresh(db_report)
    
    logger.info(f"✏️ تم تحديث التقرير: {report_id}")
    return ReportResponse.from_orm(db_report)

@app.delete("/api/reports/{report_id}", tags=["Reports"])
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    حذف تقرير
    """
    report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="التقرير غير موجود")
    
    db.delete(report)
    db.commit()
    
    logger.info(f"🗑️ تم حذف التقرير: {report_id}")
    return {"message": "تم حذف التقرير بنجاح"}

# ========== Share Endpoints ==========

@app.get("/api/reports/{report_id}/qrcode", tags=["Share"])
async def get_qr_code(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على QR Code للتقرير
    """
    report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.user_id == current_user.id
    ).first()
    
    if not report or not report.qr_code_path:
        raise HTTPException(status_code=404, detail="QR Code غير موجود")
    
    return FileResponse(report.qr_code_path, media_type="image/png")

@app.get("/api/reports/{report_id}/qrcode-base64", tags=["Share"])
async def get_qr_code_base64(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على QR Code كـ Base64
    """
    report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.user_id == current_user.id
    ).first()
    
    if not report or not report.qr_code_path:
        raise HTTPException(status_code=404, detail="QR Code غير موجود")
    
    with open(report.qr_code_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    return {
        "report_id": report_id,
        "qr_code_base64": image_data,
        "share_url": report.share_url,
        "format": "image/png"
    }

@app.get("/share/{share_token}", tags=["Share"])
async def view_shared_report(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    عرض التقرير المشارك عبر الرابط
    """
    report = db.query(ReportModel).filter(
        ReportModel.share_token == share_token,
        ReportModel.expires_at > datetime.now()
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="الرابط غير صالح أو انتهت صلاحيته")
    
    # Return HTML page
    return HTMLResponse(generate_share_html(report))

@app.get("/api/share/{share_token}", tags=["Share"])
async def get_shared_report_data(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    الحصول على بيانات التقرير المشارك (JSON)
    """
    report = db.query(ReportModel).filter(
        ReportModel.share_token == share_token,
        ReportModel.expires_at > datetime.now()
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="الرابط غير صالح أو انتهت صلاحيته")
    
    return ReportResponse.from_orm(report)

def generate_share_html(report: ReportModel) -> str:
    """
    توليد صفحة HTML لعرض التقرير المشارك
    """
    qr_data = ""
    if report.qr_code_path and os.path.exists(report.qr_code_path):
        with open(report.qr_code_path, "rb") as f:
            qr_data = base64.b64encode(f.read()).decode()
    
    medications_html = "".join([
        f'<div style="padding: 8px; background: #f0f0f0; margin: 5px 0; border-radius: 5px;">{med}</div>'
        for med in (report.medications or []) if med
    ])
    
    allergies_html = "".join([
        f'<span style="background: #ffd700; padding: 5px 10px; margin: 3px; border-radius: 15px; display: inline-block;">{allergy}</span>'
        for allergy in (report.allergies or []) if allergy
    ])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>التقرير الطبي - منصة تشيك</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Tajawal', sans-serif;
                background: linear-gradient(135deg, #00a896 0%, #028074 50%, #1a535c 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #00a896;
                padding-bottom: 20px;
            }}
            .header h1 {{
                color: #1a535c;
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .header p {{
                color: #666;
                font-size: 14px;
            }}
            .qr-section {{
                text-align: center;
                margin: 30px 0;
                padding: 20px;
                background: #f0f4f8;
                border-radius: 15px;
            }}
            .qr-section img {{
                max-width: 250px;
                height: auto;
                border-radius: 10px;
            }}
            .qr-label {{
                color: #666;
                font-size: 12px;
                margin-top: 10px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin: 30px 0;
            }}
            .info-item {{
                background: #f9f9f9;
                padding: 15px;
                border-radius: 10px;
                border-right: 4px solid #00a896;
            }}
            .info-label {{
                color: #666;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 5px;
            }}
            .info-value {{
                color: #1a535c;
                font-size: 16px;
                font-weight: 700;
            }}
            .diagnosis-section, .medications-section, .allergies-section {{
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 10px;
            }}
            .section-title {{
                color: #1a535c;
                font-weight: 700;
                margin-bottom: 15px;
                font-size: 16px;
            }}
            .medicines-list, .allergies-list {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .medicine-item, .allergy-item {{
                padding: 8px 15px;
                background: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
            .print-btn {{
                display: inline-block;
                background: #00a896;
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                margin-top: 20px;
                cursor: pointer;
                border: none;
                font-size: 14px;
            }}
            .print-btn:hover {{
                background: #028074;
            }}
            @media (max-width: 600px) {{
                .info-grid {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    padding: 20px;
                }}
            }}
            @media print {{
                body {{
                    background: white;
                }}
                .print-btn {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 التقرير الطبي</h1>
                <p>منصة تشيك - Medical Reports Platform</p>
            </div>
            
            <div class="qr-section">
                <img src="data:image/png;base64,{qr_data}" alt="QR Code">
                <p class="qr-label">امسح الـ QR Code للتحقق من صحة التقرير</p>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">اسم المريض</div>
                    <div class="info-value">{report.patient_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">العمر</div>
                    <div class="info-value">{report.patient_age} سنة</div>
                </div>
                <div class="info-item">
                    <div class="info-label">فصيلة الدم</div>
                    <div class="info-value">{report.patient_blood_type}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">نوع التقرير</div>
                    <div class="info-value">{report.report_type}</div>
                </div>
            </div>
            
            <div class="diagnosis-section">
                <div class="section-title">📋 التشخيص</div>
                <p style="line-height: 1.8; color: #333;">{report.diagnosis}</p>
            </div>
            
            {f'<div class="medications-section"><div class="section-title">💊 الأدوية الموصوفة</div><div class="medicines-list">{medications_html}</div></div>' if report.medications else ''}
            
            {f'<div class="allergies-section"><div class="section-title">⚠️ الحساسيات</div><div class="allergies-list">{allergies_html}</div></div>' if report.allergies else ''}
            
            {f'<div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin: 20px 0;"><strong>📝 ملاحظات:</strong><p style="margin-top: 10px; color: #333;">{report.notes}</p></div>' if report.notes else ''}
            
            <div class="footer">
                <p>تاريخ إنشاء التقرير: {report.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p>معرّف التقرير: {report.id}</p>
                <button class="print-btn" onclick="window.print()">🖨️ اطبع التقرير</button>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ========== Statistics Endpoints ==========

@app.get("/api/stats", tags=["Statistics"])
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على الإحصائيات
    """
    total_reports = db.query(ReportModel).filter(ReportModel.user_id == current_user.id).count()
    verified = db.query(ReportModel).filter(
        ReportModel.user_id == current_user.id,
        ReportModel.status == "verified"
    ).count()
    pending = db.query(ReportModel).filter(
        ReportModel.user_id == current_user.id,
        ReportModel.status == "pending"
    ).count()
    rejected = db.query(ReportModel).filter(
        ReportModel.user_id == current_user.id,
        ReportModel.status == "rejected"
    ).count()
    
    return {
        "total_reports": total_reports,
        "verified_reports": verified,
        "pending_reports": pending,
        "rejected_reports": rejected,
        "active_users": db.query(User).count()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
