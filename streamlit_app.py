"""نموذج حصر التحول الرقمي — Streamlit (الصفحة العامة).

- متعدد الخطوات (6 خطوات)
- يدعم RTL
- يحفظ في Supabase عبر anon key
- لا يعرض لوحة التحكم للمستخدم النهائي
"""
from __future__ import annotations

import streamlit as st

from lib import ai
from lib.db import insert_submission
from lib.scoring import compute_score, risk_color, risk_level

st.set_page_config(
    page_title="حصر التحول الرقمي — المجموعة العقارية",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ───────────────────────── RTL + ستايل ─────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp, .main, section.main {
    font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    direction: rtl;
}
.stApp { background: #F7F6F2; }
[data-testid="stSidebarNav"], [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1rem !important; max-width: 820px; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    direction: rtl; text-align: right; font-family: 'IBM Plex Sans Arabic', sans-serif !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label, .stMultiSelect label {
    direction: rtl; text-align: right; width: 100%;
}
div[data-testid="stRadio"] > div, div[data-testid="stCheckbox"] > label { direction: rtl; }
.stButton button {
    font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    border-radius: 8px; font-weight: 500;
}
.stButton button[kind="primary"] { background: #1D9E75; border-color: #1D9E75; }
.stButton button[kind="primary"]:hover { background: #0F6E56; border-color: #0F6E56; }

/* بطاقة عنوان مخصصة */
.app-header {
    background: #0F6E56; color: white; padding: 18px 24px; border-radius: 14px;
    margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.app-header .logo { display:flex; align-items:center; gap:10px; }
.app-header .logo .icon {
    width: 38px; height: 38px; background: #5DCAA5; border-radius: 8px;
    display:flex; align-items:center; justify-content:center; font-size: 20px;
}
.app-header .logo .title { font-size: 15px; font-weight: 600; }
.app-header .logo .sub { font-size: 12px; color: rgba(255,255,255,.7); }
.app-header .pill {
    background: rgba(255,255,255,.18); color: white; font-size: 12px;
    padding: 6px 14px; border-radius: 99px;
}
.progress-track { height: 4px; background: rgba(0,0,0,.08); border-radius: 99px; margin-bottom: 20px; }
.progress-fill { height: 100%; background: #1D9E75; border-radius: 99px; transition: width .4s ease; }

.step-intro { margin-bottom: 18px; }
.step-badge {
    display:inline-flex; gap:6px; background:#E1F5EE; color:#0F6E56;
    font-size:12px; font-weight:500; padding:4px 12px; border-radius:99px; margin-bottom:8px;
}
.step-title { font-size: 22px; font-weight: 600; color: #1C1C1A; margin-bottom: 4px; }
.step-desc  { font-size: 14px; color: #6B6A65; line-height: 1.7; }

.card {
    background:#fff; border:.5px solid rgba(0,0,0,.1); border-radius:12px;
    padding:18px 22px; margin-bottom:14px;
}
.card-title {
    font-size:14px; font-weight:500; color:#1C1C1A;
    padding-bottom:12px; margin-bottom:14px;
    border-bottom:.5px solid rgba(0,0,0,.08);
}
.metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }
.metric {
    background:#F7F6F2; border-radius:10px; padding:14px;
}
.metric .lbl { font-size:11px; color:#9B9A96; text-transform:uppercase; letter-spacing:.5px; margin-bottom:4px; }
.metric .val { font-size:18px; font-weight:600; color:#1C1C1A; }
.risk-pill { display:inline-block; padding:5px 14px; border-radius:99px; font-size:13px; font-weight:500; }
.tag-list { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.tag-list span { background:#E1F5EE; color:#0F6E56; border-radius:6px; padding:3px 10px; font-size:12px; }
.ai-panel {
    background:#fff; border:1px solid rgba(0,0,0,.1); border-right:3px solid #7F77DD;
    border-radius:12px; padding:18px 22px; margin-top:14px;
}
.ai-panel .head { display:flex; align-items:center; gap:8px; margin-bottom:10px; font-weight:500; }
.ai-panel .head .badge { background:#EEEDFE; color:#3C3489; font-size:11px; padding:3px 10px; border-radius:99px; }
.ai-text { font-size:14px; color:#1C1C1A; line-height:1.85; white-space:pre-wrap; }
.success-banner {
    background:#E1F5EE; border:1px solid #1D9E75; border-radius:10px;
    padding:14px 18px; margin-top:14px;
}
.success-banner .text { font-size:14px; color:#0F6E56; font-weight:500; }
.success-banner .id   { font-size:11px; color:#1D9E75; font-family:monospace; margin-top:4px; }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────── حالة الجلسة ─────────────────────────
TOTAL_STEPS = 6
DEFAULTS = {
    "step": 1,
    "name": "",
    "job_title": "",
    "department": "",
    "entity": "",
    "headcount": "",
    "systems": [],
    "other_systems": "",
    "has_erp": "",
    "ops_main": "",
    "ops_manual": "",
    "spof": "",
    "sys_count": "",
    "challenges": {},
    "data_ready": "",
    "integration": "",
    "wishlist": "",
    "readiness": "",
    "timeline": "",
    "ai_use": [],
    "notes": "",
    "submitted": False,
    "submission_id": None,
    "submission_score": None,
    "submission_risk": None,
    "ai_assessment": "",
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


# ───────────────────────── ثوابت ─────────────────────────
DEPARTMENTS = [
    "إدارة العقارات والممتلكات",
    "المبيعات والعقود والتحصيل",
    "الصيانة والتشغيل",
    "المالية والمحاسبة والخزينة",
    "الموارد البشرية وشؤون الموظفين",
    "أخرى",
]
ENTITIES = [
    "الشركة القابضة",
    "شركة تابعة — العقارات",
    "شركة تابعة — الخدمات",
    "شركة تابعة — محطات الوقود",
    "أخرى",
]
HEADCOUNT = ["1–5", "6–15", "16–30", "أكثر من 30"]
SYSTEMS = [
    "نظام ERP مركزي",
    "Excel / جداول بيانات",
    "نظام إدارة العقارات",
    "CRM علاقات العملاء",
    "نظام محاسبة مستقل",
    "نظام الموارد البشرية",
    "نظام تذاكر الصيانة",
    "نظام إدارة المشاريع",
    "نظام محطات الوقود",
    "ملفات ورقية يدوية",
    "بريد إلكتروني فقط",
    "WhatsApp / مجموعات",
]
ERP_OPTIONS = ["نعم، ويعمل بشكل كامل", "نعم، لكنه محدود", "لا يوجد", "لا أعلم"]
SPOF_OPTIONS = ["نعم، بشكل واضح", "نعم، جزئياً", "لا"]
SYS_COUNT_OPTIONS = ["نظام واحد فقط", "2–3 أنظمة", "أكثر من 3", "لا يوجد نظام"]
DATA_READY_OPTIONS = ["نعم، منظمة ومركزية", "جزئياً، موزعة على ملفات", "لا، متفرقة وغير موثقة"]
READINESS_OPTIONS = ["جاهز ومتحمس", "يحتاج تدريب وتوجيه", "مقاومة متوقعة", "غير محدد"]
TIMELINE_OPTIONS = ["أقل من 6 أشهر", "6–12 شهراً", "1–2 سنة", "أكثر من سنتين"]
AI_USE_OPTIONS = [
    "التقييم العقاري والتسعير التلقائي",
    "الصيانة التنبؤية للأصول",
    "التقارير الذكية وتحليل البيانات",
    "Chatbot خدمة المستأجرين",
    "الكشف عن المخاطر والمتأخرات",
    "أتمتة العقود والوثائق",
]
CHALLENGES = [
    "تأخر في إعداد التقارير",
    "ازدواجية إدخال البيانات",
    "صعوبة التتبع والمتابعة",
    "غياب التكامل بين الأنظمة",
    "الاعتماد المفرط على الورق",
    "غياب لوحة بيانات موحدة",
]
RATING_OPTIONS = ["—", "منخفض", "متوسط", "عالي"]


# ───────────────────────── helpers ─────────────────────────
def _select_radio(label: str, options: list[str], key: str, required: bool = False) -> str:
    """Radio أفقي كـ chips. يحفظ في session_state[key]."""
    current = st.session_state.get(key, "")
    idx = options.index(current) if current in options else None
    val = st.radio(
        ("❗ " if required else "") + label,
        options,
        index=idx,
        key=f"_radio_{key}",
        horizontal=True,
        label_visibility="visible",
    )
    if val is not None:
        st.session_state[key] = val
    return st.session_state.get(key, "")


def _go(step: int) -> None:
    st.session_state.step = max(1, min(TOTAL_STEPS, step))
    st.rerun()


def _header() -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div class="logo">
                <div class="icon">🏢</div>
                <div>
                    <div class="title">حصر التحول الرقمي</div>
                    <div class="sub">المجموعة العقارية — تقييم الإدارات</div>
                </div>
            </div>
            <div class="pill">الخطوة {st.session_state.step} من {TOTAL_STEPS}</div>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{(st.session_state.step / TOTAL_STEPS) * 100:.0f}%"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _step_intro(badge: str, title: str, desc: str) -> None:
    st.markdown(
        f"""
        <div class="step-intro">
            <div class="step-badge">{badge}</div>
            <div class="step-title">{title}</div>
            <div class="step-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _nav_buttons(prev_step: int | None, next_label: str, on_next, can_back: bool = True) -> None:
    cols = st.columns([1, 2, 1])
    with cols[0]:
        if prev_step is not None and can_back:
            if st.button("→ السابق", key=f"back_{st.session_state.step}", use_container_width=True):
                _go(prev_step)
    with cols[2]:
        if st.button(next_label, key=f"next_{st.session_state.step}", type="primary", use_container_width=True):
            on_next()


# ───────────────────────── الخطوات ─────────────────────────
def step1() -> None:
    _step_intro("👤 الخطوة الأولى", "بيانات المدير والإدارة", "المعلومات الأساسية لمن يملأ هذا النموذج")

    st.markdown('<div class="card"><div class="card-title">👤 المعلومات الشخصية</div>', unsafe_allow_html=True)
    st.session_state.name = st.text_input(
        "الاسم الكامل *", value=st.session_state.name, placeholder="مثال: أحمد عبدالله الغامدي"
    )
    st.session_state.job_title = st.text_input(
        "المسمى الوظيفي", value=st.session_state.job_title, placeholder="مثال: مدير الإدارة المالية"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🏢 الإدارة والكيان</div>', unsafe_allow_html=True)
    _select_radio("الإدارة / القسم *", DEPARTMENTS, "department", required=True)
    _select_radio("الكيان / الشركة *", ENTITIES, "entity", required=True)
    _select_radio("عدد الموظفين في الإدارة", HEADCOUNT, "headcount")
    st.markdown("</div>", unsafe_allow_html=True)

    def go_next():
        if not st.session_state.name.strip():
            st.error("الاسم الكامل مطلوب")
            return
        if not st.session_state.department:
            st.error("اختر الإدارة")
            return
        if not st.session_state.entity:
            st.error("اختر الكيان")
            return
        _go(2)

    _nav_buttons(None, "التالي ←", go_next, can_back=False)


def step2() -> None:
    _step_intro(
        "🖥️ الخطوة الثانية",
        "الأنظمة التقنية الحالية",
        "حدد جميع الأنظمة والأدوات التي تستخدمها إدارتك — اختر كل ما ينطبق",
    )
    st.markdown('<div class="card"><div class="card-title">🖥️ الأنظمة المستخدمة</div>', unsafe_allow_html=True)
    st.session_state.systems = st.multiselect(
        "اختر الأنظمة (يمكن اختيار أكثر من واحد)",
        SYSTEMS,
        default=st.session_state.systems,
    )
    st.session_state.other_systems = st.text_input(
        "أنظمة أخرى (افصل بفاصلة)",
        value=st.session_state.other_systems,
        placeholder="مثال: نظام داخلي للمشتريات، Power BI",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">⚙️ نظام ERP</div>', unsafe_allow_html=True)
    _select_radio("هل يوجد نظام ERP مركزي حالياً؟ *", ERP_OPTIONS, "has_erp", required=True)
    st.markdown("</div>", unsafe_allow_html=True)

    def go_next():
        if not st.session_state.has_erp:
            st.error("اختر حالة نظام ERP")
            return
        _go(3)

    _nav_buttons(1, "التالي ←", go_next)


def step3() -> None:
    _step_intro(
        "⚙️ الخطوة الثالثة",
        "العمليات التشغيلية",
        "وصف دورات العمل اليومية وأبرز نقاط الألم في إدارتك",
    )
    st.markdown('<div class="card"><div class="card-title">📋 وصف العمليات</div>', unsafe_allow_html=True)
    st.session_state.ops_main = st.text_area(
        "أهم 3 عمليات تقوم بها إدارتك بشكل يومي/أسبوعي *",
        value=st.session_state.ops_main,
        placeholder="1- استلام طلبات الصيانة\n2- إعداد تقرير الإيرادات\n3- متابعة عقود الإيجار",
        height=120,
    )
    st.session_state.ops_manual = st.text_area(
        "ما أكثر العمليات استهلاكاً للوقت بشكل يدوي؟",
        value=st.session_state.ops_manual,
        placeholder="مثال: إعداد التقارير من ملفات Excel متعددة...",
        height=100,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">⚠️ نقاط الضعف</div>', unsafe_allow_html=True)
    _select_radio("هل توجد عمليات تعتمد على موظف بعينه؟ (SPOF)", SPOF_OPTIONS, "spof")
    _select_radio("كم نظاماً يحتاجه الموظف لإنجاز مهمة واحدة؟", SYS_COUNT_OPTIONS, "sys_count")
    st.markdown("</div>", unsafe_allow_html=True)

    def go_next():
        if not st.session_state.ops_main.strip():
            st.error("اذكر أهم العمليات اليومية/الأسبوعية")
            return
        _go(4)

    _nav_buttons(2, "التالي ←", go_next)


def step4() -> None:
    _step_intro(
        "📊 الخطوة الرابعة",
        "التحديات ومستوى التكامل",
        "قيّم حدة كل تحدٍّ وجاهزية بياناتك للتحول الرقمي",
    )

    st.markdown('<div class="card"><div class="card-title">📊 تقييم التحديات</div>', unsafe_allow_html=True)
    for ch in CHALLENGES:
        current = st.session_state.challenges.get(ch, "—")
        idx = RATING_OPTIONS.index(current) if current in RATING_OPTIONS else 0
        val = st.radio(ch, RATING_OPTIONS, index=idx, horizontal=True, key=f"_ch_{ch}")
        if val and val != "—":
            st.session_state.challenges[ch] = val
        elif ch in st.session_state.challenges and val == "—":
            st.session_state.challenges.pop(ch, None)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🗄️ البيانات والتكامل</div>', unsafe_allow_html=True)
    _select_radio("هل البيانات الحالية منظمة وجاهزة للتحول؟", DATA_READY_OPTIONS, "data_ready")
    st.session_state.integration = st.text_area(
        "هل يوجد ربط حالي بين إدارتك وإدارات أخرى؟",
        value=st.session_state.integration,
        placeholder="مثال: نرسل تقرير التحصيل للمالية أسبوعياً عبر البريد...",
        height=100,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    _nav_buttons(3, "التالي ←", lambda: _go(5))


def step5() -> None:
    _step_intro(
        "🚀 الخطوة الخامسة",
        "التطلعات وأولويات التحول",
        "رأيك في ما يجب أن يتغير أولاً وكيف ترى مستقبل إدارتك رقمياً",
    )

    st.markdown('<div class="card"><div class="card-title">⭐ الأولويات والجاهزية</div>', unsafe_allow_html=True)
    st.session_state.wishlist = st.text_area(
        "أهم 3 وظائف تتمنى أتمتتها أو تحسينها رقمياً",
        value=st.session_state.wishlist,
        placeholder="1- أتمتة إشعارات انتهاء العقود\n2- لوحة متابعة التحصيل\n3- تقارير المصروفات الآلية",
        height=120,
    )
    _select_radio("مستوى جاهزية فريقك لتبني نظام جديد", READINESS_OPTIONS, "readiness")
    _select_radio("الفترة الزمنية المتوقعة للأثر الملموس", TIMELINE_OPTIONS, "timeline")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🤖 فرص الذكاء الاصطناعي</div>', unsafe_allow_html=True)
    st.session_state.ai_use = st.multiselect(
        "أي تطبيقات AI ترى قيمتها في إدارتك؟",
        AI_USE_OPTIONS,
        default=st.session_state.ai_use,
    )
    st.session_state.notes = st.text_area(
        "ملاحظات إضافية", value=st.session_state.notes, placeholder="أي معلومات إضافية تود مشاركتها...", height=80
    )
    st.markdown("</div>", unsafe_allow_html=True)

    _nav_buttons(4, "مراجعة وإرسال ←", lambda: _go(6))


def step6() -> None:
    if not st.session_state.submitted:
        _submit_now()

    _step_intro(
        "✅ التقرير النهائي",
        "ملخص التقييم",
        "نتائج حصر الوضع الرقمي لإدارتك — تم حفظها تلقائياً في قاعدة البيانات",
    )

    all_systems = (st.session_state.systems or []) + _other_systems_list()
    score = st.session_state.submission_score or 0
    risk = st.session_state.submission_risk or "—"
    name_disp = st.session_state.name + (f" / {st.session_state.job_title}" if st.session_state.job_title else "")

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">✓ ملخص التقييم</div>
            <div class="metrics">
                <div class="metric"><div class="lbl">المدير</div><div class="val">{name_disp or '—'}</div></div>
                <div class="metric"><div class="lbl">الإدارة</div><div class="val">{st.session_state.department or '—'}</div></div>
                <div class="metric"><div class="lbl">الكيان</div><div class="val">{st.session_state.entity or '—'}</div></div>
                <div class="metric"><div class="lbl">عدد الموظفين</div><div class="val">{st.session_state.headcount or '—'}</div></div>
            </div>
            <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;margin-top:8px">
                <div>
                    <div style="font-size:11px;color:#9B9A96;text-transform:uppercase;letter-spacing:.5px">درجة الاحتياج الرقمي</div>
                    <div style="font-size:42px;font-weight:600;color:#0F6E56;line-height:1">{score}<span style="font-size:18px">%</span></div>
                </div>
                <div>
                    <div style="font-size:11px;color:#9B9A96;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">مستوى المخاطر</div>
                    <span class="risk-pill" style="background:{risk_color(risk)}22;color:{risk_color(risk)}">{risk}</span>
                </div>
                <div>
                    <div style="font-size:11px;color:#9B9A96;text-transform:uppercase;letter-spacing:.5px">الأنظمة المحصورة</div>
                    <div style="font-size:32px;font-weight:600">{len(all_systems)}</div>
                </div>
            </div>
            <hr style="border:none;border-top:.5px solid rgba(0,0,0,.08);margin:14px 0">
            <div style="font-size:12px;color:#9B9A96;margin-bottom:6px">الأنظمة:</div>
            <div class="tag-list">
                {''.join(f'<span>{s}</span>' for s in all_systems) or '<span style="background:transparent;color:#9B9A96">لم يتم تحديد أنظمة</span>'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ai.is_enabled() and st.session_state.ai_assessment:
        st.markdown(
            f"""
            <div class="ai-panel">
                <div class="head">
                    🧠 تقييم الذكاء الاصطناعي
                    <span class="badge">Claude AI</span>
                </div>
                <div class="ai-text">{st.session_state.ai_assessment}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.submission_id:
        st.markdown(
            f"""
            <div class="success-banner">
                <div class="text">✅ تم حفظ التقييم في قاعدة البيانات بنجاح</div>
                <div class="id">ID: {st.session_state.submission_id[:8]}... | الدرجة: {score}% | الخطر: {risk}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button("→ تعديل البيانات", use_container_width=True):
            st.session_state.submitted = False
            _go(5)
    with cols[2]:
        if st.button("📋 استبيان جديد", type="primary", use_container_width=True):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)()
            st.session_state.step = 1
            st.rerun()


# ───────────────────────── إرسال ─────────────────────────
def _other_systems_list() -> list[str]:
    raw = st.session_state.other_systems or ""
    return [s.strip() for s in raw.replace("،", ",").split(",") if s.strip()]


def _submit_now() -> None:
    all_systems = list(st.session_state.systems or []) + _other_systems_list()
    payload = {
        "name": st.session_state.name,
        "job_title": st.session_state.job_title,
        "department": st.session_state.department,
        "entity": st.session_state.entity,
        "headcount": st.session_state.headcount,
        "systems": all_systems,
        "has_erp": st.session_state.has_erp,
        "ops_main": st.session_state.ops_main,
        "ops_manual": st.session_state.ops_manual,
        "spof": st.session_state.spof,
        "sys_count": st.session_state.sys_count,
        "challenges": st.session_state.challenges,
        "data_ready": st.session_state.data_ready,
        "integration": st.session_state.integration,
        "wishlist": st.session_state.wishlist,
        "readiness": st.session_state.readiness,
        "timeline": st.session_state.timeline,
        "ai_use": st.session_state.ai_use,
        "notes": st.session_state.notes,
    }
    score = compute_score(payload)
    risk = risk_level(score)
    payload["score"] = score
    payload["risk_level"] = risk

    ai_text = ""
    if ai.is_enabled():
        with st.spinner("جاري توليد التقييم الذكي..."):
            ai_text = ai.generate_assessment(payload, score)
    payload["ai_assessment"] = ai_text
    st.session_state.ai_assessment = ai_text

    try:
        record = insert_submission(payload)
        st.session_state.submission_id = record.get("id")
        st.session_state.submission_score = score
        st.session_state.submission_risk = risk
        st.session_state.submitted = True
    except Exception as exc:
        st.error(f"تعذر حفظ الاستجابة في قاعدة البيانات: {exc}")
        st.session_state.submission_score = score
        st.session_state.submission_risk = risk
        st.session_state.submitted = True


# ───────────────────────── راوتر ─────────────────────────
_header()
{
    1: step1,
    2: step2,
    3: step3,
    4: step4,
    5: step5,
    6: step6,
}[st.session_state.step]()
