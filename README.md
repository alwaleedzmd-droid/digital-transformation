# 🏢 حصر التحول الرقمي — Streamlit + Supabase

نموذج تقييم الإدارات للمجموعة العقارية، مبني بـ Streamlit مع قاعدة بيانات Supabase ولوحة تحكم محمية.

## 📁 هيكل المشروع

```
digital-transformation-streamlit/
├── streamlit_app.py            ← الصفحة العامة (الاستبيان) — لا تتطلب دخول
├── pages/
│   └── dashboard.py            ← لوحة التحكم — محمية بـ username/password
├── lib/
│   ├── db.py                   ← عميل Supabase (anon للنموذج، service_role للوحة)
│   ├── scoring.py              ← حساب الدرجة ومستوى المخاطر
│   ├── auth.py                 ← مصادقة لوحة التحكم
│   └── ai.py                   ← تقييم Claude AI الاختياري
├── supabase/
│   └── schema.sql              ← جدول البيانات + RLS policies
├── .streamlit/
│   ├── config.toml             ← الثيم وإخفاء الـ sidebar nav
│   └── secrets.toml.example    ← نموذج للأسرار (انسخه إلى secrets.toml)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 خطوات النشر الكاملة

### 1️⃣ إنشاء مشروع Supabase

1. اذهب إلى [supabase.com](https://supabase.com/dashboard) وسجّل الدخول
2. **New project** → اختر اسماً (مثلاً `digital-transformation`) واختر منطقة قريبة (`Frankfurt` أو `Bahrain` للسعودية)
3. أنشئ كلمة سر قاعدة بيانات قوية واحفظها
4. انتظر ~2 دقيقة حتى يكتمل الإعداد

#### إنشاء الجدول

1. من القائمة الجانبية اختر **SQL Editor → New query**
2. الصق محتوى ملف [supabase/schema.sql](supabase/schema.sql) كاملاً
3. اضغط **Run** — سيُنشئ الجدول مع سياسات RLS تحمي البيانات

#### الحصول على المفاتيح

من **Project Settings → API**:
- `Project URL` → ضعها في `secrets.toml` تحت `supabase.url`
- `anon public` key → ضعها تحت `supabase.anon_key` (للنموذج العام)
- `service_role` key 🔴 **سرية** → ضعها تحت `supabase.service_role_key` (للوحة التحكم فقط)

> ⚠️ **مفتاح `service_role` يتجاوز RLS ويعطي صلاحيات كاملة** — لا تضعه في كود الواجهة ولا ترفعه على Git. Streamlit Secrets آمنة لأنها على الخادم.

---

### 2️⃣ رفع المشروع على GitHub (Private)

```powershell
cd "c:\Users\adaldawsari\Downloads\استبيان\digital-transformation-streamlit"

# 1. تهيئة git
git init
git add .
git commit -m "Initial commit: Streamlit + Supabase"
git branch -M main

# 2. أنشئ repo خاص على GitHub.com (بدون README/license)
#    ثم اربط:
git remote add origin https://github.com/USERNAME/digital-transformation.git
git push -u origin main
```

> 💡 إذا لم يكن لديك GitHub CLI، يمكنك إنشاء الـ repo من الواجهة:
> [github.com/new](https://github.com/new) → الاسم: `digital-transformation` → ✅ Private → Create
>
> أو باستخدام `gh` CLI:
> ```powershell
> gh repo create digital-transformation --private --source=. --remote=origin --push
> ```

---

### 3️⃣ النشر على Streamlit Cloud

1. اذهب إلى [share.streamlit.io](https://share.streamlit.io) وسجّل الدخول بـ GitHub
2. اضغط **New app**
3. اختر الـ repo `digital-transformation` والـ branch `main`
4. **Main file path:** `streamlit_app.py`
5. اضغط **Advanced settings → Secrets** والصق محتوى `secrets.toml.example` بعد تعبئته:

```toml
[supabase]
url = "https://abcdefgh.supabase.co"
anon_key = "eyJhbGciOiJIUzI1Ni..."
service_role_key = "eyJhbGciOiJIUzI1Ni..."

[dashboard]
username = "admin"
password = "ضع-كلمة-مرور-قوية"

[anthropic]
api_key = ""  # اتركها فارغة لإخفاء تقييم AI، أو ضع مفتاح Anthropic لتفعيله
model = "claude-sonnet-4-6"
```

6. اضغط **Deploy** — سيستغرق ~3 دقائق

---

## 🔗 الروابط بعد النشر

| الصفحة | الرابط | الوصول |
|--------|--------|--------|
| 📋 نموذج الاستبيان | `https://YOUR-APP.streamlit.app/` | عام — يُشارَك مع المدراء |
| 📊 لوحة التحكم | `https://YOUR-APP.streamlit.app/dashboard` | محمي بـ username/password |

> 🔒 المستخدم الذي يعبئ الاستبيان لا يرى رابط لوحة التحكم في الواجهة. الرابط مخفي يدوياً (sidebar معطّل) ويجب على المدير زيارته مباشرة بإضافة `/dashboard` للـ URL.

---

## 🧪 التشغيل المحلي (للتطوير)

```powershell
# 1. تثبيت Python 3.10+ و pip

# 2. بيئة افتراضية
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. التبعيات
pip install -r requirements.txt

# 4. الأسرار
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
# عبّئ القيم الحقيقية

# 5. تشغيل
streamlit run streamlit_app.py
```

افتح:
- الاستبيان: http://localhost:8501
- لوحة التحكم: http://localhost:8501/dashboard

---

## 🔐 الأمان

- **RLS مفعّل** على Supabase — الزائر العادي يمكنه INSERT فقط (لا قراءة، لا تعديل، لا حذف)
- **`service_role` key** يبقى في Streamlit Secrets، لا يصل أبداً للمتصفح
- **لوحة التحكم** خلف username/password (مخزن في secrets، يُستخدم `hmac.compare_digest`)
- **التنقل الجانبي مُعطّل** على الصفحة العامة (`showSidebarNavigation = false`) — المستخدم العادي لا يرى رابط الـ dashboard
- **لا توجد API endpoints مفتوحة** — كل شيء يمر عبر Streamlit + Supabase REST

---

## 📊 ما الذي يُحفظ لكل مدير؟

كل استجابة تُخزَّن كصف واحد في جدول `submissions` يحوي:

- بيانات المدير (اسم، مسمى، إدارة، كيان، عدد موظفين)
- الأنظمة المستخدمة (JSON array) + حالة ERP
- العمليات (يومية، يدوية) + SPOF + عدد الأنظمة للمهمة
- تقييم 6 تحديات (JSON object) + جاهزية البيانات + التكامل
- التطلعات + جاهزية الفريق + الجدول الزمني
- فرص AI المختارة (JSON array) + ملاحظات
- **المحسوب:** درجة الاحتياج (0–100)، مستوى الخطر، نص تقييم AI

---

## 💡 ملاحظات

- يمكن تغيير الثيم من [.streamlit/config.toml](.streamlit/config.toml)
- لإضافة مستخدمين متعددين للوحة التحكم، استبدل `lib/auth.py` بـ `streamlit-authenticator`
- النسخ الاحتياطي: من Supabase Dashboard → Database → Backups (تلقائي يومياً للخطة المدفوعة)
- لتحديث التطبيق: `git push` فقط، Streamlit Cloud يعيد النشر تلقائياً

---

## 🆘 استكشاف الأخطاء

| المشكلة | الحل |
|---------|-----|
| "تعذر الاتصال بقاعدة البيانات" في الـ dashboard | تأكد من `supabase.service_role_key` في secrets |
| النموذج لا يحفظ | تأكد من `supabase.anon_key` ومن تشغيل `schema.sql` |
| تقييم AI لا يظهر | اتركه فارغاً لإخفائه، أو ضع مفتاح Anthropic صحيح |
| ظهور رابط dashboard في الـ sidebar | تأكد من `showSidebarNavigation = false` في `config.toml` |
