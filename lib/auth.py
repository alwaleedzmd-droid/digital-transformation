"""مصادقة للوحة التحكم — يدعم مستخدمين متعددين من Streamlit secrets."""
from __future__ import annotations

from collections.abc import Mapping

import hmac
import streamlit as st


def _users() -> dict[str, str]:
    """يعيد قاموس {username: password} من secrets.

    يدعم شكلين في secrets.toml:
      1) متعدد المستخدمين:
         [dashboard.users]
         "Mohammed Ibrahim" = "..."
         "ALWALEED"         = "..."
      2) مستخدم واحد (الشكل القديم):
         [dashboard]
         username = "..."
         password = "..."
    """
    try:
        section = st.secrets["dashboard"]
    except (KeyError, FileNotFoundError):
        return {}

    # نجرّب جلب users كقاموس فرعي (Streamlit يستخدم AttrDict وليس dict)
    try:
        users_section = section["users"]
        if isinstance(users_section, Mapping):
            return {str(k): str(v) for k, v in users_section.items()}
    except (KeyError, TypeError):
        pass

    # السقوط للشكل القديم: مستخدم واحد
    try:
        u = section["username"]
        p = section["password"]
        return {str(u): str(p)} if u and p else {}
    except (KeyError, TypeError):
        return {}


def _check(username: str, password: str) -> bool:
    """تحقق من بيانات الدخول.

    - اسم المستخدم: غير حساس لحالة الأحرف ويتجاهل المسافات الإضافية في الأطراف
    - كلمة المرور: حساسة لحالة الأحرف (كما يجب)
    """
    users = _users()
    if not users or not username or not password:
        return False

    username_normalized = username.strip().casefold()

    matched = False
    for u, p in users.items():
        u_norm = u.strip().casefold()
        # مقارنة ثابتة الوقت لتجنب timing attacks
        if hmac.compare_digest(username_normalized, u_norm) and hmac.compare_digest(password, p):
            matched = True
    return matched


def login_gate() -> bool:
    """يعرض شاشة دخول. يرجع True إذا كان المستخدم مسجلاً."""
    if st.session_state.get("dashboard_authed"):
        return True

    st.markdown(
        """
        <div style="max-width:420px;margin:60px auto 24px;text-align:center">
            <div style="font-size:32px;margin-bottom:8px">🔒</div>
            <h2 style="margin:0 0 6px">لوحة التحكم</h2>
            <p style="color:#6B6A65;font-size:14px;margin:0">
                هذه الصفحة محمية — أدخل بيانات المدير للمتابعة
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("اسم المستخدم", key="login_user")
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            submitted = st.form_submit_button("دخول", use_container_width=True, type="primary")

    if submitted:
        if _check(username, password):
            st.session_state.dashboard_authed = True
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

    return False


def logout_button() -> None:
    if st.sidebar.button("تسجيل خروج", use_container_width=True):
        st.session_state.dashboard_authed = False
        st.rerun()
