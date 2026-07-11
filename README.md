# Check Service Scaffold — كامل جاهز للنشر

ملفّات المشروع: FastAPI backend, Rules engine, Celery worker, docker-compose لتشغيل محلي (Postgres, Redis, MinIO).

تشغيل محلي (Docker Compose)
1. انسخ .env.example إلى .env وعدّل القيم إذا رغبت.
2. ابنِ الصورة وابدأ الخدمات:
   docker compose up --build

3. افتح المستندات التفاعلية:
   http://localhost:8000/docs

بدون Docker (باستخدام الـPython محلياً)
- أنشئ env, ثبّت المتطلبات، وصِّل DATABASE_URL لقاعدة Postgres محلية أو استخدم SQLite مؤقتاً.

إنشاء repo ودفع الشيفرة (آلي)
- ثبت gh CLI وسجل دخول (gh auth login).
- شغّل:
  ./create_and_push.sh YOUR_GITHUB_USERNAME medical-reports

نشر سهل على Render (باستخدام Dockerfile)
1. ادخل إلى https://render.com وسجّل الدخول.
2. Connect GitHub → اختر المستودع الذي أنشأته.
3. Create → Web Service → اختر Docker
4. أضف متغيرات البيئة من .env (DATABASE_URL, CELERY_BROKER_URL, MINIO_*)
5. أنشئ Postgres Managed Database في Render واربط DATABASE_URL.
6. بعد الإنشاء ستحصل على رابط HTTPS لواجهة التطبيق.

ملاحظات أمنيّة قبل نشر عام
- استبدل بيانات الدخول الافتراضية (Postgres, MinIO).
- فعّل TLS وحماية الوصول (أضف auth / OIDC).
- شغّل اختبارات أمنية (SAST/DAST) قبل النشر.

لمساعدة إضافية
- أستطيع: أ) أرفع الملفات إلى repo لك لو أعطيتني اسم المستودع (إذا أنشأته) — سأقوم بالدفع نيابةً. ب) أو أرشدك خطوة بخطوة لربط Render ونشر الخدمة تلقائيًا. ج) أجهّز سكربت نشر Render عبر API (تحتاج Render API key) — أخبرني أي خيار تريده.
