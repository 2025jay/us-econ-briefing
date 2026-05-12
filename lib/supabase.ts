/**
 * Supabase 클라이언트 (Server-side 전용).
 *
 * - 사이트는 SSR로 데이터 읽기만 함 → anon key로 충분
 * - briefing 스키마에 접근하려면 .schema("briefing") 명시
 * - 봇은 service_role key로 별도 (Python supabase-py에서 처리)
 */

import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

if (!url || !anonKey) {
  // 빌드 타임에는 비어있어도 OK (개발 중에는 mock fallback).
  // 런타임에 비면 fetch가 실패 → page에서 mock으로 fallback.
  console.warn(
    "[supabase] NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY 미설정 — mock 데이터로 폴백"
  );
}

export const supabase = createClient(url || "https://placeholder.supabase.co", anonKey || "placeholder", {
  auth: { persistSession: false },
  db: { schema: "briefing" },
});

export const SUPABASE_CONFIGURED = Boolean(url && anonKey);
