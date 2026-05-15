"""
경제 뉴스 수집 & Claude 분석 -> 노션 브리핑 + 카카오톡 전송

매일 미국 동부시간(ET) 06:00, 12:00, 18:00, 00:00 자동 실행

20개 매체에서 우선순위 기반으로 RSS 뉴스를 최대 50건 수집하고,
Claude가 원문 기반 팩트 정리 후:
  - 노션 하위 페이지 브리핑 생성 (시황/뉴스 분석/출처)
  - 공유 링크 자동 생성
  - 카카오톡: 핵심 요약 + 노션 링크 전송

환경변수:
  ANTHROPIC_API_KEY   - Anthropic API 키
  KAKAO_REST_API_KEY  - 카카오 REST API 키
  NOTION_API_KEY      - Notion Integration 토큰
  NOTION_PAGE_ID      - 브리핑이 생성될 노션 상위 페이지 ID

실행:
  python news_bot.py          # 스케줄러 상시 실행
  python news_bot.py --now    # 즉시 1회 실행
  python news_bot.py --auth   # 카카오 인증만 수행
"""

import os
import re
import sys
import json
import logging
import time as _time
import webbrowser
from calendar import timegm
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs
from pathlib import Path

import pytz
import requests
import anthropic
import feedparser
from notion_client import Client as NotionClient

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from email.utils import parsedate_to_datetime

# ─── 로깅 ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("news_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─── 환경변수 ──────────────────────────────────────────────
ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "").strip()
KAKAO_REST_API_KEY  = os.environ.get("KAKAO_REST_API_KEY", "").strip()
# 클라우드(GitHub Actions)에선 파일 대신 env var로 refresh_token 주입
KAKAO_REFRESH_TOKEN_ENV = os.environ.get("KAKAO_REFRESH_TOKEN", "").strip()
NOTION_API_KEY      = os.environ.get("NOTION_API_KEY", "").strip()
NOTION_PAGE_ID      = os.environ.get("NOTION_PAGE_ID", "").strip()
# 사이트 URL — 카카오톡의 "전체 브리핑 보기" 링크에 사용
SITE_BASE_URL       = os.environ.get(
    "SITE_BASE_URL", "https://2025jay.github.io/USA-Economy"
).strip().rstrip("/")

# ─── 자동화 플래그 ─────────────────────────────────────────
# GitHub Actions cron이 직접 호출하므로 BlockingScheduler는 더이상 사용 안 함.
# 로컬 PC 수동 운영 시절 잔재. 클라우드에선 의미 없음.
AUTO_SCHEDULE = False
AUTO_CARDNEWS = False

# ─── 상수 ──────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
TOKEN_FILE = BASE_DIR / "kakao_token.json"
REDIRECT_URI = "http://127.0.0.1:9876/callback"
ET           = pytz.timezone("America/New_York")
KST          = pytz.timezone("Asia/Seoul")
MAX_ARTICLES = 50
MAX_PER_SOURCE = 10

KAKAO_AUTH_URL  = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL  = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
FALLBACK_URL    = SITE_BASE_URL

# 20개 매체 RSS (우선순위 순서)
RSS_FEEDS = [
    # 1순위
    {"name": "Bloomberg",    "url": "https://feeds.bloomberg.com/markets/news.rss",              "tier": 1},
    {"name": "WSJ",          "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",            "tier": 1},
    {"name": "Investing.com","url": "https://www.investing.com/rss/news.rss",                     "tier": 1},
    {"name": "FT",           "url": "https://www.ft.com/rss/home",                              "tier": 1},
    {"name": "CNBC",         "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html",     "tier": 1},
    # 2순위
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml",            "tier": 2},
    {"name": "Yahoo Finance","url": "https://finance.yahoo.com/news/rssindex",                   "tier": 2},
    {"name": "MarketWatch",  "url": "https://feeds.marketwatch.com/marketwatch/topstories",      "tier": 2},
    {"name": "The Guardian", "url": "https://www.theguardian.com/us/business/rss",               "tier": 2},
    {"name": "NY Times Biz", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "tier": 2},
    # 3순위
    {"name": "Business Insider", "url": "https://feeds.businessinsider.com/custom/all",          "tier": 3},
    {"name": "Seeking Alpha","url": "https://seekingalpha.com/feed.xml",                         "tier": 3},
    {"name": "Financial Post","url": "https://financialpost.com/feed",                            "tier": 3},
    {"name": "Nasdaq",       "url": "https://www.nasdaq.com/feed/rssoutbound",                   "tier": 3},
    {"name": "Morningstar",  "url": "https://www.morningstar.com/rss/rss.aspx?file=USNews",     "tier": 3},
    # 4순위
    {"name": "Motley Fool",  "url": "https://www.fool.com/feeds/index.aspx",                     "tier": 4},
    {"name": "Kiplinger",    "url": "https://www.kiplinger.com/rss/kiplinger.xml",               "tier": 4},
    {"name": "Investopedia", "url": "https://www.investopedia.com/feedbuilder/feed/getarticles/?tag=News", "tier": 4},
    {"name": "Financial Post","url": "https://financialpost.com/feed",                           "tier": 4},
    {"name": "The Economist","url": "https://www.economist.com/finance-and-economics/rss.xml",   "tier": 4},
]

DAY_NAMES_KR = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 카카오 OAuth
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    authorization_code: Optional[str] = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        code  = query.get("code", [None])[0]
        if code:
            _OAuthCallbackHandler.authorization_code = code
            self._respond(200, "인증 성공! 이 창을 닫아도 됩니다.")
        else:
            error = query.get("error_description", ["알 수 없는 오류"])[0]
            self._respond(400, f"인증 실패: {error}")

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<html><body><h2>{body}</h2></body></html>".encode())

    def log_message(self, *_):
        pass


def _open_kakao_login() -> str:
    _OAuthCallbackHandler.authorization_code = None
    auth_url = KAKAO_AUTH_URL + "?" + urlencode({
        "client_id": KAKAO_REST_API_KEY, "redirect_uri": REDIRECT_URI,
        "response_type": "code", "scope": "talk_message",
    })
    log.info("브라우저에서 카카오 로그인을 진행해 주세요...")
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", 9876), _OAuthCallbackHandler)
    server.timeout = 1
    deadline = _time.time() + 120
    while _OAuthCallbackHandler.authorization_code is None:
        if _time.time() > deadline:
            server.server_close()
            raise TimeoutError("카카오 로그인 대기 시간 초과 (120초)")
        server.handle_request()
    server.server_close()
    log.info("authorization code 수신 완료")
    return _OAuthCallbackHandler.authorization_code


def _raise_kakao_error(resp: requests.Response, context: str) -> None:
    try:
        body = resp.json()
        code = body.get("error_code") or body.get("error", "")
        desc = body.get("error_description", "")
        if code == "KOE101":
            hint = (
                "앱 키가 유효하지 않습니다. KAKAO_REST_API_KEY가 "
                "카카오 디벨로퍼스 REST API 키와 일치하는지 확인하세요."
            )
            raise RuntimeError(f"[{context}] Kakao {code}: {desc} — {hint}")
        raise RuntimeError(f"[{context}] Kakao {code}: {desc} (HTTP {resp.status_code})")
    except (ValueError, KeyError):
        resp.raise_for_status()


def _request_token(code: str) -> dict:
    resp = requests.post(KAKAO_TOKEN_URL, data={
        "grant_type": "authorization_code", "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": REDIRECT_URI, "code": code,
    }, timeout=15)
    if not resp.ok:
        _raise_kakao_error(resp, "토큰 발급")
    tokens = resp.json()
    if "error" in tokens:
        _raise_kakao_error(resp, "토큰 발급")
    log.info("access_token 발급 완료 (expires_in=%s초)", tokens.get("expires_in"))
    return tokens


def _refresh_access_token(refresh_token: str) -> dict:
    resp = requests.post(KAKAO_TOKEN_URL, data={
        "grant_type": "refresh_token", "client_id": KAKAO_REST_API_KEY,
        "refresh_token": refresh_token,
    }, timeout=15)
    if not resp.ok:
        _raise_kakao_error(resp, "토큰 갱신")
    data = resp.json()
    if "error" in data:
        _raise_kakao_error(resp, "토큰 갱신")
    return data


def _save_tokens(data: dict) -> None:
    try:
        TOKEN_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        # 클라우드(Actions)의 ephemeral FS에선 다음 실행에 안 살아남음. 로그만 남기고 계속.
        log.warning("토큰 파일 저장 실패 (클라우드 ephemeral FS면 정상): %s", exc)


def _load_tokens() -> Optional[dict]:
    # 클라우드: env var의 refresh_token으로 초기화 (파일 없어도 OK)
    if not TOKEN_FILE.exists():
        if KAKAO_REFRESH_TOKEN_ENV:
            log.info("kakao_token.json 없음 → 환경변수 KAKAO_REFRESH_TOKEN으로 초기화")
            return {"access_token": "", "refresh_token": KAKAO_REFRESH_TOKEN_ENV}
        return None
    return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))


def get_access_token() -> str:
    tokens = _load_tokens()
    if tokens is None:
        log.info("저장된 토큰 없음 -> 브라우저 로그인 시작")
        code = _open_kakao_login()
        tokens = _request_token(code)
        _save_tokens(tokens)
        return tokens["access_token"]
    try:
        refreshed = _refresh_access_token(tokens["refresh_token"])
        tokens["access_token"] = refreshed["access_token"]
        if "refresh_token" in refreshed:
            tokens["refresh_token"] = refreshed["refresh_token"]
        _save_tokens(tokens)
        log.info("access_token 자동 갱신 완료")
        return tokens["access_token"]
    except Exception as exc:
        log.warning("토큰 갱신 실패 (%s) -> 재로그인 진행", exc)
        code = _open_kakao_login()
        tokens = _request_token(code)
        _save_tokens(tokens)
        return tokens["access_token"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시장 상태 판별
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_market_context(now_et: datetime) -> tuple:
    """(context_str, market_status_short, is_weekend) 반환."""
    date_str = now_et.strftime("%Y-%m-%d")
    weekday  = now_et.weekday()
    day_kr   = DAY_NAMES_KR[weekday]
    hour     = now_et.hour
    is_weekend = weekday >= 5

    if is_weekend:
        status = "휴장 (주말)"
        emoji  = "😴"
    elif 9 <= hour < 16:
        status = "정규장 개장 중 (ET 9:30~16:00)"
        emoji  = "🟢"
    elif 16 <= hour < 20:
        status = "정규장 마감, 시간외 거래 중"
        emoji  = "🟡"
    elif 4 <= hour < 9:
        status = "프리마켓 (ET 4:00~9:30)"
        emoji  = "🔵"
    else:
        status = "폐장"
        emoji  = "⚫"

    status_short = f"{emoji} 미국 증시: {status}"
    now_kst = now_et.astimezone(KST)
    context_str = (
        f"현재 시각: {date_str} {now_et.strftime('%H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST) ({day_kr})\n"
        f"시장 상태: {status_short}"
    )
    return context_str, status_short, is_weekend


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 뉴스 수집 (우선순위 기반, 최대 50건)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _parse_entry_time(entry) -> Optional[datetime]:
    tp = entry.get("published_parsed") or entry.get("updated_parsed")
    if tp:
        return datetime.fromtimestamp(timegm(tp), tz=pytz.utc)
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        try:
            return parsedate_to_datetime(raw)
        except Exception:
            pass
    return None


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_news() -> list:
    """우선순위 순서대로 RSS 수집, 최대 50건. 중복 제목 제거."""
    all_articles = []
    seen_titles = set()
    cutoff = datetime.now(pytz.utc) - timedelta(hours=6)

    for feed_info in RSS_FEEDS:
        if len(all_articles) >= MAX_ARTICLES:
            break

        name, url, tier = feed_info["name"], feed_info["url"], feed_info["tier"]
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                log.warning("[Tier %d] %s RSS 파싱 실패: %s", tier, name, feed.bozo_exception)
                continue

            count = 0
            for entry in feed.entries:
                if len(all_articles) >= MAX_ARTICLES:
                    break
                if count >= MAX_PER_SOURCE:
                    break

                title = entry.get("title", "").strip()
                if not title:
                    continue

                # 중복 제거
                title_norm = title.lower().strip()
                if title_norm in seen_titles:
                    continue

                # 6시간 필터
                pub_time = _parse_entry_time(entry)
                if pub_time and pub_time < cutoff:
                    continue

                description = _clean_html(entry.get("summary") or entry.get("description") or "")
                if len(description) > 300:
                    description = description[:300] + "..."

                link = entry.get("link", "")
                pub_str = pub_time.strftime("%Y-%m-%d %H:%M UTC") if pub_time else ""

                all_articles.append({
                    "title":       title,
                    "description": description,
                    "source":      name,
                    "tier":        tier,
                    "url":         link,
                    "publishedAt": pub_str,
                })
                seen_titles.add(title_norm)
                count += 1

            if count > 0:
                log.info("[Tier %d] %s: %d건 수집", tier, name, count)

        except Exception as exc:
            log.warning("[Tier %d] %s RSS 수집 실패: %s", tier, name, exc)

    log.info("전체 뉴스 %d건 수집 완료 (cutoff=%s)", len(all_articles), cutoff.strftime("%H:%M UTC"))
    return all_articles


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Claude 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_SYSTEM_PROMPT = (
    "당신은 글로벌 경제 전문 비서입니다. 매일 주요 뉴스를 정리해 독자께 직접 브리핑하는 역할입니다.\n"
    "불특정 다수를 향한 신문 기사체가 아니라, 한 분께 차분하게 말 걸듯 정중한 존댓말로 작성하세요.\n"
    "정중하되 딱딱하지 않게, 친근하되 프로페셔널하게.\n"
    "\n"
    "말투 원칙:\n"
    "- 기본 종결어미는 '~입니다', '~됩니다', '~했습니다'. 분위기에 따라 '~네요', '~군요', '~거든요'도 자연스럽게 섞습니다.\n"
    "- 기사체('~했다', '~이다', '~한다')는 절대 사용하지 않습니다.\n"
    "- 단락을 '참고로', '다만', '특히', '한편', '흥미로운 점은' 같은 연결어로 자연스럽게 이어주세요.\n"
    "- 액션 힌트를 자연스럽게 녹여주세요. '주목하실 만한 움직임입니다', '지켜보실 포인트입니다', '꼼꼼히 확인해보시면 좋겠습니다' 같은 방식으로.\n"
    "\n"
    "절대 규칙:\n"
    "- 수집된 뉴스 원문의 팩트만 전달합니다. 없는 내용은 만들지 않습니다.\n"
    "- 과장, 축소, 추측, 개인 의견은 금지합니다.\n"
    "- 수치(금리, 주가, 지표 등)는 원문 그대로 옮깁니다.\n"
    "- 뉴스 부족 시 솔직히 '현재 시간대 주요 뉴스 없음'으로 처리합니다.\n"
    "- 특정 종목/자산 매수/매도/보유 추천 절대 금지. '지금이 기회', '수혜종목', '모멘텀' 같은 투자 권유 표현 절대 금지.\n"
    "- 팩트와 수치, 인용문만 전달하고 해석은 최소화합니다.\n"
    "- 시간/날짜 언급 시 반드시 미국 동부시간(ET)과 한국시간(KST)을 병기합니다. 예: '현지시간 4월 19일 오후 4시 ET (한국시간 4월 20일 오전 5시 KST)'. KST 기준 날짜가 바뀌면 날짜도 반드시 명시합니다.\n"
    "\n"
    "서식 규칙 (반드시 준수):\n"
    "- #, ##, **, *, ``` 등 마크다운 기호를 절대 사용하지 않습니다.\n"
    "- 점수, 숫자 등급, 평가 수치를 본문에 절대 노출하지 않습니다.\n"
    "- 1️⃣2️⃣ 같은 번호 이모지를 사용하지 않습니다.\n"
    "- 내용 중간중간 적절한 이모티콘을 자연스럽게 배치합니다 (📈📉💰🏦🛢️ 등 경제 관련 이모티콘 위주, 과하지 않게).\n"
    "- 순수한 한국어 문장과 최소한의 구분 기호(쉼표, 마침표, 줄바꿈)만 사용합니다.\n"
    "\n"
    "내부 선정 기준 (본문에 노출 금지):\n"
    "경제영향도, 정책변화, 기업실적, 지정학리스크 네 축으로 판단해\n"
    "상위 10개 핵심 뉴스를 선정합니다. 점수나 기준명은 글에 쓰지 않습니다."
)


def analyze_news(articles: list, market_context: str, is_weekend: bool) -> tuple:
    """Claude로 뉴스 분석. (docs_blocks, kakao_summary) 반환."""
    if not articles:
        return [{"type": "body", "text": "수집된 뉴스가 없습니다."}], "현재 시간대 주요 뉴스 없음"

    # 수집된 매체 목록
    sources = sorted(set(a["source"] for a in articles))

    # ── 뉴스 수집 완료 → Claude API 호출 전 상세 로그 ──
    source_counts = {}
    for a in articles:
        source_counts[a["source"]] = source_counts.get(a["source"], 0) + 1
    log.info("─── Claude API 호출 준비 ───")
    log.info("총 %d건 | 매체 %d개: %s",
             len(articles), len(sources),
             ", ".join(f"{s}({source_counts[s]})" for s in sources))
    for a in articles:
        desc_preview = (a.get("description") or "")[:80].replace("\n", " ")
        log.info("  • [%s] %s | %s", a["source"], a["title"][:60], desc_preview)
    log.info("─── Claude API 호출 시작 ───")

    # 매체별 기사 목록 (토큰 초과 방지: 요약 200자 제한)
    headlines = "\n".join(
        f"[{a['source']}] {a['title']}"
        + (f"\n  -> {a['description'][:200]}" if a.get("description") else "")
        + (f"\n  시간: {a['publishedAt']}" if a.get("publishedAt") else "")
        for a in articles
    )
    source_list = ", ".join(sources)

    weekend_instruction = ""
    if is_weekend:
        weekend_instruction = (
            "\n\n[주말/폐장 특별 지시]\n"
            "현재 미국 증시 휴장 중입니다.\n"
            "- PDF/카카오톡에 휴장 상태를 명시하세요.\n"
            "- 다음 개장 시 영향을 줄 수 있는 뉴스를 우선 선별하세요.\n"
            "- 원문에 없는 전망이나 추측은 절대 추가하지 마세요."
        )

    market_instruction = ""
    if not is_weekend:
        now_et = datetime.now(ET)
        if 9 <= now_et.hour < 16:
            market_instruction = (
                "\n\n[개장 중 특별 지시]\n"
                "현재 미국 증시 정규장 개장 중입니다.\n"
                "- 실시간 시장 영향이 큰 뉴스를 최우선으로 다루세요.\n"
                "- 주가/지수 변동 수치가 있으면 반드시 포함하세요."
            )

    common_context = (
        f"[현재 시각 및 시장 상태]\n{market_context}\n\n"
        f"수집 매체: {source_list}\n"
        f"수집 건수: {len(articles)}건\n\n"
        f"아래는 최근 6시간 이내 뉴스 원문입니다.\n\n"
        f"{headlines}\n\n"
        "규칙:\n"
        "- 원문 팩트만 전달. 과장/축소/추측/의견 금지.\n"
        "- 수치는 원문 그대로.\n"
        "- 4가지 기준(경제영향도, 정책변화, 기업실적, 지정학리스크)으로 점수를 매겨 상위 10개 TOP 뉴스를 선정.\n"
        f"{weekend_instruction}{market_instruction}\n\n"
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=600.0)
    system_block = [{
        "type": "text",
        "text": _SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }]

    # ── 1) 노션 본문용 API 호출 ──
    log.info("Claude API [노션용] 호출 시작 (timeout=600초, 기사 %d건)", len(articles))
    t0 = _time.time()
    docs_resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8000,
        system=system_block,
        messages=[{
            "role": "user",
            "content": (
                common_context
                + "오늘의 브리핑을 JSON 배열로 작성하세요.\n"
                "전문 비서가 독자께 직접 브리핑하듯, 정중하고 자연스러운 존댓말로 작성합니다.\n"
                "딱딱한 나열이 아니라, 한 분께 차분히 설명드리듯 문단이 자연스러운 흐름으로 이어지게 해주세요.\n"
                "'오늘 아침에는 이런 움직임이 있었습니다' 하고 상황을 풀어 전달해드리는 느낌으로.\n\n"
                "시간/날짜 표기 규칙 (반드시 준수):\n"
                "- 본문에서 시간이나 날짜가 나올 때마다 미국 동부시간(ET)과 한국시간(KST)을 병기하세요.\n"
                "- 예: '현지시간 4월 19일 장 마감(한국시간 4월 20일 오전 5시)', '연준은 ET 기준 수요일 오후 2시(한국시간 목요일 새벽 3시)에 발표했습니다'.\n"
                "- KST 기준으로 날짜가 바뀌는 경우를 유의해 날짜도 함께 명시합니다 (ET로는 19일이더라도 KST로는 20일일 수 있음).\n\n"
                "절대 금지:\n"
                "- #, ##, **, * 등 마크다운 기호 사용 금지\n"
                "- 점수, 숫자 등급, 평가 수치 노출 금지\n"
                "- 1️⃣2️⃣ 같은 번호 이모지 금지\n"
                "- 내용 중간중간 적절한 이모티콘을 자연스럽게 배치 (📈📉💰🏦🛢️⚡🌍 등 경제 관련, 과하지 않게)\n\n"
                "중요: 반드시 JSON 배열만 출력하세요. 다른 텍스트 없이 [ 로 시작해서 ] 로 끝나야 합니다.\n"
                "각 항목은 {\"type\": \"...\", \"text\": \"...\"} 형식입니다.\n"
                "type은 다음 5가지만 허용: title, section, article, body, source\n\n"
                "아래 구조를 정확히 따르세요:\n\n"
                "[\n"
                "  {\"type\": \"section\", \"text\": \"시장 시황 및 분위기\"},\n"
                "  {\"type\": \"body\", \"text\": \"그날의 전반적인 시장 분위기 서술...\"},\n"
                "  {\"type\": \"body\", \"text\": \"주요 키워드 3~5개를 뉴스에서 직접 추출해 제시 (단순 나열, 시장 방향 의견 금지)...\"},\n"
                "  {\"type\": \"body\", \"text\": \"동시다발적인 사건/발표들의 상호관계 요약 (팩트 기반, 예측 금지)...\"},\n"
                "  {\"type\": \"section\", \"text\": \"주요 뉴스 심층 분석\"},\n"
                "  {\"type\": \"article\", \"text\": \"1. 소제목 (한국어 번역 제목)\"},\n"
                "  {\"type\": \"body\", \"text\": \"비서가 독자께 브리핑하듯 존댓말로. 사실 전달 → 배경 맥락 → 주목하실 포인트 순서로 3~5줄 서술. 해석/예측/권유 금지, 팩트와 인용문 중심.\"},\n"
                "  {\"type\": \"source\", \"text\": \"출처: 원문 영문 기사 제목 · 매체명\"},\n"
                "  {\"type\": \"article\", \"text\": \"2. 다음 소제목...\"},\n"
                "  ...(1부터 순서대로 번호)\n"
                "  {\"type\": \"section\", \"text\": \"기타 뉴스\"},\n"
                "  {\"type\": \"article\", \"text\": \"11. 소제목 (한국어 번역 제목)\"},\n"
                "  {\"type\": \"body\", \"text\": \"2줄 이내 요약\"},\n"
                "  {\"type\": \"source\", \"text\": \"출처: 원문 영문 기사 제목 · 매체명\"},\n"
                "  ...\n"
                "  {\"type\": \"section\", \"text\": \"섹터별 동향\"},\n"
                "  {\"type\": \"body\", \"text\": \"섹터/산업별 팩트 정리 — 보도된 수치·인용 중심 (전망/추천 금지). 없으면 이 섹션 통째로 생략.\"},\n"
                "  {\"type\": \"section\", \"text\": \"주목할 일정\"},\n"
                "  {\"type\": \"body\", \"text\": \"향후 예정 이벤트 정리 (없으면 이 섹션 통째로 생략)\"}\n"
                "]\n\n"
                "출처의 text는 '출처: 원문 영문 기사 제목 · 매체명' 형식으로 작성하세요. 예: '출처: Oil Declines as US, Iran Weigh More Talks · Bloomberg'\n"
                "URL/링크는 절대 포함하지 마세요."
            ),
        }],
    )
    elapsed_docs = _time.time() - t0
    log.info("Claude API [노션용] 응답 완료 (%.1f초 소요)", elapsed_docs)
    docs_raw = docs_resp.content[0].text

    # JSON 파싱 (코드블록 래핑 제거 대비)
    docs_json_str = docs_raw.strip()
    if docs_json_str.startswith("```"):
        docs_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', docs_json_str)
        docs_json_str = re.sub(r'\n?```$', '', docs_json_str).strip()
    try:
        docs_blocks = json.loads(docs_json_str)
    except json.JSONDecodeError as exc:
        log.error("Claude 노션 JSON 파싱 실패: %s", exc)
        log.error("원본 (첫 500자): %s", docs_raw[:500])
        # fallback: 전체를 body 하나로
        docs_blocks = [{"type": "body", "text": docs_raw}]

    # type 검증
    valid_types = {"title", "section", "article", "body", "source"}
    for block in docs_blocks:
        if block.get("type") not in valid_types:
            block["type"] = "body"

    type_counts = {}
    for b in docs_blocks:
        type_counts[b["type"]] = type_counts.get(b["type"], 0) + 1
    log.info("노션 JSON 파싱 완료: %s (총 %d블록)",
             ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())),
             len(docs_blocks))

    # ── 2) 카카오톡 요약용 API 호출 ──
    # 시스템 프롬프트(_SYSTEM_PROMPT)는 '존댓말/기사체 금지'라 카톡 간결체와 충돌함.
    # 그래서 카톡 호출은 system_block을 빼고 user 프롬프트만으로 포맷 강제.
    # 또한 common_context에 '현재 시각' 정보가 있어서 Claude가 본문에도 시간/시장상태를
    # 중복으로 슔니, 카톡용에는 헤드라인만 넘긴다.
    kakao_minimal_context = (
        f"아래는 최근 6시간 이내 경제 뉴스 원문입니다.\n\n"
        f"{headlines}\n\n"
    )
    log.info("Claude API [카카오용] 호출 시작 (timeout=600초, 기사 %d건)", len(articles))
    t0 = _time.time()
    kakao_resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": (
                kakao_minimal_context
                + "위 뉴스에서 가장 중요한 3~5개를 골라 카카오톡 푸시 알림용으로 아주 짧게 요약하세요.\n\n"
                "출력 형식 (정확히 이 형태, 앞뒤 서론/맺음말 절대 없이):\n"
                "🛢️ 유가 100달러 아래 복귀 (Bloomberg)\n"
                "📈 SK하이닉스 사상 최고치 경신 (Reuters)\n"
                "💰 연준 금리 동결 시사 (WSJ)\n\n"
                "규칙:\n"
                "- 3~5줄, 한 줄당 30자 이내.\n"
                "- 무조건 명사형 종결 (예: 경신, 복귀, 시사, 급락, 상승, 발표, 합의). '~했습니다', '~입니다', '~됩니다', '~했다', '~이다' 같은 문장 어미 절대 금지.\n"
                "- 맨 앞에 이모티콘 1개 (📈 주가, 📉 하락, 💰 금융/금리, 🏦 은행, 🛢️ 에너지, ⚡ 기술/AI, 🌍 지정학, 📊 지표/실적, 🏠 부동산).\n"
                "- 마지막 괄호에 매체명만 (Bloomberg, Reuters, WSJ, CNBC, FT 등). 영문 기사 제목 넣지 말 것.\n"
                "- 날짜/시간(예: '2026-04-20', 'ET', 'KST'), 시장 상태(예: '멟 증시는', '휴장 중', '정규장', '개장', '주말'), 요일, 이모티콘 🕐🟡🟢🔵⚫😴를 절대 출력하지 말 것. 맨 첫 줄부터 바로 뉴스 요약으로 시작.\n"
                "- 링크/URL, 마크다운(#, **, *) 금지.\n"
                "- 주요 뉴스 없으면 '현재 시간대 주요 뉴스 없음'만 한 줄로 출력."
            ),
        }],
    )
    elapsed_kakao = _time.time() - t0
    log.info("Claude API [카카오용] 응답 완료 (%.1f초 소요)", elapsed_kakao)
    kakao_content = kakao_resp.content[0].text

    # ── 안전망: Claude가 날짜/시간/시장상태 헤더 찍어버렸다면 잘라냄 ──
    kakao_content = kakao_content.strip()
    _junk_patterns = [
        re.compile(r"^[🕐🟢🟡🔵⚫😴]"),              # 시간/시장 상태 이모지
        re.compile(r"^현재 시[각간]"),                    # '현재 시각/시간'
        re.compile(r"^미국 증시:"),                        # '미국 증시: ...'
        re.compile(r"^시장 상태"),                          # '시장 상태 ...'
        re.compile(r"^\d{4}-\d{2}-\d{2}"),                   # '2026-04-20 ...'
        re.compile(r"^\[.*(ET|KST).*\]"),                    # '[... ET]'
        re.compile(r".*휴장.*"),                             # '휴장 중', '주말 휴장'
        re.compile(r"^정규장"),                              # '정규장 개장'
        re.compile(r"^프리마윂"),                            # '프리마윂'
    ]
    _lines = kakao_content.split("\n")
    while _lines and (not _lines[0].strip() or any(p.match(_lines[0].strip()) for p in _junk_patterns)):
        _lines.pop(0)
    kakao_content = "\n".join(_lines).strip()

    log.info("Claude 분석 완료 (노션: %d블록, 카카오: %d자)", len(docs_blocks), len(kakao_content))
    return docs_blocks, kakao_content


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노션 브리핑 페이지 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _notion_rich_text(text: str, bold: bool = False, color: str = "default") -> list:
    """노션 rich_text 배열 생성 헬퍼."""
    rt: dict = {
        "type": "text",
        "text": {"content": text},
        "annotations": {
            "bold": bold,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": color,
        },
    }
    return [rt]


def _notion_block(block_type: str, text: str,
                  bold: bool = False, color: str = "default") -> dict:
    """노션 블록 dict 생성 헬퍼."""
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": _notion_rich_text(text, bold=bold, color=color),
        },
    }


def generate_notion_page(docs_blocks: list, articles: list,
                         time_str: str, market_status: str) -> str:
    """노션 하위 페이지로 브리핑 생성. 공개 링크 반환.

    공개 설정 전제조건:
      상위 페이지(NOTION_PAGE_ID)에서 한 번만 수동으로
      '웹에 게시(Publish)' + '하위 페이지 포함' 을 켜두면
      이후 생성되는 모든 하위 페이지가 자동으로 공개됩니다.
    """

    notion = NotionClient(auth=NOTION_API_KEY)

    # ── 노션 블록 리스트 조립 ──
    children: list[dict] = []

    # 표지
    children.append(_notion_block("heading_1", "Global Economy Daily Briefing"))
    children.append(_notion_block("paragraph", time_str))
    children.append(_notion_block("paragraph", market_status))
    children.append({"object": "block", "type": "divider", "divider": {}})

    # Claude 블록 → 노션 블록 변환
    prev_type = None
    for block in docs_blocks:
        btype = block.get("type", "body")
        text  = block.get("text", "")

        # 기사 사이 구분선
        if btype == "article" and prev_type not in (None, "section"):
            children.append({"object": "block", "type": "divider", "divider": {}})

        if btype == "title":
            children.append(_notion_block("heading_1", text))
        elif btype == "section":
            children.append(_notion_block("heading_2", text, bold=True))
        elif btype == "article":
            children.append(_notion_block("heading_2", text, bold=True))
        elif btype == "source":
            children.append(_notion_block("paragraph", text, color="gray"))
        else:
            # body (빈 줄 포함)
            children.append(_notion_block("paragraph", text))

        prev_type = btype

    # ── 노션 API: 100블록 제한 대응 (청크 분할) ──
    first_chunk = children[:100]
    remaining   = children[100:]

    page = notion.pages.create(
        parent={"page_id": NOTION_PAGE_ID},
        properties={
            "title": [{"text": {"content": f"경제 뉴스 브리핑 — {time_str}"}}],
        },
        children=first_chunk,
    )
    page_id = page["id"]
    log.info("노션 페이지 생성: %s (%d블록)", page_id, len(first_chunk))

    # 100블록 초과분 추가
    while remaining:
        chunk = remaining[:100]
        remaining = remaining[100:]
        notion.blocks.children.append(block_id=page_id, children=chunk)
        log.info("노션 블록 추가: %d블록", len(chunk))

    # ── 공개 링크 생성 ──
    # API 응답의 url 필드에서 공개 링크 추출
    # 상위 페이지가 '웹에 게시' 상태이면 이 URL로 누구나 접근 가능
    page_url = page.get("url", "")
    if page_url:
        link = page_url
    else:
        # fallback: ID로 URL 직접 구성
        clean_id = page_id.replace("-", "")
        link = f"https://notion.so/{clean_id}"

    log.info("노션 페이지 링크: %s", link)
    return link


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 카카오톡 전송
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_kakao_message(text: str, retry: bool = False) -> None:
    access_token = get_access_token()

    if len(text) > 2000:
        text = text[:1997] + "..."

    template_object = json.dumps({
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": FALLBACK_URL,
            "mobile_web_url": FALLBACK_URL,
        },
        "button_title": "6시간 USA 뉴스",
    }, ensure_ascii=False)

    resp = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": template_object},
        timeout=30,
    )

    if resp.status_code == 401 and not retry:
        log.warning("access_token 만료 -> 재발급 후 재시도")
        tokens = _load_tokens() or {}
        tokens.pop("access_token", None)
        _save_tokens(tokens)
        send_kakao_message(text, retry=True)
        return

    resp.raise_for_status()
    result = resp.json()
    if result.get("result_code") == 0:
        log.info("카카오톡 전송 완료")
    else:
        raise RuntimeError(f"카카오톡 API 오류: {result}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 파이프라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_pipeline() -> None:
    now_et   = datetime.now(ET)
    now_kst  = now_et.astimezone(KST)
    time_str = f"{now_et.strftime('%Y-%m-%d %H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST)"
    log.info("=== 파이프라인 시작: %s ===", time_str)

    market_context, market_status, is_weekend = _get_market_context(now_et)
    log.info("시장 상태: %s", market_status)

    try:
        # 1. 뉴스 수집
        log.info("[1/4] 뉴스 수집 시작...")
        t_step = _time.time()
        articles = fetch_news()
        log.info("[1/4] 뉴스 수집 완료: %d건 (%.1f초)", len(articles), _time.time() - t_step)

        if not articles:
            log.warning("수집된 뉴스 없음")
            send_kakao_message(
                f"🕐 {time_str}\n{market_status}\n\n현재 시간대 주요 뉴스 없음"
            )
            return

        # 2. Claude 분석
        log.info("[2/4] Claude 분석 시작...")
        t_step = _time.time()
        docs_blocks, kakao_summary = analyze_news(
            articles, market_context, is_weekend
        )
        log.info("[2/4] Claude 분석 완료 (%.1f초)", _time.time() - t_step)

        # 3. 노션 페이지 생성
        doc_link = None
        try:
            log.info("[3/4] 노션 페이지 생성 시작...")
            t_step = _time.time()
            doc_link = generate_notion_page(docs_blocks, articles, time_str, market_status)
            log.info("[3/4] 노션 페이지 생성 완료 (%.1f초)", _time.time() - t_step)
        except Exception:
            log.exception("[3/4] 노션 페이지 생성 실패 (카카오톡 전송은 계속 진행)")

        # 4. 카카오톡 메시지 전송
        log.info("[4/4] 카카오톡 메시지 전송 시작...")
        t_step = _time.time()
        msg = (
            f"🕐 {time_str}\n"
            f"{market_status}\n\n"
            f"{kakao_summary}"
        )
        if doc_link:
            msg += f"\n\n전체 브리핑 보기:\n{doc_link}"

        send_kakao_message(msg)
        log.info("[4/4] 카카오톡 전송 완료 (%.1f초)", _time.time() - t_step)

        # 5-6. 카드뉴스 생성 + Gmail 발송 (AUTO_CARDNEWS=True 그리고 18:00 ET에만)
        # 인스타그램 자동 게시는 Meta API 이슈로 비활성화 (아래 주석 참고)
        is_18_et = (now_et.hour == 18)
        if AUTO_CARDNEWS and is_18_et:
            try:
                log.info("[5/6] 카드뉴스 생성 시작...")
                t_step = _time.time()
                from card_news_generator import generate_card_news
                card_date_str = f"{now_et.strftime('%Y.%m.%d %a').upper()} · {now_et.strftime('%H:%M')} ET"
                png_files, cards_data = generate_card_news(docs_blocks, card_date_str)
                log.info("[5/6] 카드뉴스 생성 완료: %d장 (%.1f초)", len(png_files), _time.time() - t_step)

                # 6. Gmail 발송 (인스타 API 풀리면 아래 주석 해제)
                if png_files:
                    log.info("[6/6] Gmail 카드뉴스 발송 시작...")
                    t_step = _time.time()
                    from gmail_sender import send_card_news_email
                    sent = send_card_news_email(png_files, cards_data, card_date_str)
                    log.info("[6/6] Gmail 발송 %s (%.1f초)",
                             "완료" if sent else "실패", _time.time() - t_step)

                    # ── 미래: 인스타 API 풀리면 아래 주석 해제 ──
                    # from instagram_poster import post_carousel_to_instagram
                    # post_id = post_carousel_to_instagram(png_files, cards_data)
                else:
                    log.warning("[5/6] 카드뉴스 생성 실패 — Gmail 발송 건너뜀")
            except Exception:
                log.exception("[5-6] 카드뉴스/Gmail 처리 실패 (기존 파이프라인에는 영향 없음)")
        else:
            log.info("[5-6] 카드뉴스 생성 스킵 (AUTO_CARDNEWS=%s, 18시=%s)",
                     AUTO_CARDNEWS, is_18_et)

        log.info("=== 파이프라인 완료 ===")

    except Exception:
        log.exception("파이프라인 실행 실패")
        try:
            send_kakao_message(
                f"⚠️ [뉴스봇 오류]\n{time_str}\n오류가 발생했습니다. 로그를 확인해 주세요."
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 브리핑 전용 수동 실행 (briefing-once)
#   run_pipeline 과 동일 흐름이지만 카드뉴스/Gmail 블록 제외.
#   fetch_news → analyze_news → generate_notion_page → send_kakao_message
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_briefing_only() -> None:
    now_et   = datetime.now(ET)
    now_kst  = now_et.astimezone(KST)
    time_str = f"{now_et.strftime('%Y-%m-%d %H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST)"
    log.info("=== [브리핑 전용 모드] 시작: %s ===", time_str)

    market_context, market_status, is_weekend = _get_market_context(now_et)
    log.info("시장 상태: %s", market_status)

    try:
        # 1. 뉴스 수집
        log.info("[1/4] 뉴스 수집 시작...")
        t_step = _time.time()
        articles = fetch_news()
        log.info("[1/4] 뉴스 수집 완료: %d건 (%.1f초)", len(articles), _time.time() - t_step)

        if not articles:
            log.warning("수집된 뉴스 없음")
            send_kakao_message(
                f"🕐 {time_str}\n{market_status}\n\n현재 시간대 주요 뉴스 없음"
            )
            return

        # 2. Claude 분석
        log.info("[2/4] Claude 분석 시작...")
        t_step = _time.time()
        docs_blocks, kakao_summary = analyze_news(
            articles, market_context, is_weekend
        )
        log.info("[2/4] Claude 분석 완료 (%.1f초)", _time.time() - t_step)

        # 3. 노션 페이지 생성
        doc_link = None
        try:
            log.info("[3/4] 노션 페이지 생성 시작...")
            t_step = _time.time()
            doc_link = generate_notion_page(docs_blocks, articles, time_str, market_status)
            log.info("[3/4] 노션 페이지 생성 완료 (%.1f초)", _time.time() - t_step)
        except Exception:
            log.exception("[3/4] 노션 페이지 생성 실패 (카카오톡 전송은 계속 진행)")

        # 4. 카카오톡 메시지 전송
        log.info("[4/4] 카카오톡 메시지 전송 시작...")
        t_step = _time.time()
        msg = (
            f"🕐 {time_str}\n"
            f"{market_status}\n\n"
            f"{kakao_summary}"
        )
        if doc_link:
            msg += f"\n\n전체 브리핑 보기:\n{doc_link}"

        send_kakao_message(msg)
        log.info("[4/4] 카카오톡 전송 완료 (%.1f초)", _time.time() - t_step)

        log.info("=== [브리핑 전용 모드] 완료 ===")

    except Exception:
        log.exception("브리핑 실행 실패")
        try:
            send_kakao_message(
                f"⚠️ [뉴스봇 오류]\n{time_str}\n오류가 발생했습니다. 로그를 확인해 주세요."
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전체 파이프라인 1회 실행 (daily-once)
#   run_pipeline 의 6단계 흐름(수집→분석→노션→카톡→카드뉴스→메일)을
#   AUTO_CARDNEWS / 시간 조건 없이 무조건 전부 실행.
#   run_pipeline 본체는 건드리지 않고 별도 함수로 분리.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_daily_once() -> None:
    now_et   = datetime.now(ET)
    now_kst  = now_et.astimezone(KST)
    time_str = f"{now_et.strftime('%Y-%m-%d %H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST)"
    log.info("=== [전체 1회 모드] 시작: %s ===", time_str)

    market_context, market_status, is_weekend = _get_market_context(now_et)
    log.info("시장 상태: %s", market_status)

    results = {
        "뉴스수집": "미실행",
        "Claude분석": "미실행",
        "노션": "미실행",
        "카카오": "미실행",
        "카드뉴스": "미실행",
        "Gmail": "미실행",
    }

    # 1. 뉴스 수집
    log.info("[1/6] 뉴스 수집 시작...")
    t_step = _time.time()
    try:
        articles = fetch_news()
        log.info("[1/6] 뉴스 수집 완료: %d건 (%.1f초)", len(articles), _time.time() - t_step)
        results["뉴스수집"] = f"성공 ({len(articles)}건)"
    except Exception:
        log.exception("[1/6] 뉴스 수집 실패 — 종료")
        results["뉴스수집"] = "실패"
        _print_daily_once_summary(results)
        return

    if not articles:
        log.warning("[1/6] 수집된 뉴스 없음 — 종료")
        results["뉴스수집"] = "성공 (0건)"
        _print_daily_once_summary(results)
        return

    # 2. Claude 분석
    log.info("[2/6] Claude 분석 시작...")
    t_step = _time.time()
    docs_blocks = None
    kakao_summary = ""
    try:
        docs_blocks, kakao_summary = analyze_news(articles, market_context, is_weekend)
        log.info("[2/6] Claude 분석 완료 (%.1f초)", _time.time() - t_step)
        results["Claude분석"] = f"성공 ({len(docs_blocks)}블록)"
    except Exception:
        log.exception("[2/6] Claude 분석 실패 — 이후 단계 불가, 종료")
        results["Claude분석"] = "실패"
        _print_daily_once_summary(results)
        return

    # 3. 노션 페이지 생성
    doc_link = None
    log.info("[3/6] 노션 페이지 생성 시작...")
    t_step = _time.time()
    try:
        doc_link = generate_notion_page(docs_blocks, articles, time_str, market_status)
        log.info("[3/6] 노션 페이지 생성 완료 (%.1f초)", _time.time() - t_step)
        results["노션"] = "성공"
    except Exception:
        log.exception("[3/6] 노션 페이지 생성 실패 (카카오 전송은 계속 진행)")
        results["노션"] = "실패"

    # 4. 카카오톡 메시지 전송
    log.info("[4/6] 카카오톡 메시지 전송 시작...")
    t_step = _time.time()
    try:
        msg = (
            f"🕐 {time_str}\n"
            f"{market_status}\n\n"
            f"{kakao_summary}"
        )
        if doc_link:
            msg += f"\n\n전체 브리핑 보기:\n{doc_link}"

        send_kakao_message(msg)
        log.info("[4/6] 카카오톡 전송 완료 (%.1f초)", _time.time() - t_step)
        results["카카오"] = "성공"
    except Exception:
        log.exception("[4/6] 카카오 전송 실패 (카드뉴스/메일은 계속 진행)")
        results["카카오"] = "실패"

    # 5. 카드뉴스 생성
    png_files: list = []
    cards_data: list = []
    card_date_str = f"{now_et.strftime('%Y.%m.%d %a').upper()} · {now_et.strftime('%H:%M')} ET"
    log.info("[5/6] 카드뉴스 생성 시작...")
    t_step = _time.time()
    try:
        from card_news_generator import generate_card_news
        png_files, cards_data = generate_card_news(docs_blocks, card_date_str)
        log.info("[5/6] 카드뉴스 생성 완료: %d장 (%.1f초)",
                 len(png_files), _time.time() - t_step)
        results["카드뉴스"] = f"성공 ({len(png_files)}장)" if png_files else "실패 (0장)"
    except Exception:
        log.exception("[5/6] 카드뉴스 생성 실패 (메일 발송은 스킵)")
        results["카드뉴스"] = "실패"

    # 6. Gmail 발송 — 카드뉴스 성공 시에만
    if png_files:
        log.info("[6/6] Gmail 발송 시작...")
        t_step = _time.time()
        try:
            from gmail_sender import send_card_news_email
            sent = send_card_news_email(png_files, cards_data, card_date_str)
            log.info("[6/6] Gmail 발송 %s (%.1f초)",
                     "완료" if sent else "실패", _time.time() - t_step)
            results["Gmail"] = "성공" if sent else "실패"
        except Exception:
            log.exception("[6/6] Gmail 발송 중 예외")
            results["Gmail"] = "실패"
    else:
        log.warning("[6/6] 카드뉴스 PNG 없음 — Gmail 발송 스킵")
        results["Gmail"] = "스킵 (PNG 없음)"

    _print_daily_once_summary(results)
    log.info("=== [전체 1회 모드] 완료 ===")


def _print_daily_once_summary(results: dict) -> None:
    log.info("─── daily-once 실행 결과 ───")
    for step, status in results.items():
        log.info("  %-10s : %s", step, status)
    log.info("────────────────────────────")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 카드뉴스 전용 수동 실행 (--cardnews)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_cardnews_only() -> None:
    """
    뉴스 수집 → Claude 분석 → 카드뉴스 PNG 생성 → Gmail 발송.
    노션 페이지 생성과 카카오톡 전송은 건너뜀.
    """
    now_et   = datetime.now(ET)
    now_kst  = now_et.astimezone(KST)
    time_str = f"{now_et.strftime('%Y-%m-%d %H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST)"
    log.info("=== [카드뉴스 전용 모드] 시작: %s ===", time_str)

    market_context, market_status, is_weekend = _get_market_context(now_et)
    log.info("시장 상태: %s", market_status)

    # 1. 뉴스 수집
    log.info("[1/4] 뉴스 수집 시작...")
    t_step = _time.time()
    articles = fetch_news()
    log.info("[1/4] 뉴스 수집 완료: %d건 (%.1f초)", len(articles), _time.time() - t_step)
    if not articles:
        log.warning("수집된 뉴스 없음 — 종료")
        return

    # 2. Claude 분석
    log.info("[2/4] Claude 분석 시작...")
    t_step = _time.time()
    docs_blocks, _ = analyze_news(articles, market_context, is_weekend)
    log.info("[2/4] Claude 분석 완료 (%.1f초)", _time.time() - t_step)

    # 3. 카드뉴스 PNG 생성
    log.info("[3/4] 카드뉴스 생성 시작...")
    t_step = _time.time()
    from card_news_generator import generate_card_news
    card_date_str = f"{now_et.strftime('%Y.%m.%d %a').upper()} · {now_et.strftime('%H:%M')} ET"
    png_files, cards_data = generate_card_news(docs_blocks, card_date_str)
    log.info("[3/4] 카드뉴스 생성 완료: %d장 (%.1f초)", len(png_files), _time.time() - t_step)

    if not png_files:
        log.error("카드뉴스 생성 실패 — 종료")
        return

    # 4. Gmail 발송
    log.info("[4/4] Gmail 발송 시작...")
    t_step = _time.time()
    from gmail_sender import send_card_news_email
    sent = send_card_news_email(png_files, cards_data, card_date_str)
    log.info("[4/4] Gmail 발송 %s (%.1f초)",
             "완료" if sent else "실패", _time.time() - t_step)
    log.info("=== [카드뉴스 전용 모드] 완료 ===")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 클라우드 모드 (GitHub Actions 진입점)
#   매 실행 1회: 뉴스 수집 → Claude 분석 → 사이트 5개 이슈 추출
#                → 시장 시황 → Supabase upsert → 노션 → 카카오톡(사이트 링크)
#   카드뉴스/Gmail은 사용자가 AUTO_CARDNEWS 또는 GMAIL env 세팅했을 때만.
#   세션(morning/evening)은 KST 현재 시각으로 자동 판별.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_cloud() -> None:
    now_et   = datetime.now(ET)
    now_kst  = now_et.astimezone(KST)
    time_str = f"{now_et.strftime('%Y-%m-%d %H:%M')} ET (한국시간 {now_kst.strftime('%H:%M')} KST)"
    log.info("=== [클라우드 모드] 시작: %s ===", time_str)

    market_context, market_status_str, is_weekend = _get_market_context(now_et)
    log.info("시장 상태: %s", market_status_str)

    results = {
        "뉴스수집": "미실행", "Claude분석": "미실행", "사이트추출": "미실행",
        "시장시황": "미실행", "Supabase": "미실행",
        "노션": "미실행", "카카오": "미실행", "카드뉴스": "미실행", "Gmail": "미실행",
    }

    # ── 사이트 세션 결정 ──
    # ★ 정책: morning/evening 모두 사이트·노션 갱신. 카드뉴스/Gmail만 morning 전용(API 절감).
    from supabase_writer import get_site_session, upsert_briefing
    session_date, session_time = get_site_session(now_kst)
    is_morning_session = (session_time == "morning")
    log.info("사이트 세션: %s/%s (KST 기준, morning=%s)", session_date, session_time, is_morning_session)

    # 1. 뉴스 수집
    log.info("[1/9] 뉴스 수집 시작...")
    t = _time.time()
    try:
        articles = fetch_news()
        log.info("[1/9] 뉴스 수집 완료: %d건 (%.1f초)", len(articles), _time.time() - t)
        results["뉴스수집"] = f"성공 ({len(articles)}건)"
    except Exception:
        log.exception("[1/9] 뉴스 수집 실패")
        results["뉴스수집"] = "실패"
        _print_daily_once_summary(results)
        return

    if not articles:
        log.warning("[1/9] 수집된 뉴스 없음 — 종료")
        results["뉴스수집"] = "성공 (0건)"
        _print_daily_once_summary(results)
        return

    # 2. Claude 분석 (노션용 docs + 카카오 요약)
    log.info("[2/9] Claude 분석 시작...")
    t = _time.time()
    try:
        docs_blocks, kakao_summary = analyze_news(articles, market_context, is_weekend)
        log.info("[2/9] Claude 분석 완료 (%.1f초)", _time.time() - t)
        results["Claude분석"] = f"성공 ({len(docs_blocks)}블록)"
    except Exception:
        log.exception("[2/9] Claude 분석 실패 — 종료")
        results["Claude분석"] = "실패"
        _print_daily_once_summary(results)
        return

    # 3. 사이트용 5개 이슈 추출 (morning/evening 둘 다)
    log.info("[3/9] 사이트용 이슈 추출 시작...")
    t = _time.time()
    try:
        from site_extractor import extract_for_site
        site_payload = extract_for_site(docs_blocks)
        log.info(
            "[3/9] 사이트 추출 완료: intro %d자, items %d개 (%.1f초)",
            len(site_payload.get("briefing_intro", "")),
            len(site_payload.get("items", [])),
            _time.time() - t,
        )
        results["사이트추출"] = f"성공 ({len(site_payload.get('items', []))}개)"
    except Exception:
        log.exception("[3/9] 사이트 추출 실패")
        results["사이트추출"] = "실패"
        site_payload = {"briefing_intro": "", "items": []}

    # 4. 시장 시황 (yfinance)
    log.info("[4/9] 시장 시황 수집 시작...")
    t = _time.time()
    try:
        from market_fetcher import fetch_market_status
        market_status = fetch_market_status()
        log.info("[4/9] 시장 시황 완료 (%.1f초)", _time.time() - t)
        results["시장시황"] = "성공" if market_status else "실패 (None)"
    except Exception:
        log.exception("[4/9] 시장 시황 수집 실패 (계속 진행)")
        market_status = None
        results["시장시황"] = "실패"

    # 5. 노션 페이지 (NOTION env 있을 때만) — 먼저 생성해서 URL 받아옴
    doc_link = None
    if NOTION_API_KEY and NOTION_PAGE_ID:
        log.info("[5/9] 노션 페이지 생성 시작...")
        t = _time.time()
        try:
            doc_link = generate_notion_page(docs_blocks, articles, time_str, market_status_str)
            log.info("[5/9] 노션 페이지 생성 완료 (%.1f초)", _time.time() - t)
            results["노션"] = "성공"
        except Exception:
            log.exception("[5/9] 노션 페이지 생성 실패")
            results["노션"] = "실패"
    else:
        log.info("[5/9] NOTION env 없음 — 스킵")
        results["노션"] = "스킵"

    # 6. Supabase upsert (morning/evening 둘 다 — 사이트는 양쪽 슬롯 갱신)
    log.info("[6/9] Supabase 저장 시작...")
    t = _time.time()
    try:
        row_id = upsert_briefing(
            session_date=session_date,
            session_time=session_time,
            market_status=market_status,
            briefing_intro=site_payload.get("briefing_intro", ""),
            items=site_payload.get("items", []),
            notion_url=doc_link,
        )
        log.info("[6/9] Supabase 저장 완료 (%.1f초)", _time.time() - t)
        results["Supabase"] = f"성공 ({row_id})" if row_id else "실패/스킵"
    except Exception:
        log.exception("[6/9] Supabase 저장 실패 (계속 진행)")
        results["Supabase"] = "실패"

    # 7. 카카오톡 — ★ 서비스 종료. 노션 + 사이트만 운영.
    log.info("[7/9] 카톡 서비스 종료 — 스킵 (노션/사이트만 운영)")
    results["카카오"] = "스킵 (서비스 종료)"

    # 8-9. 카드뉴스 + Gmail
    # ★ morning 세션에만 실행 (evening은 Anthropic + Unsplash API 비용 절약 위해 스킵)
    GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "").strip()
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not is_morning_session:
        log.info("[8-9] evening 세션 — 카드뉴스/Gmail 스킵 (morning에만 생성, API 비용 절약)")
        results["카드뉴스"] = "스킵 (evening)"
        results["Gmail"] = "스킵 (evening)"
    elif GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        log.info("[8/9] 카드뉴스 생성 시작...")
        t = _time.time()
        png_files, cards_data = [], []
        try:
            from card_news_generator import generate_card_news
            card_date_str = f"{now_et.strftime('%Y.%m.%d %a').upper()} · {now_et.strftime('%H:%M')} ET"
            png_files, cards_data = generate_card_news(docs_blocks, card_date_str)
            log.info("[8/9] 카드뉴스 생성 완료: %d장 (%.1f초)", len(png_files), _time.time() - t)
            results["카드뉴스"] = f"성공 ({len(png_files)}장)" if png_files else "실패 (0장)"
        except Exception:
            log.exception("[8/9] 카드뉴스 생성 실패")
            results["카드뉴스"] = "실패"

        if png_files:
            log.info("[9/9] Gmail 발송 시작...")
            t = _time.time()
            try:
                from gmail_sender import send_card_news_email
                sent = send_card_news_email(png_files, cards_data, card_date_str)
                log.info("[9/9] Gmail 발송 %s (%.1f초)", "완료" if sent else "실패", _time.time() - t)
                results["Gmail"] = "성공" if sent else "실패"
            except Exception:
                log.exception("[9/9] Gmail 발송 예외")
                results["Gmail"] = "실패"
        else:
            results["Gmail"] = "스킵 (PNG 없음)"
    else:
        log.info("[8-9] 카드뉴스/Gmail 스킵 — GMAIL_ADDRESS/GMAIL_APP_PASSWORD 미설정")
        results["카드뉴스"] = "스킵"
        results["Gmail"] = "스킵"

    _print_daily_once_summary(results)
    log.info("=== [클라우드 모드] 완료 ===")



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 진입점
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _check_env(require_notion: bool = True, require_kakao: bool = True) -> None:
    required = [("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)]
    if require_kakao:
        required.append(("KAKAO_REST_API_KEY", KAKAO_REST_API_KEY))
    if require_notion:
        required.append(("NOTION_API_KEY", NOTION_API_KEY))
        required.append(("NOTION_PAGE_ID", NOTION_PAGE_ID))
    missing = [name for name, val in required if not val]
    if missing:
        log.error("환경변수가 설정되지 않았습니다: %s", ", ".join(missing))
        sys.exit(1)


def main() -> None:
    # cloud 모드면 NOTION/KAKAO 옵셔널 (require_=False).
    # 다른 모드(--now, --auth 등)는 기존대로 모두 필요.
    cloud_mode = "cloud" in sys.argv
    _check_env(require_notion=not cloud_mode, require_kakao=not cloud_mode)

    if "--auth" in sys.argv:
        log.info("카카오 인증 모드")
        code = _open_kakao_login()
        tokens = _request_token(code)
        _save_tokens(tokens)
        log.info("인증 완료. 토큰이 %s에 저장되었습니다.", TOKEN_FILE)
        return

    if "--now" in sys.argv:
        log.info("즉시 실행 모드 (뉴스+노션+카톡)")
        get_access_token()
        run_pipeline()
        return

    if "briefing-once" in sys.argv:
        log.info("브리핑 1회 실행 모드 (뉴스+노션+카톡 내게쓰기, 카드뉴스/메일 제외)")
        get_access_token()
        run_briefing_only()
        return

    if "daily-once" in sys.argv:
        log.info("전체 1회 실행 모드 (뉴스+노션+카톡+카드뉴스+Gmail)")
        get_access_token()
        run_daily_once()
        return

    if "--cardnews" in sys.argv:
        log.info("카드뉴스 전용 모드 (뉴스+분석+카드뉴스+Gmail)")
        run_cardnews_only()
        return

    if "cloud" in sys.argv:
        log.info("클라우드 모드 (GitHub Actions 진입점)")
        run_cloud()
        return

    # 스케줄러 모드 — AUTO_SCHEDULE=False면 안내만 출력하고 종료
    if not AUTO_SCHEDULE:
        log.info("=" * 60)
        log.info("AUTO_SCHEDULE=False — 자동 스케줄러가 꺼져있습니다.")
        log.info("수동 실행 옵션:")
        log.info("  python news_bot.py cloud            # 클라우드 모드 (Actions cron이 호출)")
        log.info("  python news_bot.py --now            # 뉴스+노션+카톡 즉시 실행")
        log.info("  python news_bot.py briefing-once    # 브리핑+노션+카톡 내게쓰기 (카드뉴스/메일 제외)")
        log.info("  python news_bot.py daily-once       # 전체 1회 (뉴스+노션+카톡+카드뉴스+Gmail)")
        log.info("  python news_bot.py --cardnews       # 카드뉴스 생성 + Gmail 발송")
        log.info("  python news_bot.py --auth           # 카카오 재인증")
        log.info("")
        log.info("자동화를 켜려면 news_bot.py 상단의 AUTO_SCHEDULE=True로 변경하세요.")
        log.info("(카드뉴스 자동화는 AUTO_CARDNEWS=True도 함께 설정)")
        log.info("=" * 60)
        return

    # 스케줄러 모드 (AUTO_SCHEDULE=True)
    log.info("카카오 토큰 확인 중...")
    get_access_token()
    log.info("카카오 인증 준비 완료")

    scheduler = BlockingScheduler(timezone=ET)
    scheduler.add_job(
        run_pipeline,
        CronTrigger(hour="0,6,12,18", minute=0, timezone=ET),
        id="news_pipeline",
        name="경제 뉴스 브리핑",
        misfire_grace_time=300,
        coalesce=True,
    )

    log.info("스케줄러 시작 — 매일 ET 00:00 / 06:00 / 12:00 / 18:00 실행")
    log.info("종료하려면 Ctrl+C를 누르세요.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("스케줄러 종료")


if __name__ == "__main__":
    main()
