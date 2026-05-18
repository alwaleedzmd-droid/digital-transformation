"""لوحة التحكم المحمية — للمدراء فقط.

الوصول: https://YOUR-APP.streamlit.app/dashboard
محمية بـ username/password من Streamlit secrets.
"""
from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.auth import login_gate, logout_button
from lib.db import delete_submission, fetch_all_submissions

st.set_page_config(
    page_title="لوحة التحكم — حصر التحول الرقمي",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# RTL + ستايل أساسي
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'IBM Plex Sans Arabic', sans-serif !important; direction: rtl; }
[data-testid="stSidebarNav"] { display: none !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px; }
h1, h2, h3, h4 { text-align: right; }
.stMetric { background:#fff; border-radius:10px; padding:14px 18px; border:.5px solid rgba(0,0,0,.08); }
div[data-testid="stMetricLabel"] { direction: rtl; }
.stDataFrame { direction: ltr; }  /* الجدول يبقى LTR للقراءة الأسهل */
.dash-header {
    background: linear-gradient(135deg, #0F6E56, #1D9E75); color:white;
    padding: 22px 28px; border-radius: 14px; margin-bottom: 22px;
}
.dash-header h1 { color:white !important; font-size: 24px; margin:0 0 4px; }
.dash-header p { color: rgba(255,255,255,.85); margin:0; font-size: 14px; }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────── المصادقة ─────────────────────────
if not login_gate():
    st.stop()

# ───────────────────────── واجهة اللوحة ─────────────────────────
with st.sidebar:
    st.markdown("### 📊 لوحة التحكم")
    st.caption("حصر التحول الرقمي")
    st.divider()
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    logout_button()
    st.divider()
    st.markdown("[← العودة للاستبيان](../)", unsafe_allow_html=True)

st.markdown(
    """
    <div class="dash-header">
        <h1>لوحة التحكم — حصر التحول الرقمي</h1>
        <p>المجموعة العقارية · نظرة شاملة على استجابات المدراء</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30, show_spinner="جاري تحميل البيانات...")
def _load() -> list[dict]:
    return fetch_all_submissions()


try:
    rows = _load()
except Exception as exc:
    st.error(f"تعذر الاتصال بقاعدة البيانات: {exc}")
    st.info("تأكد من إعداد `supabase.service_role_key` في Streamlit secrets.")
    st.stop()

if not rows:
    st.info("لا توجد استجابات بعد. شارك رابط الاستبيان مع المدراء وستظهر البيانات هنا.")
    st.stop()

df = pd.DataFrame(rows)
# تحويلات أساسية
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)

# ───────────────────────── KPIs ─────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("إجمالي الاستجابات", len(df))
k2.metric("متوسط درجة الاحتياج", f"{df['score'].mean():.0f}%")
k3.metric("عدد الإدارات", df["department"].nunique())
high_risk = (df["risk_level"] == "عالية").sum()
k4.metric("استجابات عالية الخطر", int(high_risk), delta=f"{high_risk/len(df)*100:.0f}%")

st.divider()

# ───────────────────────── الرسوم ─────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("توزيع مستوى المخاطر")
    risk_counts = df["risk_level"].fillna("غير محدد").value_counts().reset_index()
    risk_counts.columns = ["مستوى الخطر", "العدد"]
    color_map = {"عالية": "#E24B4A", "متوسطة": "#EF9F27", "منخفضة": "#1D9E75", "غير محدد": "#9B9A96"}
    fig = px.pie(
        risk_counts,
        names="مستوى الخطر",
        values="العدد",
        color="مستوى الخطر",
        color_discrete_map=color_map,
        hole=0.5,
    )
    fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("متوسط الدرجة لكل إدارة")
    dept_avg = df.groupby("department")["score"].agg(["mean", "count"]).reset_index()
    dept_avg.columns = ["الإدارة", "متوسط الدرجة", "العدد"]
    dept_avg = dept_avg.sort_values("متوسط الدرجة", ascending=True)
    fig = px.bar(
        dept_avg,
        x="متوسط الدرجة",
        y="الإدارة",
        orientation="h",
        text="متوسط الدرجة",
        color="متوسط الدرجة",
        color_continuous_scale=["#1D9E75", "#EF9F27", "#E24B4A"],
        range_color=[0, 100],
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    st.subheader("توزيع الكيانات")
    ent_counts = df["entity"].fillna("غير محدد").value_counts().reset_index()
    ent_counts.columns = ["الكيان", "العدد"]
    fig = px.bar(ent_counts, x="العدد", y="الكيان", orientation="h", text="العدد", color_discrete_sequence=["#0F6E56"])
    fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("الأنظمة الأكثر استخداماً")
    sys_flat: list[str] = []
    for s in df["systems"].fillna("").tolist():
        if isinstance(s, list):
            sys_flat.extend(s)
        elif isinstance(s, str) and s:
            sys_flat.extend([x.strip() for x in s.split(",")])
    if sys_flat:
        sys_counts = pd.Series(sys_flat).value_counts().reset_index()
        sys_counts.columns = ["النظام", "العدد"]
        sys_counts = sys_counts.sort_values("العدد", ascending=True)
        fig = px.bar(sys_counts, x="العدد", y="النظام", orientation="h", text="العدد", color_discrete_sequence=["#7F77DD"])
        fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات أنظمة")

st.divider()

# ───────────────────────── تحديات + جاهزية ─────────────────────────
c5, c6 = st.columns(2)

with c5:
    st.subheader("متوسط حدة التحديات")
    rating_map = {"منخفض": 1, "متوسط": 2, "عالي": 3}
    ch_sum: dict[str, list[int]] = {}
    for c in df["challenges"].fillna({}).tolist():
        if isinstance(c, dict):
            for ch, rating in c.items():
                ch_sum.setdefault(ch, []).append(rating_map.get(rating, 0))
    if ch_sum:
        ch_avg = pd.DataFrame(
            [{"التحدي": k, "المتوسط": round(sum(v) / len(v), 2)} for k, v in ch_sum.items()]
        ).sort_values("المتوسط", ascending=True)
        fig = px.bar(
            ch_avg,
            x="المتوسط",
            y="التحدي",
            orientation="h",
            text="المتوسط",
            color="المتوسط",
            color_continuous_scale=["#1D9E75", "#EF9F27", "#E24B4A"],
            range_color=[1, 3],
        )
        fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات تحديات")

with c6:
    st.subheader("جاهزية الفِرَق للتحول")
    ready_counts = df["readiness"].fillna("غير محدد").value_counts().reset_index()
    ready_counts.columns = ["الجاهزية", "العدد"]
    fig = px.bar(ready_counts, x="الجاهزية", y="العدد", text="العدد", color_discrete_sequence=["#5DCAA5"])
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="IBM Plex Sans Arabic"))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ───────────────────────── الجدول ─────────────────────────
st.subheader("سجل الاستجابات")
display_df = df[
    ["created_at", "name", "job_title", "department", "entity", "headcount", "score", "risk_level"]
].copy()
display_df.columns = ["التاريخ", "الاسم", "المسمى", "الإدارة", "الكيان", "الموظفون", "الدرجة", "الخطر"]
display_df["التاريخ"] = display_df["التاريخ"].dt.strftime("%Y-%m-%d %H:%M")

st.dataframe(display_df, use_container_width=True, hide_index=True, height=380)

# ───────────────────────── أدوات ─────────────────────────
exp_csv, exp_id = st.columns([1, 2])

with exp_csv:
    csv_buf = io.StringIO()
    csv_buf.write("﻿")  # BOM للعربية في Excel
    df_export = df.copy()
    df_export["systems"] = df_export["systems"].apply(
        lambda s: " | ".join(s) if isinstance(s, list) else (s or "")
    )
    df_export["challenges"] = df_export["challenges"].apply(
        lambda c: " | ".join(f"{k}={v}" for k, v in c.items()) if isinstance(c, dict) else ""
    )
    df_export["ai_use"] = df_export["ai_use"].apply(
        lambda a: " | ".join(a) if isinstance(a, list) else (a or "")
    )
    df_export.to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ تصدير CSV (Excel)",
        data=csv_buf.getvalue().encode("utf-8-sig"),
        file_name="digital-transformation-assessments.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp_id:
    with st.expander("🗑️ حذف استجابة محددة"):
        ids = df["id"].astype(str).tolist()
        labels = [f"{r['name']} — {r['department']} ({r['id'][:8]}...)" for _, r in df.iterrows()]
        choice = st.selectbox("اختر الاستجابة للحذف", options=range(len(ids)), format_func=lambda i: labels[i])
        if st.button("تأكيد الحذف", type="secondary"):
            try:
                delete_submission(ids[choice])
                st.cache_data.clear()
                st.success("تم الحذف")
                st.rerun()
            except Exception as exc:
                st.error(f"فشل الحذف: {exc}")

st.divider()

# ───────────────────────── تفاصيل استجابة ─────────────────────────
st.subheader("عرض تفاصيل استجابة")
if not df.empty:
    selected_idx = st.selectbox(
        "اختر استجابة لعرض كامل التفاصيل",
        options=range(len(df)),
        format_func=lambda i: f"{df.iloc[i]['name']} — {df.iloc[i]['department']} — درجة {df.iloc[i]['score']}%",
    )
    r = df.iloc[selected_idx]
    with st.container(border=True):
        cA, cB, cC = st.columns(3)
        cA.markdown(f"**الاسم:** {r['name']}\n\n**المسمى:** {r.get('job_title','—')}")
        cB.markdown(f"**الإدارة:** {r['department']}\n\n**الكيان:** {r['entity']}")
        cC.markdown(f"**الدرجة:** {r['score']}%\n\n**الخطر:** {r['risk_level']}")

        st.markdown("**الأنظمة المستخدمة:**")
        sys_list = r["systems"] if isinstance(r["systems"], list) else []
        st.write(" · ".join(sys_list) or "—")

        st.markdown("**العمليات اليومية:**")
        st.write(r.get("ops_main") or "—")

        st.markdown("**العمليات اليدوية:**")
        st.write(r.get("ops_manual") or "—")

        st.markdown("**التحديات (التقييم):**")
        ch = r.get("challenges")
        if isinstance(ch, dict) and ch:
            st.write(" · ".join(f"{k}: {v}" for k, v in ch.items()))
        else:
            st.write("—")

        st.markdown("**التطلعات:**")
        st.write(r.get("wishlist") or "—")

        st.markdown("**ملاحظات:**")
        st.write(r.get("notes") or "—")

        if r.get("ai_assessment"):
            st.markdown("**تقييم الذكاء الاصطناعي:**")
            st.info(r["ai_assessment"])
