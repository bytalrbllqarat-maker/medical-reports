from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

from app.auth_routes import router as auth_router

app = FastAPI()

# Create directories if they don't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/qrcodes', exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include auth routes
app.include_router(auth_router)

# ========== Template Routes ==========

@app.get("/auth")
async def auth_page():
    """صفحة التسجيل/الدخول"""
    return FileResponse(Path("templates/auth.html"), media_type="text/html")

@app.get("/login")
async def login_page():
    """صفحة تسجيل الدخول"""
    return FileResponse(Path("templates/auth.html"), media_type="text/html")

@app.get("/register")
async def register_page():
    """صفحة إنشاء حساب"""
    return FileResponse(Path("templates/auth.html"), media_type="text/html")

@app.get("/create-report")
async def create_report_page():
    """صفحة إنشاء تقرير جديد"""
    return FileResponse(Path("templates/create_report.html"), media_type="text/html")

@app.get("/")
async def home():
    """الصفحة الرئيسية"""
    return FileResponse(Path("templates/auth.html"), media_type="text/html")
