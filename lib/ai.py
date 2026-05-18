"""تقييم Claude AI الاختياري — يُخفى تلقائياً إذا لم يكن المفتاح متوفراً."""
from __future__ import annotations

import streamlit as st


def is_enabled() -> bool:
    try:
        key = st.secrets["anthropic"]["api_key"]
        return bool(key)
    except (KeyError, FileNotFoundError):
        return False


def _model() -> str:
    try:
        return st.secrets["anthropic"].get("model", "claude-sonnet-4-6")
    except (KeyError, FileNotFoundError):
        return "claude-sonnet-4-6"


def generate_assessment(payload: dict, score: int) -> str:
    """يولد تقييماً عربياً من 4 فقرات. يرجع نصاً فارغاً عند الفشل."""
    if not is_enabled():
        return ""

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=st.secrets["anthropic"]["api_key"])
        prompt = _build_prompt(payload, score)
        msg = client.messages.create(
            model=_model(),
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
    except Exception as exc:
        st.warning(f"تعذر توليد تقييم AI: {exc}")
        return ""


def _build_prompt(p: dict, score: int) -> str:
    systems = "، ".join(p.get("systems") or []) or "غير محدد"
    ai_use = "، ".join(p.get("ai_use") or []) or "غير محدد"
    challenges = ", ".join(f"{k}: {v}" for k, v in (p.get("challenges") or {}).items())

    return (
        "أنت مستشار تحول رقمي متخصص في القطاع العقاري السعودي.\n"
        f"الإدارة: {p.get('department','—')} | الكيان: {p.get('entity','—')}\n"
        f"الأنظمة: {systems}\n"
        f"العمليات: {p.get('ops_main','')}\n"
        f"العمليات اليدوية: {p.get('ops_manual','')}\n"
        f"SPOF: {p.get('spof','—')} | أنظمة للمهمة الواحدة: {p.get('sys_count','—')}\n"
        f"جاهزية البيانات: {p.get('data_ready','—')}\n"
        f"التحديات: {challenges}\n"
        f"الأتمتة المطلوبة: {p.get('wishlist','')}\n"
        f"جاهزية الفريق: {p.get('readiness','—')} | الجدول الزمني: {p.get('timeline','—')}\n"
        f"فرص AI: {ai_use}\n"
        f"درجة الاحتياج: {score}%\n\n"
        "اكتب تقييماً باللغة العربية في 4 فقرات:\n"
        "١. خلاصة الوضع الحالي\n"
        "٢. أبرز الثغرات الرقمية ومخاطرها\n"
        "٣. أهم 3 توصيات عملية مرتبة بالأولوية مع تحديد زمني\n"
        "٤. فرص الذكاء الاصطناعي الأكثر جدوى لهذه الإدارة تحديداً\n"
        "كن محدداً ومباشراً."
    )
