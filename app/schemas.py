from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class ReportCreate(BaseModel):
    patient_name: str
    patient_age: int
    patient_blood_type: str
    report_type: str
    diagnosis: str
    medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    notes: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    patient_name: str
    patient_age: int
    patient_blood_type: str
    report_type: str
    diagnosis: str
    medications: List[str]
    allergies: List[str]
    notes: Optional[str]
    status: str
    share_url: str
    share_token: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True

class ShareResponse(BaseModel):
    share_url: str
    share_token: str
    qr_code_url: str
    expires_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    role: str
    
    class Config:
        from_attributes = True
