# مستندات API للمصادقة والتسجيل

## 🔐 نقاط نهاية المصادقة

### 1. تسجيل الدخول

**Endpoint**
```
POST /api/auth/login
Content-Type: application/json
```

**طلب (Request)**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**رد (Response)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user123",
    "full_name": "محمد علي",
    "is_active": true,
    "role": "user"
  }
}
```

---

### 2. إنشاء حساب جديد

**Endpoint**
```
POST /api/auth/register
Content-Type: application/json
```

**طلب (Request)**
```json
{
  "full_name": "محمد علي",
  "username": "user123",
  "email": "user@example.com",
  "password": "password123"
}
```

**رد (Response)**
```json
{
  "message": "تم إنشاء الحساب بنجاح",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user123",
    "full_name": "محمد علي",
    "is_active": true,
    "role": "user"
  }
}
```

---

### 3. الحصول على بيانات المستخدم الحالي

**Endpoint**
```
GET /api/auth/me
Authorization: Bearer <token>
```

**رد (Response)**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "user123",
  "full_name": "محمد علي",
  "is_active": true,
  "role": "user"
}
```

---

### 4. تسجيل الخروج

**Endpoint**
```
POST /api/auth/logout
Authorization: Bearer <token>
```

**رد (Response)**
```json
{
  "message": "تم تسجيل الخروج بنجاح"
}
```

---

### 5. تحديث التوكن

**Endpoint**
```
POST /api/auth/refresh
Content-Type: application/json
```

**طلب (Request)**
```json
{
  "refresh_token": "token"
}
```

**رد (Response)**
```json
{
  "access_token": "new_token",
  "token_type": "bearer"
}
```

---

## ❌ رسائل الخطأ الشائعة

### 401 Unauthorized
```json
{
  "detail": "بيانات تسجيل الدخول غير صحيحة"
}
```

### 400 Bad Request
```json
{
  "detail": "البريد الإلكتروني مسجل بالفعل"
}
```

### 403 Forbidden
```json
{
  "detail": "حساب المستخدم معطل"
}
```

---

## 🎯 أمثلة الاستخدام

### JavaScript/Fetch

**تسجيل الدخول**
```javascript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
if (response.ok) {
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
}
```

**إنشاء حساب**
```javascript
const response = await fetch('/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    full_name: 'محمد علي',
    username: 'user123',
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
if (response.ok) {
  console.log('تم إنشاء الحساب بنجاح');
}
```

### cURL

**تسجيل الدخول**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

---

## 🔒 التخزين الآمن للتوكن

**في LocalStorage (أساسي)**
```javascript
localStorage.setItem('token', data.access_token);
const token = localStorage.getItem('token');
```

**في SessionStorage (محدود بالجلسة)**
```javascript
sessionStorage.setItem('token', data.access_token);
const token = sessionStorage.getItem('token');
```

**في Cookie (آمن جداً)**
```javascript
document.cookie = `token=${data.access_token}; path=/; max-age=3600; secure; samesite=strict`;
```

---

## 📋 المتطلبات الأمنية

- ✅ كلمة المرور يجب أن تكون 8 أحرف على الأقل
- ✅ تشفير bcrypt لكلمات المرور
- ✅ JWT tokens للمصادقة
- ✅ معالجة الأخطاء الآمنة
- ✅ التحقق من البريد الإلكتروني والاسم المستخدم
