-- ─────────────────────────────────────────────────────────────
--  Digital Transformation Assessment — Supabase Schema
--  شغّل هذا الملف من: Supabase Dashboard → SQL Editor → New query
-- ─────────────────────────────────────────────────────────────

-- 1) جدول الاستجابات الرئيسي
create table if not exists public.submissions (
    id                uuid          primary key default gen_random_uuid(),
    created_at        timestamptz   not null    default now(),

    -- بيانات المدير
    name              text          not null,
    job_title         text,

    -- الإدارة والكيان
    department        text,
    entity            text,
    headcount         text,

    -- الأنظمة
    systems           jsonb         default '[]'::jsonb,
    has_erp           text,

    -- العمليات
    ops_main          text,
    ops_manual        text,
    spof              text,
    sys_count         text,

    -- التحديات والبيانات
    challenges        jsonb         default '{}'::jsonb,
    data_ready        text,
    integration       text,

    -- التطلعات
    wishlist          text,
    readiness         text,
    timeline          text,
    ai_use            jsonb         default '[]'::jsonb,
    notes             text,

    -- النتائج المحسوبة
    score             int           default 0,
    risk_level        text,
    ai_assessment     text
);

create index if not exists submissions_created_at_idx on public.submissions (created_at desc);
create index if not exists submissions_department_idx on public.submissions (department);
create index if not exists submissions_entity_idx     on public.submissions (entity);

-- 2) Row Level Security
--    - INSERT مسموح للجميع (anon key) عبر نموذج الاستبيان
--    - SELECT/UPDATE/DELETE ممنوع لـ anon ومسموح فقط لـ service_role (لوحة التحكم)
alter table public.submissions enable row level security;

drop policy if exists "anon_insert"  on public.submissions;
drop policy if exists "anon_no_read" on public.submissions;

-- يسمح للجمهور بالإرسال فقط (لا قراءة، لا تعديل، لا حذف)
create policy "anon_insert"
    on public.submissions
    for insert
    to anon
    with check (true);

-- ملاحظة: لا توجد policy SELECT لدور anon، إذن القراءة محظورة افتراضياً.
-- لوحة التحكم تستخدم service_role_key الذي يتجاوز RLS — يبقى في Streamlit Secrets فقط.

-- 3) (اختياري) View تجميعي للقراءة السريعة
create or replace view public.submissions_summary as
select
    id,
    created_at,
    name,
    job_title,
    department,
    entity,
    headcount,
    score,
    risk_level,
    has_erp,
    data_ready,
    readiness,
    timeline
from public.submissions
order by created_at desc;
