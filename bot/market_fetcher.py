"""
S&P 500 / NASDAQ / DOW 종가·등락률 수집.

기본: Stooq (https://stooq.com) — 무료, API key 불필요, EOD 데이터.
폴백: yfinance — Stooq 실패 시.

반환 형식 (Supabase market_status JSON):
{
  "sp500":  { "value": 5234.18, "change": 21.92, "change_pct": 0.42 },
  "nasdaq": { ... },
  "dow":    { ... },
  "as_of":  "05.11 마감"
}
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Optional

import pytz
import requests

log = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")

# Stooq 심볼 (US 지수)
STOOQ_TICKERS = {
    "sp500": "^spx",
    "nasdaq": "^ndq",
    "dow": "^dji",
}

YF_TICKERS = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
}


def _fetch_one_stooq(symbol: str) -> Optional[tuple[float, float, str]]:
    """
    Stooq에서 한 심볼의 최근 5일 일봉 CSV를 받아
    (latest_close, prev_close, latest_date_mmdd) 반환.
    """
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        text = resp.text
        if not text or "Date,Open,High,Low,Close" not in text:
            log.warning("Stooq %s: 예상치 못한 응답 형식", symbol)
            return None
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if len(rows) < 2:
            log.warning("Stooq %s: 데이터 부족", symbol)
            return None
        latest = rows[-1]
        prev = rows[-2]
        latest_close = float(latest["Close"])
        prev_close = float(prev["Close"])
        # Date 형식: YYYY-MM-DD
        d = latest["Date"]
        mmdd = f"{d[5:7]}.{d[8:10]}"
        return latest_close, prev_close, mmdd
    except Exception as exc:
        log.warning("Stooq %s 실패: %s", symbol, exc)
        return None


def _fetch_one_yfinance(symbol: str) -> Optional[tuple[float, float, str]]:
    """yfinance 폴백."""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if len(hist) < 2:
            return None
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        latest_close = float(latest["Close"])
        prev_close = float(prev["Close"])
        latest_date = hist.index[-1]
        mmdd = f"{latest_date.month:02d}.{latest_date.day:02d}"
        return latest_close, prev_close, mmdd
    except Exception as exc:
        log.warning("yfinance %s 실패: %s", symbol, exc)
        return None


def fetch_market_status() -> Optional[dict]:
    """3대 지수 시황 수집. Stooq → yfinance 순으로 시도."""
    result: dict = {}
    as_of_str = ""

    for key in ("sp500", "nasdaq", "dow"):
        data = _fetch_one_stooq(STOOQ_TICKERS[key])
        source = "Stooq"
        if data is None:
            data = _fetch_one_yfinance(YF_TICKERS[key])
            source = "yfinance"
        if data is None:
            log.error("%s: 모든 소스 실패", key)
            continue

        latest_close, prev_close, mmdd = data
        change = latest_close - prev_close
        change_pct = (change / prev_close) * 100
        result[key] = {
            "value": round(latest_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
        log.info(
            "%s (%s): %s (%+.2f, %+.2f%%)",
            key.upper(), source, result[key]["value"], change, change_pct,
        )
        if not as_of_str:
            as_of_str = f"{mmdd} 마감"

    if len(result) != 3:
        log.error("3대 지수 모두 못 가져옴")
        return None

    result["as_of"] = as_of_str or datetime.now(ET).strftime("%m.%d 마감")
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    import json
    print(json.dumps(fetch_market_status(), indent=2, ensure_ascii=False))
