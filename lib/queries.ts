/**
 * Supabase에서 브리핑 데이터를 읽는 쿼리 모음.
 *
 * 환경변수가 없거나 쿼리가 실패하면 lib/mockData.ts의 더미 데이터로 폴백.
 * → 로컬 개발/Phase 1처럼 mock으로도 페이지 잘 렌더됨.
 */

import { supabase, SUPABASE_CONFIGURED } from "./supabase";
import { Briefing, SessionTime } from "./types";
import {
  mockBriefings,
  getLatestBriefing as mockGetLatest,
  getBriefingByDate as mockGetByDate,
  getRecentBriefings as mockGetRecent,
} from "./mockData";

// Next.js 14 RSC 캐시: 60초마다 재검증
const REVALIDATE_SECONDS = 60;

// briefings 테이블 row → Briefing 타입
function rowToBriefing(row: any): Briefing {
  return {
    id: row.id,
    session_date: row.session_date,
    session_time: row.session_time as SessionTime,
    market_status: row.market_status ?? {
      sp500: { value: 0, change: 0, change_pct: 0 },
      nasdaq: { value: 0, change: 0, change_pct: 0 },
      dow: { value: 0, change: 0, change_pct: 0 },
    },
    briefing_intro: row.briefing_intro ?? "",
    items: Array.isArray(row.items) ? row.items : [],
    notion_url: row.notion_url ?? undefined,
    generated_at: row.generated_at,
  };
}

export async function getLatestBriefing(): Promise<Briefing> {
  if (!SUPABASE_CONFIGURED) return mockGetLatest();
  try {
    const { data, error } = await supabase
      .from("briefings")
      .select("*")
      .order("session_date", { ascending: false })
      .order("session_time", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) throw error;
    if (!data) return mockGetLatest();
    return rowToBriefing(data);
  } catch (e) {
    console.error("[queries] getLatestBriefing 실패, mock 폴백:", e);
    return mockGetLatest();
  }
}

export async function getBriefingByDate(
  date: string,
  session: SessionTime
): Promise<Briefing | null> {
  if (!SUPABASE_CONFIGURED) return mockGetByDate(date, session);
  try {
    const { data, error } = await supabase
      .from("briefings")
      .select("*")
      .eq("session_date", date)
      .eq("session_time", session)
      .maybeSingle();
    if (error) throw error;
    if (!data) {
      // DB에는 없지만 mock에는 있을 수도 (개발 중)
      return mockGetByDate(date, session);
    }
    return rowToBriefing(data);
  } catch (e) {
    console.error("[queries] getBriefingByDate 실패, mock 폴백:", e);
    return mockGetByDate(date, session);
  }
}

export async function getRecentBriefings(n = 6): Promise<Briefing[]> {
  if (!SUPABASE_CONFIGURED) return mockGetRecent(n);
  try {
    const { data, error } = await supabase
      .from("briefings")
      .select("*")
      .order("session_date", { ascending: false })
      .order("session_time", { ascending: false })
      .limit(n);
    if (error) throw error;
    if (!data || data.length === 0) return mockGetRecent(n);
    return data.map(rowToBriefing);
  } catch (e) {
    console.error("[queries] getRecentBriefings 실패, mock 폴백:", e);
    return mockGetRecent(n);
  }
}

export async function getAllBriefings(): Promise<Briefing[]> {
  if (!SUPABASE_CONFIGURED) return mockBriefings;
  try {
    const { data, error } = await supabase
      .from("briefings")
      .select("*")
      .order("session_date", { ascending: false })
      .order("session_time", { ascending: false })
      .limit(200);
    if (error) throw error;
    if (!data || data.length === 0) return mockBriefings;
    return data.map(rowToBriefing);
  } catch (e) {
    console.error("[queries] getAllBriefings 실패, mock 폴백:", e);
    return mockBriefings;
  }
}

// 페이지 캐싱 힌트 export (Next.js page에서 import 후 export 가능)
export const revalidate = REVALIDATE_SECONDS;
