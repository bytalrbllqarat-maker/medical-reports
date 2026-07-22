from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

app = FastAPI()

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/qrcodes', exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve templates
@app.get("/create-report")
async def create_report_page():
    """صفحة إنشاء تقرير جديد"""
    return FileResponse(Path("templates/create_report.html"), media_type="text/html")

@app.get("/")
async def home():
    """الصفحة الرئيسية"""
    return FileResponse(Path("templates/create_report.html"), media_type="text/html")
