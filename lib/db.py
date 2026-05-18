"""عميل Supabase — يدعم وضعين:
   - anon: للنموذج العام (INSERT فقط)
   - service: للوحة التحكم (يتجاوز RLS)
"""
from __future__ import annotations

import streamlit as st
from supabase import Client, create_client


def _get_secret(section: str, key: str, default: str = "") -> str:
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError):
        return default


@st.cache_resource(show_spinner=False)
def get_public_client() -> Client | None:
    """عميل بمفتاح anon — للنموذج العام."""
    url = _get_secret("supabase", "url")
    key = _get_secret("supabase", "anon_key")
    if not url or not key:
        return None
    return create_client(url, key)


@st.cache_resource(show_spinner=False)
def get_admin_client() -> Client | None:
    """عميل بمفتاح service_role — للوحة التحكم فقط."""
    url = _get_secret("supabase", "url")
    key = _get_secret("supabase", "service_role_key")
    if not url or not key:
        return None
    return create_client(url, key)


def insert_submission(payload: dict) -> dict:
    """يحفظ استجابة جديدة في Supabase ويعيد السجل المُدرج."""
    client = get_public_client()
    if client is None:
        raise RuntimeError("لم يتم إعداد Supabase — راجع .streamlit/secrets.toml")
    res = client.table("submissions").insert(payload).execute()
    if not res.data:
        raise RuntimeError("فشل حفظ الاستجابة")
    return res.data[0]


def fetch_all_submissions() -> list[dict]:
    """يجلب كل الاستجابات — يتطلب service_role."""
    client = get_admin_client()
    if client is None:
        raise RuntimeError("لم يتم إعداد service_role_key")
    res = (
        client.table("submissions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def delete_submission(submission_id: str) -> None:
    client = get_admin_client()
    if client is None:
        raise RuntimeError("لم يتم إعداد service_role_key")
    client.table("submissions").delete().eq("id", submission_id).execute()
