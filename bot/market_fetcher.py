"""
yfinance로 S&P 500 / NASDAQ / DOW 종가·등락률 수집.

호출 시점에 따라 다른 값을 반환:
- 미국 장중: 직전 거래일 종가 + 오늘 실시간 가격
- 폐장: 직전 거래일 종가 + 그 전 거래일 종가 (등락률 계산용)

반환 형식 (Supabase market_status JSON과 일치):
{
  "sp500":  { "value": 5234.18, "change": 21.92, "change_pct": 0.42 },
  "nasdaq": { ... },
  "dow":    { ... },
  "as_of":  "05.11 마감"
}
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pytz

log = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")

TICKERS = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
}


def fetch_market_status() -> Optional[dict]:
    """yfinance로 3대 지수 정보 가져옴. 실패 시 None."""
    try:
        import yfinance as yf
    except ImportError:
        log.error("yfinance 미설치 — pip install yfinance")
        return None

    result = {}
    as_of_str = ""

    for key, ticker in TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")  # 5일치 (휴장 대비 여유)
            if len(hist) < 2:
                log.warning("%s: 데이터 부족 (%d행)", ticker, len(hist))
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            close = float(latest["Close"])
            prev_close = float(prev["Close"])
            change = close - prev_close
            change_pct = (change / prev_close) * 100

            result[key] = {
                "value": round(close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            }

            # as_of: 가장 최근 거래일 (ET 기준 월일)
            if not as_of_str:
                latest_date = hist.index[-1]
                # tz-naive로 올 수 있으니 strftime만 사용
                as_of_str = f"{latest_date.month:02d}.{latest_date.day:02d} 마감"

        except Exception as exc:
            log.warning("%s 수집 실패: %s", ticker, exc)

    if len(result) != 3:
        log.error("3대 지수 모두 못 가져옴 — market_status 누락")
        return None

    result["as_of"] = as_of_str or datetime.now(ET).strftime("%m.%d 마감")
    log.info(
        "시장 시황 수집 완료: S&P %s / NASDAQ %s / DOW %s",
        result["sp500"]["value"],
        result["nasdaq"]["value"],
        result["dow"]["value"],
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    import json
    print(json.dumps(fetch_market_status(), indent=2, ensure_ascii=False))
