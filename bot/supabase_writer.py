"""
Supabase에 브리핑 데이터 저장.

스키마: briefing.briefings (briefing 전용 스키마로 격리)
환경변수:
  SUPABASE_URL              - 프로젝트 URL (https://xxx.supabase.co)
  SUPABASE_SERVICE_ROLE_KEY - service_role key (RLS 우회. 쓰기 권한 필요)

저장하는 데이터 형태:
{
  "session_date": "2026-05-12",
  "session_time": "morning" | "evening",
  "market_status": { sp500: {...}, nasdaq: {...}, dow: {...}, as_of: "..." },
  "briefing_intro": "오늘은 ...",
  "items": [
    { "title": "...", "body": "...", "source": "주요 외신" },
    ... 5개
  ]
}
"""

from __future__ import annotations

import os
import logging
from typing import Optional

log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def _get_client():
    """supabase 클라이언트 반환. 미설치/미설정이면 None."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        log.warning("Supabase 환경변수 미설정 — DB 저장 스킵")
        return None
    try:
        from supabase import create_client
    except ImportError:
        log.error("supabase-py 미설치 — pip install supabase")
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def upsert_briefing(
    session_date: str,
    session_time: str,
    market_status: Optional[dict],
    briefing_intro: str,
    items: list,
    notion_url: Optional[str] = None,
) -> Optional[str]:
    """
    briefing.briefings 테이블에 upsert.

    같은 (session_date, session_time) 조합이 이미 있으면 덮어씀.
    성공 시 row id, 실패/스킵 시 None.
    """
    client = _get_client()
    if client is None:
        return None

    if session_time not in ("morning", "evening"):
        log.error("session_time은 'morning' 또는 'evening'이어야 함: %s", session_time)
        return None

    payload: dict = {
        "session_date": session_date,
        "session_time": session_time,
        "market_status": market_status,
        "briefing_intro": briefing_intro,
        "items": items,
    }
    if notion_url:
        payload["notion_url"] = notion_url

    try:
        # briefing 스키마의 briefings 테이블에 upsert
        # supabase-py의 .schema() 메서드로 스키마 지정
        resp = (
            client.schema("briefing")
            .table("briefings")
            .upsert(payload, on_conflict="session_date,session_time")
            .execute()
        )
        data = resp.data
        if data and len(data) > 0:
            row_id = data[0].get("id")
            log.info(
                "Supabase 저장 완료: %s/%s (id=%s, items=%d)",
                session_date, session_time, row_id, len(items),
            )
            return row_id
        else:
            log.warning("Supabase 응답에 data 없음: %s", resp)
            return None
    except Exception as exc:
        log.exception("Supabase 저장 실패: %s", exc)
        return None


def get_site_session(now_kst) -> tuple[str, str]:
    """
    현재 KST 시각으로 사이트 세션 결정.
    - 새벽 ~ 정오: morning (그날 아침 브리핑)
    - 오후 ~ 자정: evening (그날 저녁 브리핑)

    반환: (session_date YYYY-MM-DD, session_time)
    """
    date_str = now_kst.strftime("%Y-%m-%d")
    if now_kst.hour < 14:  # 14시(오후 2시) 이전이면 morning
        return date_str, "morning"
    else:
        return date_str, "evening"


if __name__ == "__main__":
    # 단독 테스트: 더미 데이터로 한 번 insert
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    test_id = upsert_briefing(
        session_date="2026-05-12",
        session_time="morning",
        market_status={
            "sp500": {"value": 5234.18, "change": 21.92, "change_pct": 0.42},
            "nasdaq": {"value": 16789.34, "change": 102.15, "change_pct": 0.61},
            "dow": {"value": 38492.07, "change": -57.84, "change_pct": -0.15},
            "as_of": "05.11 마감",
        },
        briefing_intro="테스트 브리핑입니다.",
        items=[
            {"title": "테스트 제목 1", "body": "본문...", "source": "주요 외신"},
        ],
    )
    print("inserted id:", test_id)
