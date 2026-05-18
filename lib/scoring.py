"""حساب درجة الاحتياج الرقمي ومستوى المخاطر — نفس منطق server.js الأصلي."""
from __future__ import annotations


def compute_score(payload: dict) -> int:
    s = 0
    has_erp = payload.get("has_erp") or ""
    if "لا" in has_erp:
        s += 25
    elif "محدود" in has_erp:
        s += 12

    sys_count = payload.get("sys_count") or ""
    if "أكثر" in sys_count:
        s += 20
    elif "2–3" in sys_count or "2-3" in sys_count:
        s += 10

    data_ready = payload.get("data_ready") or ""
    if "متفرقة" in data_ready:
        s += 20
    elif "جزئياً" in data_ready or "جزئيا" in data_ready:
        s += 10

    spof = payload.get("spof") or ""
    if "واضح" in spof:
        s += 15
    elif "جزئياً" in spof or "جزئيا" in spof:
        s += 8

    if len(payload.get("ops_manual") or "") > 40:
        s += 20

    return min(s, 100)


def risk_level(score: int) -> str:
    if score >= 70:
        return "عالية"
    if score >= 40:
        return "متوسطة"
    return "منخفضة"


def risk_color(level: str) -> str:
    return {"عالية": "#E24B4A", "متوسطة": "#EF9F27", "منخفضة": "#1D9E75"}.get(level, "#6B6A65")
