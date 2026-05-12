// brief의 DB 스키마와 1:1 매칭되는 TypeScript 타입.

export type MarketTickerData = {
  value: number;
  change: number;
  change_pct: number;
};

export type MarketStatus = {
  sp500: MarketTickerData;
  nasdaq: MarketTickerData;
  dow: MarketTickerData;
  as_of?: string; // 종가 시각 (ET 기준 표시용)
};

export type BriefingItem = {
  title: string;
  body: string; // 4~5 문장
  source: string; // 표시는 "주요 외신" 일반화 (brief 명세)
};

export type SessionTime = "morning" | "evening";

export type Briefing = {
  id: string;
  session_date: string; // YYYY-MM-DD
  session_time: SessionTime;
  market_status: MarketStatus;
  briefing_intro: string;
  items: BriefingItem[]; // 노션의 모든 article (보통 10~15개)
  notion_url?: string; // 노션 페이지 전체 링크
  generated_at: string; // ISO
};

export type User = {
  id: string;
  google_id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  created_at: string;
  last_login: string | null;
};
