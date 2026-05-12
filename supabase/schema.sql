-- ─────────────────────────────────────────────────────────────
-- 미국 경제 AI 브리핑 — Supabase 스키마 (briefing 전용)
-- ─────────────────────────────────────────────────────────────
-- 사용법:
--   1. Supabase 대시보드 → SQL Editor → New query
--   2. 아래 전체 붙여넣기 → Run
--   3. 이미 다른 용도로 쓰는 프로젝트여도 'briefing' 스키마로 격리되어 안전
--
-- 만약 처음부터 다시 깔고 싶다면 맨 위 한 줄 'DROP SCHEMA briefing CASCADE;'
-- 의 주석을 풀고 실행하세요 (기존 데이터 모두 삭제).
-- ─────────────────────────────────────────────────────────────

-- drop schema briefing cascade;

create schema if not exists briefing;

-- 1. 브리핑 본문
create table if not exists briefing.briefings (
  id uuid primary key default gen_random_uuid(),
  session_date date not null,
  session_time text not null check (session_time in ('morning', 'evening')),
  market_status jsonb,
    -- { sp500: {value, change, change_pct}, nasdaq: {...}, dow: {...}, as_of: text }
  briefing_intro text,
  items jsonb,
    -- [{ title, body, source }, ...]
  generated_at timestamptz default now(),
  unique (session_date, session_time)
);

create index if not exists briefings_session_date_idx
  on briefing.briefings (session_date desc, session_time desc);

-- 2. 사용자 (Phase 3 Google 로그인용)
create table if not exists briefing.users (
  id uuid primary key default gen_random_uuid(),
  google_id text unique not null,
  email text not null,
  name text,
  avatar_url text,
  created_at timestamptz default now(),
  last_login timestamptz
);

-- 3. 활동 로그 (선택)
create table if not exists briefing.activity_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references briefing.users(id) on delete cascade,
  action text,
  briefing_id uuid references briefing.briefings(id) on delete set null,
  created_at timestamptz default now()
);

create index if not exists activity_log_user_idx
  on briefing.activity_log (user_id, created_at desc);

-- ─────────────────────────────────────────────────────────────
-- RLS — 콘텐츠는 누구나 read, write는 service_role 키만
-- ─────────────────────────────────────────────────────────────
alter table briefing.briefings    enable row level security;
alter table briefing.users        enable row level security;
alter table briefing.activity_log enable row level security;

drop policy if exists "briefings public read" on briefing.briefings;
create policy "briefings public read"
  on briefing.briefings for select
  using (true);

drop policy if exists "users self read" on briefing.users;
create policy "users self read"
  on briefing.users for select
  using (auth.uid()::text = google_id or auth.role() = 'service_role');

drop policy if exists "activity self read" on briefing.activity_log;
create policy "activity self read"
  on briefing.activity_log for select
  using (
    user_id in (select id from briefing.users where google_id = auth.uid()::text)
    or auth.role() = 'service_role'
  );

-- ─────────────────────────────────────────────────────────────
-- API 노출 — PostgREST/supabase-js가 briefing 스키마에 접근 가능하게
-- ─────────────────────────────────────────────────────────────
-- Supabase 대시보드: Project Settings → API → Schema Exposure 에
-- 'briefing'을 추가해야 클라이언트에서 .schema('briefing') 로 접근 가능합니다.
-- (위 SQL 실행 후 한 번만 설정)

-- ─────────────────────────────────────────────────────────────
-- GRANTS — service_role/anon/authenticated 권한 부여
-- (이거 없으면 봇이 briefing 스키마에 INSERT 못함: 42501)
-- ─────────────────────────────────────────────────────────────
grant usage on schema briefing to anon, authenticated, service_role;
grant all on all tables in schema briefing to service_role;
grant select on all tables in schema briefing to anon, authenticated;
grant all on all sequences in schema briefing to service_role;
grant all on all routines in schema briefing to service_role;

-- 앞으로 새로 만들 객체에도 자동 적용
alter default privileges in schema briefing
  grant all on tables to service_role;
alter default privileges in schema briefing
  grant select on tables to anon, authenticated;
