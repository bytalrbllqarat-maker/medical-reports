# 🏥 منصة التقارير الطبية - Medical Reports Platform

## نظرة عامة
منصة شاملة وحديثة لإدارة التقارير الطبية مع نظام باركود QR ورابط مشاركة آمن.

## ✨ الميزات الرئيسية

### 📋 إدارة التقارير
- ✅ إنشاء وتعديل وحذف التقارير
- ✅ تتبع حالة التقارير (قيد المراجعة، موثق، مرفوض)
- ✅ تخزين آمن لبيانات المريض
- ✅ تصفية وبحث متقدم

### 🎯 نظام QR Code
- ✅ توليد QR Code تلقائي لكل تقرير
- ✅ تحميل QR Code بصيغ مختلفة (PNG, SVG)
- ✅ دعم Base64 للعرض المباشر

### 🔗 رابط المشاركة الآمن
- ✅ روابط فريدة وآمنة لكل تقرير
- ✅ صلاحية انتهاء صريحة
- ✅ عد للزيارات والوصول
- ✅ صفحة عرض جميلة وسهلة الاستخدام

### 📊 لوحة التحكم
- ✅ إحصائيات فورية
- ✅ رسوم بيانية توضيحية
- ✅ جداول بيانات متفاعلة
- ✅ تصدير البيانات

### 🔐 الأمان
- ✅ مصادقة JWT
- ✅ تشفير كلمات المرور بـ bcrypt
- ✅ CORS محمي
- ✅ معالجة الأخطاء الشاملة

---

## 🚀 البدء السريع

### المتطلبات
- Docker و Docker Compose
- Python 3.11+ (للتطوير المحلي)
- Git

### التثبيت باستخدام Docker

```bash
# 1. استنساخ المستودع
git clone https://github.com/yourusername/medical-reports.git
cd medical-reports

# 2. إنشاء ملف .env
cp .env.example .env

# 3. تشغيل Docker Compose
docker compose up --build

# 4. الوصول إلى التطبيق
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### التثبيت المحلي (بدون Docker)

```bash
# 1. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # على Windows: venv\Scripts\activate

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. تعيين متغيرات البيئة
cp .env.example .env

# 4. تشغيل التطبيق
uvicorn main:app --reload
```

---

## 📚 واجهة API

### 1. إنشاء تقرير جديد
```bash
POST /api/reports
Content-Type: application/json
Authorization: Bearer <token>

{
  "patient_name": "محمد علي",
  "patient_age": 30,
  "patient_blood_type": "O+",
  "report_type": "فحص عام",
  "diagnosis": "سليم",
  "medications": ["الأسبرين"],
  "allergies": ["البنسلين"],
  "notes": "متابعة دورية"
}
```

### 2. الحصول على قائمة التقارير
```bash
GET /api/reports?skip=0&limit=10
Authorization: Bearer <token>
```

### 3. الحصول على QR Code
```bash
GET /api/reports/{report_id}/qrcode
Authorization: Bearer <token>
```

### 4. الحصول على رابط المشاركة
```bash
GET /api/reports/{report_id}/qrcode-base64
Authorization: Bearer <token>

Response:
{
  "report_id": "...",
  "qr_code_base64": "data:image/png;base64,...",
  "share_url": "http://localhost:8000/share/...",
  "format": "image/png"
}
```

### 5. عرض التقرير المشارك
```bash
GET /share/{share_token}
# يعيد صفحة HTML جميلة
```

### 6. الإحصائيات
```bash
GET /api/stats
Authorization: Bearer <token>
```

---

## 🎨 واجهة المستخدم

### صفحات الواجهة

1. **لوحة التحكم** (`admin-dashboard.html`)
   - إحصائيات شاملة
   - جدول التقارير الأخيرة
   - رسوم بيانية توضيحية
   - إجراءات سريعة

2. **صفحة عرض التقرير** (تُوَلَّد تلقائياً)
   - عرض جميل للتقرير
   - QR Code للتحقق
   - خيارات الطباعة

3. **صفحة التحقق** (الصفحة الأصلية)
   - نموذج البحث عن التقرير
   - عرض بيانات المريض
   - معلومات التشخيص والأدوية

---

## 🗄️ هيكل قاعدة البيانات

```sql
-- المستخدمون
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE,
    username VARCHAR UNIQUE,
    full_name VARCHAR,
    hashed_password VARCHAR,
    is_active BOOLEAN,
    is_admin BOOLEAN,
    role VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- التقارير
CREATE TABLE reports (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    patient_name VARCHAR,
    patient_age INTEGER,
    patient_blood_type VARCHAR,
    report_type VARCHAR,
    diagnosis TEXT,
    medications JSON,
    allergies JSON,
    notes TEXT,
    status VARCHAR,
    share_url VARCHAR UNIQUE,
    share_token VARCHAR UNIQUE,
    qr_code_path VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- روابط المشاركة
CREATE TABLE share_links (
    id VARCHAR PRIMARY KEY,
    report_id VARCHAR REFERENCES reports(id),
    token VARCHAR UNIQUE,
    is_active BOOLEAN,
    access_count INTEGER,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

---

## 🔧 ملفات التكوين

### .env
```bash
DATABASE_URL=postgresql://user:password@db:5432/medical_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
BASE_URL=http://localhost:8000
QR_CODE_SIZE=300
```

### requirements.txt
يتضمن:
- FastAPI
- SQLAlchemy
- psycopg2 (لـ PostgreSQL)
- qrcode (لـ QR Codes)
- Pillow (لمعالجة الصور)
- python-jose (لـ JWT)
- passlib (لتشفير كلمات المرور)
- Celery (للعمليات غير المتزامنة)

---

## 📱 الواجهات الرئيسية

### 1. Dashboard
```
┌─────────────────────────────────────────────────────┐
│  شريط العنوان (بحث، إخطارات، ملف المستخدم)         │
├──────────────────────────────────────────────────────┤
│ القائمة │                                            │
│الجانبية │         محتوى لوحة التحكم                  │
│         │  - بطاقات الإحصائيات                       │
│         │  - جدول التقارير                          │
│         │  - رسوم بيانية                            │
└──────────────────────────────────────────────────────┘
```

### 2. Share Report
```
┌──────────────────────────────────┐
│   منصة تشيك - التقرير الطبي      │
│  ┌────────────────────────────┐  │
│  │      QR CODE هنا           │  │
│  └────────────────────────────┘  │
│  المريض: محمد علي               │
│  العمر: 30 سنة                  │
│  الفصيلة: O+                    │
│  التشخيص: سليم                  │
│  [🖨️ اطبع التقرير]              │
└──────────────────────────────────┘
```

---

## 🎯 حالات الاستخدام

### 1. إنشاء تقرير طبي
```
 الطبيب → ينشئ التقرير → نظام يولد QR Code → يحصل على رابط المشاركة
```

### 2. مشاركة التقرير
```
 الطبيب → ينسخ الرابط/QR → يرسله للمريض → المريض يعرضه
```

### 3. التحقق من التقرير
```
 مستخدم → يمسح QR Code → يشاهد التقرير → يطبعه
```

---

## 🚀 نشر على Render

### الخطوات:
1. ادخل إلى [Render.com](https://render.com)
2. اختر "New" → "Web Service"
3. اختر "Docker" كبيئة التشغيل
4. أضف متغيرات البيئة
5. انتظر النشر

```bash
# اختياري: استخدام CLI
render deploy --name medical-reports
```

---

## 📊 الإحصائيات والمراقبة

### معايير الأداء
- وقت الاستجابة: < 200ms
- معدل النجاح: > 99.9%
- التوفر: 99.9%

### السجلات
```bash
# عرض السجلات
docker compose logs -f api

# تصفية السجلات
docker compose logs -f api | grep ERROR
```

---

## 🔐 الأمان

### أفضل الممارسات المطبقة
- ✅ حماية CSRF
- ✅ تحقق JWT مصرح به
- ✅ تشفير كلمات المرور
- ✅ HTTPS في الإنتاج
- ✅ معالجة الأخطاء الآمنة
- ✅ معايرة مدخلات المستخدم

### قبل الإطلاق العام
```bash
# تغيير المفاتيح السرية
SECRET_KEY=generate-new-key-here

# تفعيل HTTPS
HTTPS_ONLY=true

# تغيير كلمات مرور قاعدة البيانات
POSTGRES_PASSWORD=strong-password
```

---

## 📞 الدعم والمساعدة

### التواصل
- 📧 البريد: support@medical-reports.app
- 🐛 الأخطاء: [Issues على GitHub](https://github.com/yourusername/medical-reports/issues)
- 💬 المناقشات: [Discussions على GitHub](https://github.com/yourusername/medical-reports/discussions)

### الموارد
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [QRCode Docs](https://pypi.org/project/qrcode/)

---

## 📄 الترخيص
MIT License - استخدم بحرية في المشاريع التجارية والشخصية

---

**صُنع بـ ❤️ من قبل فريق المنصة الطبية**
