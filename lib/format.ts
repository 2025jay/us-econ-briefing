// 표시용 포매팅 헬퍼

import { SessionTime } from "./types";

export function formatSessionLabel(session: SessionTime): string {
  return session === "morning" ? "아침 08:30" : "저녁 20:30";
}

export function formatDateKor(dateStr: string): string {
  // "2026-05-12" → "2026.05.12 MON"
  const d = new Date(dateStr + "T00:00:00+09:00");
  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}.${m}.${day} ${days[d.getDay()]}`;
}

export function formatNumber(n: number): string {
  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatChangePct(pct: number): string {
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

// 액센트 컬러 5색 순환 인덱스
export const ACCENT_CLASSES = [
  "bg-accent-pink",
  "bg-accent-lime",
  "bg-accent-yellow",
  "bg-accent-purple",
  "bg-accent-blue",
] as const;

export function accentByIndex(i: number): string {
  return ACCENT_CLASSES[i % ACCENT_CLASSES.length];
}
