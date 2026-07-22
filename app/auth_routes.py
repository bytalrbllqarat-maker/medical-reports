from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import uuid
from dotenv import load_dotenv
import os

from app.models import User
from app.schemas import UserCreate, UserResponse
from app.database import get_db
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token
)

load_dotenv()

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# ========== Login ==========
@router.post("/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    تسجيل الدخول
    """
    # Find user
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات تسجيل الدخول غير صحيحة"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب المستخدم معطل"
        )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

# ========== Register ==========
@router.post("/register")
async def register(
    full_name: str,
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    إنشاء حساب جديد
    """
    # Validate input
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور يجب أن تكون 8 أحرف على الأقل"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مسجل بالفعل"
        )
    
    # Check if username exists
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="اسم المستخدم مسجل بالفعل"
        )
    
    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_admin=False,
        role="user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "تم إنشاء الحساب بنجاح",
        "user": UserResponse.from_orm(new_user)
    }

# ========== Get Current User ==========
@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db)
):
    """
    الحصول على بيانات المستخدم الحالي
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    return UserResponse.from_orm(user)

# ========== Logout ==========
@router.post("/logout")
async def logout():
    """
    تسجيل الخروج (يتم الحذف من جانب العميل)
    """
    return {"message": "تم تسجيل الخروج بنجاح"}

# ========== Refresh Token ==========
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    تحديث التوكن
    """
    try:
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المستخدم غير موجود"
            )
        
        new_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
            }
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توكن غير صالح"
        )
