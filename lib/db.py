"""عميل Supabase — يدعم وضعين:
   - anon: للنموذج العام (INSERT فقط)
   - service: للوحة التحكم (يتجاوز RLS)
"""
from __future__ import annotations

import streamlit as st
from supabase import Client, create_client


def _get_secret(section: str, key: str) -> str:
    """يقرأ قيمة من st.secrets ويرفع خطأ واضح إذا كانت مفقودة أو فارغة."""
    try:
        section_data = st.secrets[section]
    except (KeyError, FileNotFoundError):
        raise RuntimeError(
            f"الأسرار مفقودة: لم يتم العثور على القسم [{section}] في Streamlit Secrets. "
            "أضفها من: Streamlit Cloud → Manage app → Settings → Secrets"
        )

    try:
        val = section_data[key]
    except (KeyError, TypeError):
        raise RuntimeError(
            f"المفتاح '{section}.{key}' مفقود في Streamlit Secrets."
        )

    val = str(val).strip()
    if not val:
        raise RuntimeError(
            f"المفتاح '{section}.{key}' موجود لكنه فارغ — أضف قيمته في Streamlit Secrets."
        )
    return val


# ملاحظة: نستخدم @st.cache_resource لإعادة استخدام نفس الاتصال،
# لكن نرفع استثناءً عند الفشل بدلاً من إرجاع None، حتى يعيد Streamlit المحاولة
# بعد تحديث الأسرار (الاستثناءات لا تُخزّن في cache_resource).


@st.cache_resource(show_spinner=False)
def get_public_client() -> Client:
    """عميل بمفتاح anon — للنموذج العام."""
    url = _get_secret("supabase", "url")
    key = _get_secret("supabase", "anon_key")
    return create_client(url, key)


@st.cache_resource(show_spinner=False)
def get_admin_client() -> Client:
    """عميل بمفتاح service_role — للوحة التحكم فقط."""
    url = _get_secret("supabase", "url")
    key = _get_secret("supabase", "service_role_key")
    return create_client(url, key)


def insert_submission(payload: dict) -> dict:
    """يحفظ استجابة جديدة في Supabase ويعيد السجل المُدرج."""
    client = get_public_client()
    res = client.table("submissions").insert(payload).execute()
    if not res.data:
        raise RuntimeError("فشل حفظ الاستجابة في Supabase (استجابة فارغة)")
    return res.data[0]


def fetch_all_submissions() -> list[dict]:
    """يجلب كل الاستجابات — يتطلب service_role."""
    client = get_admin_client()
    res = (
        client.table("submissions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def delete_submission(submission_id: str) -> None:
    client = get_admin_client()
    client.table("submissions").delete().eq("id", submission_id).execute()
