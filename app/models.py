from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ReportStatusEnum(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    reports = relationship("ReportModel", back_populates="user")

class ReportModel(Base):
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    patient_name = Column(String, index=True)
    patient_age = Column(Integer)
    patient_blood_type = Column(String)
    report_type = Column(String)  # فحص عام، تحليل دم، إلخ
    diagnosis = Column(Text)
    medications = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    notes = Column(Text)
    status = Column(String, default="pending", index=True)
    
    # Share & QR Code
    share_url = Column(String, unique=True)
    share_token = Column(String, unique=True, index=True)
    qr_code_path = Column(String)
    share_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="reports")

class ShareLink(Base):
    __tablename__ = "share_links"
    
    id = Column(String, primary_key=True, index=True)
    report_id = Column(String, ForeignKey("reports.id"), index=True)
    token = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
