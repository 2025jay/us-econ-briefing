"""
카드뉴스 자동 생성 모듈 (Y2K Sticker Pop 디자인)

news_bot의 docs_blocks를 받아서:
1. Claude API로 카드뉴스용 5대 뉴스 추출 (새 스키마: n/tag/title/highlight/tldr/body/stat/imageCaption)
2. Unsplash API로 photo_0.jpg ~ photo_4.jpg 다운로드
3. cardnews/index.html에 데이터 주입 → card_news_output/preview.html 생성
4. Playwright로 각 카드를 1080x1080 PNG로 캡처 (card_01.png ~ card_07.png)

환경변수:
  ANTHROPIC_API_KEY    - (기존 news_bot과 공유)
  UNSPLASH_ACCESS_KEY  - Unsplash API Access Key
"""

import os
import re
import json
import logging
import time as _time
from pathlib import Path
from datetime import datetime

import requests
import anthropic

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
CARD_OUTPUT_DIR = BASE_DIR / "card_news_output"
CARD_OUTPUT_DIR.mkdir(exist_ok=True)

DESIGN_HTML_PATH = BASE_DIR / "cardnews" / "index.html"
PREVIEW_HTML_PATH = CARD_OUTPUT_DIR / "preview.html"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1단계: Claude API — 카드뉴스용 5대 뉴스 추출 (새 스키마)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_card_news_data(docs_blocks: list) -> list:
    """docs_blocks에서 카드뉴스용 5대 뉴스를 새 디자인 스키마로 추출한다."""
    full_text = "\n".join(b.get("text", "") for b in docs_blocks)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=120.0)

    log.info("Claude API [카드뉴스용] 호출 시작")
    t0 = _time.time()

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3500,
        messages=[{
            "role": "user",
            "content": (
                "아래는 오늘의 경제 뉴스 브리핑 전문입니다.\n\n"
                f"{full_text}\n\n"
                "위 브리핑에서 인스타그램 카드뉴스용 TOP 5 뉴스를 뽑아주세요.\n"
                "중요도가 높고 대중의 관심을 끌 수 있는 뉴스를 우선 선정하세요.\n\n"
                "반드시 아래 JSON 배열 형식으로만 출력하세요. 다른 텍스트 없이.\n\n"
                "[\n"
                "  {\n"
                '    "n": "01",\n'
                '    "tag": "ENERGY",\n'
                '    "title": "한국어 헤드라인 (40자 이내, 한 줄)",\n'
                '    "highlight": "title 안에 포함된 강조 substring (2~8자)",\n'
                '    "source": "원문 영문 기사 제목 (풀 문장)",\n'
                '    "outlet": "매체명 (예: Bloomberg)",\n'
                '    "tldr": "한 줄 요약 15자 이내 (공백 포함, 한국어 기준)",\n'
                '    "body": "비서가 독자께 직접 말씀드리듯 정중한 존댓말 본문 100~260자. 핵심 사실 → 수치/데이터 → 배경 맥락 → 주목하실 영향 순서로.",\n'
                '    "stat": { "label": "지표 라벨 8자 이내", "value": "$3+ / 04.21 등 핵심 수치", "unit": "단위 또는 부가설명", "note": "짧은 비고 (없으면 빈 문자열)" },\n'
                '    "imageCaption": "영문 폴라로이드 캡션 28자 이내 (예: Strait of Hormuz)",\n'
                '    "unsplash_keywords": "시각적 구체 명사 2~4개, 쉼표 구분, 영어 소문자. imageCaption과 같은 시각 도메인. 규칙은 하단 참고."\n'
                "  }\n"
                "]\n\n"
                "카테고리 다양성 가이드 (가급적 준수):\n"
                "- 01 tag: ENERGY 또는 산업 관련 (예: ENERGY, OIL, INDUSTRY, COMMODITIES)\n"
                "- 02 tag: GEOPOLITICS (지정학·외교·분쟁)\n"
                "- 03 tag: FED 또는 일정/정책 (예: FED, POLICY, SCHEDULE, CPI)\n"
                "- 04 tag: BIG TECH (빅테크·AI·반도체)\n"
                "- 05 tag: MARKETS (증시·지수·밸류에이션)\n"
                "- 해당 카테고리 뉴스가 없으면 근접 주제로 대체 가능. tag는 항상 대문자 영문 14자 이내.\n\n"
                "규칙:\n"
                "- title은 한 줄 40자 이내 (줄바꿈 금지).\n"
                "- tldr은 공백 포함 15자 이내 (한국어 기준). 한 줄 디자인이 깨지지 않도록 반드시 준수.\n"
                "- highlight는 title 안에 정확히 포함된 substring이어야 함 (JS에서 replace로 강조 처리됨).\n"
                "- body는 원문의 사실과 수치만 전달. '주목하세요', '사야 할 때', '지금이 기회', '수혜를 입을 수 있습니다', '날아오를 가능성' 같은 투자 조언/예측/권유 표현 절대 금지.\n"
                "- body는 반드시 정중한 존댓말(~입니다, ~나타났습니다, ~보입니다). 기자체(~했다, ~이다) 절대 금지.\n"
                "- 특정 종목/자산에 대한 매수/매도/보유 추천 금지. 시장 방향/모멘텀 의견 금지.\n"
                "- source는 원문 영문 기사 제목 (풀 문장). outlet은 매체명만 따로.\n"
                "- stat은 숫자·날짜·퍼센트 등 카드에 박힐 단일 수치 위주. value는 8자 이내 (예: $3+, 04.21, +$4T, 10AM ET).\n"
                "\n"
                "★★ stat 필드 특수 제약 (카드 인덱스 02, 03은 디자인에 직접 박히므로 아래 형식 엄수):\n"
                "- 카드 인덱스 02 (n='03', 3번째 카드, FED/POLICY/SCHEDULE):\n"
                "    * stat.value: 날짜 형식 \"MM.DD DAY\" 고정 (예: \"04.21 MON\", \"05.03 FRI\"). 정확히 9자.\n"
                "    * stat.unit: 시각 형식 \"HH AM/PM ET\" (예: \"10AM ET\", \"2PM ET\", \"9:30AM ET\"). 7자 이내.\n"
                "    * 박스에 \"📅 {value} · {unit}\" 모양으로 렌더링되므로 둘 다 비우지 말 것.\n"
                "    * 이벤트 일정(청문회/FOMC/CPI 발표 등)이 없으면 가장 임박한 경제 일정 기준으로 채울 것.\n"
                "- 카드 인덱스 03 (n='04', 4번째 카드, BIG TECH/AI/SEMICONDUCTOR):\n"
                "    * stat.label: 영문 대문자 키워드 1~2단어 (예: \"AI CHIP\", \"M&A\", \"EARNINGS\", \"CLOUD\"). 10자 이내.\n"
                "    * 박스에 \"🤖 {label}\" 모양으로 렌더링됨. 한글/소문자 금지, 공백 1개만 허용.\n"
                "- 다른 카드(01, 02, 05)의 stat은 카드에 직접 노출되지 않으므로 자유롭게 작성.\n"
                "\n"
                "★★ 카드 인덱스별 추가 제약 (공통 규칙보다 우선 — 디자인 박스 폭 맞춤):\n"
                "- 카드 인덱스 01 (n='02', GEOPOLITICS 권장): title 10자 이내. 공통 40자 규칙보다 짧게. 보라 제목 박스 폭이 좁아 반드시 준수.\n"
                "- 카드 인덱스 02 (n='03', FED 권장): tldr 11자 이내. 공통 15자 규칙보다 짧게. 노란 말풍선에 ✏️와 함께 한 줄로 들어가므로 반드시 준수.\n"
                "- 카드 인덱스 03 (n='04', BIG TECH 권장): title 11자 이내, tldr 12자 이내. 주황 제목 박스 폭이 좁고 손글씨 인사이트도 짧게 들어가야 해서 공통 규칙(title 40자 / tldr 15자)보다 훨씬 짧아야 함. highlight도 title 안에 포함되어야 하므로 title이 짧아지면 highlight도 자연히 짧아짐.\n"
                "- imageCaption은 영문 대/소문자 혼용, 장소·인물·개념 위주 (한글 금지).\n"
                "- ★★ unsplash_keywords 작성 규칙 (절대 준수):\n"
                "  * Unsplash 검색은 쉼표를 AND 조건으로 해석한다. 따라서 각 키워드는 짧고 검색 가능한 명사구여야 한다.\n"
                "  * 첫 키워드는 반드시 1~2 단어로 된 쉽게 검색되는 명사구. 이게 메인 검색어가 됨.\n"
                "      좋은 예: 'oil refinery', 'aircraft carrier', 'capitol building',\n"
                "              'computer chip', 'stock chart', 'container ship',\n"
                "              'federal reserve', 'data center', 'trading floor', 'oil tanker'\n"
                "      나쁜 예: 'senate hearing chamber' (3단어 너무 구체적 → zero hit),\n"
                "              'oil tanker strait middle east' (4단어 zero hit 보장),\n"
                "              'official testimony podium' (추상적 3단어)\n"
                "  * 두 번째부터는 fallback용 1~2 단어 명사구를 쉼표로 추가. 각 키워드는 독립적으로도 Unsplash에서 잘 검색되어야 함.\n"
                "  * 전체 쿼리는 최대 4개 키워드, 각 키워드는 1~2단어 엄수.\n"
                "  * 추상명사(growth, success, decline, opportunity, recovery, momentum, innovation 등) 절대 금지 — 시각 명사만.\n"
                "  * 인물명/좁은 지명/회사명 고유명사는 가능한 한 회피하고 일반 시각 명사 우선. 'nvidia chip'보다 'computer chip'이 매칭률 높음.\n"
                "  * 모두 영어 소문자, 쉼표 구분, 특수문자 금지.\n"
                "  * imageCaption(영문)과 같은 시각 도메인을 유지.\n"
                "\n"
                "  * 카테고리별 권장 예시 (참고용, 그대로 복붙 말고 기사에 맞게 변형):\n"
                "      ENERGY 호르무즈 폐쇄 → 'oil tanker, oil refinery, container ship'\n"
                "      GEOPOLITICS 군사 충돌 → 'aircraft carrier, military jet, naval ship'\n"
                "      FED 청문회/정책 → 'capitol building, federal reserve, official podium'\n"
                "      BIG TECH AI 칩 → 'computer chip, semiconductor wafer, data center'\n"
                "      MARKETS 증시/밸류 → 'stock chart, trading floor, financial graph'\n"
                "- n은 \"01\" ~ \"05\" 고정, 정확히 5개만 출력."
            ),
        }],
    )

    elapsed = _time.time() - t0
    log.info("Claude API [카드뉴스용] 응답 완료 (%.1f초)", elapsed)

    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw).strip()

    try:
        cards_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("카드뉴스 JSON 파싱 실패: %s", exc)
        return []

    log.info("카드뉴스 5대 뉴스 추출 완료: %d건", len(cards_data))
    return cards_data[:5]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2단계: Unsplash API — 사진 다운로드 (photo_0.jpg ~ photo_4.jpg)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 카드 tag 기반 카테고리 fallback — generic 직전에 시도
TAG_FALLBACKS = {
    "ENERGY": "oil refinery",
    "OIL": "oil refinery",
    "INDUSTRY": "factory interior",
    "COMMODITIES": "shipping port",
    "GEOPOLITICS": "military aircraft",
    "DEFENSE": "military aircraft",
    "FED": "federal reserve building",
    "POLICY": "capitol building",
    "SCHEDULE": "capitol building",
    "CPI": "stock chart",
    "BIG TECH": "computer chip",
    "TECH": "computer chip",
    "AI": "data center",
    "SEMICONDUCTOR": "semiconductor wafer",
    "MARKETS": "stock chart",
    "EARNINGS": "office building",
    "MACRO": "global finance",
}

GENERIC_FALLBACKS = ["business", "finance", "technology", "global economy", "stock market"]


def fetch_unsplash_image(keywords: str, index: int, card_tag: str = "") -> str:
    """Unsplash에서 키워드로 이미지를 검색하고 photo_{index}.jpg 로 저장.

    시도 순서 (Unsplash가 쉼표를 AND 조건으로 해석하는 특성 고려):
      a) full       — 전체 쿼리 그대로
      b) split[0]   — 메인 키워드 (첫 콤마 앞)
      c) split[1]   — 두 번째 키워드
      d) split[2]   — 세 번째 키워드 (있으면)
      e) tag        — 카드 tag 기반 카테고리 fallback (TAG_FALLBACKS)
      f) generic    — 마지막 generic 로테이션

    로그: [card N] stage=<단계> keyword='...' → matched: '<desc>' (<url>)
    """
    card_label = f"[card {index+1}]"

    if not UNSPLASH_ACCESS_KEY:
        log.warning("%s UNSPLASH_ACCESS_KEY 미설정 — placeholder로 폴백", card_label)
        return ""

    # 1) 시도 큐 구성: (stage 이름, 쿼리) 튜플 리스트
    parts = [p.strip() for p in keywords.split(",") if p.strip()]
    attempts: list[tuple[str, str]] = []

    if keywords.strip():
        attempts.append(("full", keywords.strip()))
    for i, p in enumerate(parts[:3]):
        if p and p != keywords.strip():
            attempts.append((f"split[{i}]", p))

    tag_key = (card_tag or "").strip().upper()
    if tag_key and tag_key in TAG_FALLBACKS:
        attempts.append(("tag", TAG_FALLBACKS[tag_key]))
    else:
        log.info("%s tag='%s' → TAG_FALLBACKS 미매핑 (generic 으로 직행)", card_label, card_tag)

    attempts.append(("generic", GENERIC_FALLBACKS[index % len(GENERIC_FALLBACKS)]))

    # 2) 중복 쿼리 제거 (stage 순서 유지)
    seen = set()
    dedup_attempts = []
    for stage, q in attempts:
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        dedup_attempts.append((stage, q))

    # 3) 순서대로 시도
    for stage, attempt_q in dedup_attempts:
        try:
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": attempt_q,
                    "per_page": 5,
                    "orientation": "squarish",
                    "content_filter": "high",
                },
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or []

            if not results:
                log.warning("%s stage=%-9s keyword='%s' → no results",
                            card_label, stage, attempt_q)
                continue

            top = results[0]
            desc = (top.get("description")
                    or top.get("alt_description")
                    or "(no description)")
            img_url = top["urls"]["regular"]
            page_url = (top.get("links") or {}).get("html", "")

            log.info("%s stage=%-9s keyword='%s' → MATCH: '%s' (%s)",
                     card_label, stage, attempt_q, desc, page_url or img_url)

            if len(results) > 1:
                alt_descs = [
                    (r.get("description") or r.get("alt_description") or "?")
                    for r in results[1:4]
                ]
                log.info("%s   other top results: %s", card_label, " | ".join(alt_descs))

            img_resp = requests.get(img_url, timeout=30)
            img_resp.raise_for_status()

            img_path = CARD_OUTPUT_DIR / f"photo_{index}.jpg"
            img_path.write_bytes(img_resp.content)
            log.info("%s 이미지 저장: %s (최종 stage=%s)",
                     card_label, img_path.name, stage)
            return img_path.name

        except Exception as exc:
            log.warning("%s stage=%-9s keyword='%s' 실패: %s",
                        card_label, stage, attempt_q, exc)
            continue

    log.error("%s 모든 Unsplash 검색 시도 실패", card_label)
    return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3단계: preview.html 생성 — cardnews/index.html 에 데이터 주입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _short_cover_date(date_str: str) -> str:
    """'2026.04.14 MON · 00:00 ET' → '04.14 MON' (표지 상단 배지용)."""
    m = re.search(r'\d{4}\.(\d{2}\.\d{2})\s+([A-Z]{3})', date_str)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return datetime.now().strftime('%m.%d %a').upper()


def _patch_photoslot_src(html: str) -> str:
    """뉴스 카드 5장 + CTA 폴라로이드 3장의 <PhotoSlot>에 src 주입.

    - PopNews01~04: src={item.image} (label={item.imageCaption} 로 식별)
    - PopNews05: src={item.image} (rect 78x28 로 식별)
    - CTA 3장 폴라로이드: src={(window.NEWS_ITEMS[i] || {}).image || ''} (NEWS_ITEMS 0~2)
    Cover의 "AI curated ✨" 폴라로이드는 그대로 placeholder 유지.
    """
    # Pattern A: PopNews01~04 — label={item.imageCaption} 을 포함한 PhotoSlot 4개
    patA = re.compile(
        r'(<PhotoSlot\b[^>]*?label=\{item\.imageCaption\}[^>]*?)/>',
        flags=re.DOTALL,
    )
    html, nA = patA.subn(r'\1 src={item.image} alt={item.imageCaption}/>', html)

    # Pattern B: PopNews05 — label 없이 shape="rect" w="78cqw" h="28cqw" borderColor=...
    patB = re.compile(
        r'(<PhotoSlot\s+shape="rect"\s+w="78cqw"\s+h="28cqw"\s+borderColor=\{popColors\.ink\})\s*/>',
        flags=re.DOTALL,
    )
    html, nB = patB.subn(r'\1 src={item.image} alt={item.imageCaption}/>', html)

    # Pattern C: CTA 폴라로이드 3장 (map rotate={rot}) — NEWS_ITEMS[0..2].image 를 주입
    patC = re.compile(
        r'(<PhotoSlot\s+shape="polaroid"\s+w="16cqw"\s+h="12cqw"\s+rotate=\{rot\})\s*/>',
        flags=re.DOTALL,
    )
    html, nC = patC.subn(
        r"\1 src={((window.NEWS_ITEMS || [])[i] || {}).image || ''}/>",
        html,
    )

    # Pattern D: Cover "AI curated ✨" 폴라로이드 — photo_0.jpg 리터럴 주입
    patD = re.compile(
        r'(<PhotoSlot\s+shape="polaroid"\s+w="24cqw"\s+h="18cqw"\s+rotate=\{7\}\s*\n?\s*'
        r'label="AI curated[^"]*"\s+labelSize="3\.4cqw")\s*/>',
        flags=re.DOTALL,
    )
    html, nD = patD.subn(r'\1 src="photo_0.jpg" alt="AI curated"/>', html)

    if nA != 4 or nB != 1 or nC != 1 or nD != 1:
        log.warning(
            "PhotoSlot src 주입 개수 불일치: A=%d B=%d C=%d D=%d (기대 4/1/1/1). 디자인이 바뀌었을 수 있음.",
            nA, nB, nC, nD,
        )
    else:
        log.info("PhotoSlot src 주입 완료: Cover 1 + 뉴스 5 + CTA map 1곳 (폴라로이드 3장)")
    return html


def build_preview_html(cards_data: list, date_str: str) -> Path:
    """cardnews/index.html 을 읽어 데이터/이미지/날짜를 주입한 preview.html 을 생성."""
    if not DESIGN_HTML_PATH.exists():
        raise FileNotFoundError(f"디자인 파일 없음: {DESIGN_HTML_PATH}")

    html = DESIGN_HTML_PATH.read_text(encoding="utf-8")

    # 1) NEWS_ITEMS 주입 (5개 뉴스 카드 데이터 + image 필드)
    news_items = []
    for i, card in enumerate(cards_data):
        img_filename = f"photo_{i}.jpg"
        img_exists = (CARD_OUTPUT_DIR / img_filename).exists()
        news_items.append({
            "n": card.get("n", f"{i+1:02d}"),
            "tag": card.get("tag", ""),
            "title": card.get("title", ""),
            "highlight": card.get("highlight", ""),
            "source": card.get("source", ""),
            "outlet": card.get("outlet", ""),
            "tldr": card.get("tldr", ""),
            "body": card.get("body", ""),
            "stat": card.get("stat", {"label": "", "value": "", "unit": "", "note": ""}),
            "imageCaption": card.get("imageCaption", ""),
            "image": img_filename if img_exists else "",
        })

    news_items_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    news_items_replacement = f"const NEWS_ITEMS = {news_items_json};"

    html, n1 = re.subn(
        r'const NEWS_ITEMS = \[.*?\];',
        lambda _m: news_items_replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n1 != 1:
        raise RuntimeError("NEWS_ITEMS 블록을 찾지 못함 — 디자인이 바뀌었을 수 있음")

    # 2) BRIEFING_META 주입 (Cover/CTA는 하드코딩이라 실제로는 안 읽지만 일관성 유지)
    short_cover_date = _short_cover_date(date_str)
    time_part_match = re.search(r'(\d{2}:\d{2}\s+ET)', date_str)
    time_part = time_part_match.group(1) if time_part_match else ""

    meta = {
        "date": short_cover_date,
        "time": time_part,
        "brand": "미국 경제 AI 브리핑",
        "tagline": "AI가 골라주는 진짜 핵심만",
        "kakaoLabel": "KAKAO OPENCHAT",
    }
    meta_json = json.dumps(meta, ensure_ascii=False, indent=2)
    meta_replacement = f"const BRIEFING_META = {meta_json};"
    html, n2 = re.subn(
        r'const BRIEFING_META = \{.*?\};',
        lambda _m: meta_replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n2 != 1:
        log.warning("BRIEFING_META 블록을 찾지 못함")

    # 3) Cover 상단 배지의 하드코딩 날짜 ("DAILY · 04.19 SUN") → 오늘 날짜
    html, n3 = re.subn(
        r'DAILY · \d{2}\.\d{2}\s+[A-Z]{3}',
        f'DAILY · {short_cover_date}',
        html,
    )
    if n3 >= 1:
        log.info("Cover 날짜 치환: DAILY · %s", short_cover_date)
    else:
        log.warning("Cover 날짜 문자열을 찾지 못함 (디자인이 바뀌었을 수 있음)")

    # 4) PopNews01~05 의 PhotoSlot 에 src={item.image} 주입
    html = _patch_photoslot_src(html)

    # 5) PopNews03 파란 date pill — "📅 04.21 MON · 10AM ET" 리터럴을 cards_data[2].stat 으로 치환
    if len(cards_data) >= 3:
        stat3 = cards_data[2].get("stat") or {}
        new_pill = f"📅 {stat3.get('value', '')} {stat3.get('unit', '')}".strip()
        html, n5 = re.subn(r'📅 04\.21 MON · 10AM ET', new_pill, html, count=1)
        if n5 != 1:
            log.warning("PopNews03 date pill 치환 실패 (매칭 %d회) — 디자인이 바뀌었을 수 있음", n5)
        else:
            log.info("PopNews03 date pill 치환 완료: '%s'", new_pill)
    else:
        log.warning("cards_data 길이 %d — PopNews03 date pill 치환 스킵", len(cards_data))

    # 6) PopNews04 라임 sticker — "🤖 AI CHIP" 리터럴을 cards_data[3].stat.label 로 치환
    if len(cards_data) >= 4:
        stat4 = cards_data[3].get("stat") or {}
        new_sticker = f"🤖 {stat4.get('label', '')}".strip()
        html, n6 = re.subn(r'🤖 AI CHIP', new_sticker, html, count=1)
        if n6 != 1:
            log.warning("PopNews04 sticker 치환 실패 (매칭 %d회) — 디자인이 바뀌었을 수 있음", n6)
        else:
            log.info("PopNews04 sticker 치환 완료: '%s'", new_sticker)
    else:
        log.warning("cards_data 길이 %d — PopNews04 sticker 치환 스킵", len(cards_data))

    # 7) PopNews04 주황 제목 박스 폰트 사이즈 축소 (4.6cqw → 3.4cqw, card_03 노란 박스와 동일)
    #    — background:popColors.orange 를 anchor 로 anchored-lookahead 하여 PopNews04 주황 박스만 타깃
    #      (fontSize:"4.6cqw" 는 index.html 에 3곳 있음 — 주황/핑크/스카이블루. orange 앵커로 유일하게 지목)
    html, n7 = re.subn(
        r'(background:popColors\.orange,[\s\S]{0,300}?fontSize:")4\.6cqw(")',
        r'\g<1>3.4cqw\g<2>',
        html,
        count=1,
    )
    if n7 != 1:
        log.warning("PopNews04 주황 박스 폰트 사이즈 치환 실패 (매칭 %d회) — 디자인이 바뀌었을 수 있음", n7)
    else:
        log.info("PopNews04 주황 박스 폰트 사이즈 치환 완료: 4.6cqw → 3.4cqw")

    PREVIEW_HTML_PATH.write_text(html, encoding="utf-8")
    log.info("preview.html 생성: %s", PREVIEW_HTML_PATH)
    return PREVIEW_HTML_PATH


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4단계: Playwright — 각 카드를 1080x1080 PNG로 캡처
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_CAPTURE_SETUP_JS = r"""
() => {
  // 오프스크린이 아닌 최상위 오버레이에 1080x1080 로 카드 1장만 마운트한다.
  // Playwright 가 headless 로 돌기 때문에 사용자에게는 보이지 않음.
  const holder = document.createElement('div');
  holder.id = '__cap_holder';
  holder.style.cssText =
    'position:fixed;left:0;top:0;width:1080px;height:1080px;' +
    'background:#ffffff;z-index:2147483647;';
  document.body.appendChild(holder);

  window.__captureRender = async (idx) => {
    const h = document.getElementById('__cap_holder');
    h.innerHTML = '';
    const mount = document.createElement('div');
    mount.style.cssText = 'width:1080px;height:1080px;';
    h.appendChild(mount);

    const Card = window.PopOption.cards[idx];
    const root = window.ReactDOM.createRoot(mount);
    root.render(window.React.createElement(Card));

    // React 커밋 대기
    await new Promise(r => setTimeout(r, 600));
    if (document.fonts && document.fonts.ready) {
      try { await document.fonts.ready; } catch (e) {}
    }
    // <img> 로딩 대기 (실패 시 onError 가 placeholder 로 폴백)
    const imgs = Array.from(mount.querySelectorAll('img'));
    await Promise.all(imgs.map(img => {
      if (img.complete) return Promise.resolve();
      return new Promise(r => {
        img.addEventListener('load', r, { once: true });
        img.addEventListener('error', r, { once: true });
      });
    }));
    // 폴백이 발생했다면 재렌더 완료 대기
    await new Promise(r => setTimeout(r, 400));
  };
}
"""


async def render_preview_to_pngs(preview_path: Path) -> list:
    """preview.html을 열고 각 카드를 1080x1080 PNG로 캡처."""
    from playwright.async_api import async_playwright

    png_paths = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1400, "height": 1200},
            device_scale_factor=1,
        )
        page = await context.new_page()

        await page.goto(preview_path.resolve().as_uri(), wait_until="networkidle")

        # React + window.PopOption 마운트 완료 대기
        await page.wait_for_function(
            "() => window.PopOption && Array.isArray(window.PopOption.cards) && window.PopOption.cards.length > 0",
            timeout=20000,
        )
        # 폰트 로딩 대기
        try:
            await page.evaluate(
                "async () => { if (document.fonts && document.fonts.ready) { await document.fonts.ready; } }"
            )
        except Exception:
            pass
        await page.wait_for_timeout(1200)

        # 오프스크린 캡처용 헬퍼 설치
        await page.evaluate(_CAPTURE_SETUP_JS)

        # 카드 개수 확인 (기본 7 = Cover + 5 News + CTA)
        n_cards = await page.evaluate("window.PopOption.cards.length")
        log.info("캡처 대상 카드: %d장", n_cards)

        for i in range(n_cards):
            await page.evaluate(f"window.__captureRender({i})")
            holder = page.locator("#__cap_holder")
            png_path = CARD_OUTPUT_DIR / f"card_{i+1:02d}.png"
            await holder.screenshot(path=str(png_path), type="png")
            png_paths.append(png_path)
            log.info("스크린샷 생성: %s", png_path.name)

        await browser.close()

    log.info("PNG 이미지 %d개 생성 완료", len(png_paths))
    return png_paths


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 통합 함수 — news_bot에서 호출 (시그니처 불변)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_card_news(docs_blocks: list, date_str: str) -> tuple:
    """
    메인 함수. docs_blocks를 받아 카드뉴스 PNG 7장을 생성.
    (PNG 파일 경로 리스트, cards_data) 튜플을 반환.

    사용법 (news_bot.py에서):
        from card_news_generator import generate_card_news
        png_files, cards_data = generate_card_news(docs_blocks, "2026.04.14 MON · 00:00 ET")
    """
    import asyncio

    log.info("=== 카드뉴스 생성 시작 (Y2K Sticker Pop) ===")
    t_total = _time.time()

    # 0. 이전 산출물 정리 (다른 파일명 패턴이 남아 있으면 downstream glob이 섞어서 집음)
    for stale in CARD_OUTPUT_DIR.glob("card_*.png"):
        try:
            stale.unlink()
        except OSError:
            pass
    for stale in CARD_OUTPUT_DIR.glob("card_*.html"):
        try:
            stale.unlink()
        except OSError:
            pass

    # 1. Claude 로 5대 뉴스 추출 (새 스키마)
    cards_data = extract_card_news_data(docs_blocks)
    if not cards_data:
        log.error("카드뉴스 데이터 추출 실패")
        return [], []

    # 2. Unsplash 이미지 다운로드 (photo_0.jpg ~ photo_4.jpg)
    for i, card in enumerate(cards_data):
        keywords = card.get("unsplash_keywords", "economy news")
        card_tag = card.get("tag", "")
        fetch_unsplash_image(keywords, i, card_tag=card_tag)

    # 3. preview.html 생성 (cardnews/index.html + 데이터 주입)
    preview_path = build_preview_html(cards_data, date_str)

    # 4. Playwright 로 카드별 PNG 캡처
    png_paths = asyncio.run(render_preview_to_pngs(preview_path))

    log.info("=== 카드뉴스 생성 완료 (%.1f초, %d장) ===", _time.time() - t_total, len(png_paths))
    return [str(p) for p in png_paths], cards_data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI 진입점
#   python card_news_generator.py         → 실제 RSS 수집 + 분석 + 카드뉴스 생성
#   python card_news_generator.py test    → 샘플 docs_blocks로 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_SAMPLE_BLOCKS = [
    {"type": "section", "text": "시장 시황 및 분위기"},
    {"type": "body", "text": "미국 증시가 폐장한 가운데, 아시아 시장은 중동 긴장 완화 기대감으로 상승했습니다."},
    {"type": "section", "text": "주요 뉴스 심층 분석"},
    {"type": "article", "text": "1. 호르무즈 해협 통항 사실상 전면 중단 — 유가 급등"},
    {"type": "body", "text": "호르무즈 해협 선박 총격 이후 이란이 재폐쇄 조치를 취하며 통항이 멈췄습니다."},
    {"type": "source", "text": "출처: Hormuz Shipping Traffic Grinds to a Halt · Bloomberg"},
    {"type": "article", "text": "2. 트럼프, 이란 '휴전 전면 위반' 공습 재개 경고"},
    {"type": "body", "text": "트럼프 대통령이 이란의 휴전 위반을 비난하며 공습 재개 가능성을 경고했습니다."},
    {"type": "source", "text": "출처: Trump accuses Iran of total violation · Investing.com"},
    {"type": "article", "text": "3. 연준 의장 후보 케빈 워시 4월 21일 인사청문회"},
    {"type": "body", "text": "미국 상원 은행위원회가 연준 의장 지명자 케빈 워시의 청문회를 잡았습니다."},
    {"type": "source", "text": "출처: Fed Chair Nominee Kevin Warsh Hearing · Bloomberg"},
    {"type": "article", "text": "4. 구글, 마블과 AI 칩 공동 개발 협의"},
    {"type": "body", "text": "구글이 엔비디아 의존도를 낮추기 위해 마블과 자체 AI 칩 개발을 논의 중입니다."},
    {"type": "source", "text": "출처: Google in talks with Marvell · The Information"},
    {"type": "article", "text": "5. FT '시장의 새 밸류에이션 키워드 EBITDA'"},
    {"type": "body", "text": "FT는 이란·관세·정책 불확실성을 제외한 이익을 바라보는 EBITDA 심리를 짚었습니다."},
    {"type": "source", "text": "출처: The stock market's new approach to valuation · FT"},
]


def _run_test() -> None:
    result = generate_card_news(_SAMPLE_BLOCKS, "2026.04.20 MON · 00:00 ET")
    png_files, _ = result
    print("\n[완료] 생성된 PNG:")
    for p in png_files:
        print(f"   {p}")


def _run_live() -> None:
    """실제 RSS 수집 → Claude 분석 → 카드뉴스 생성 → Gmail 발송."""
    # news_bot 의 수집/분석 함수를 재사용 (노션/카카오 전송은 생략)
    from news_bot import fetch_news, analyze_news, _get_market_context, ET, KST

    now_et = datetime.now(ET)
    now_kst = now_et.astimezone(KST)
    log.info("=== [단독 실행] %s ET / %s KST ===", now_et.strftime('%H:%M'), now_kst.strftime('%H:%M'))

    market_context, _status, is_weekend = _get_market_context(now_et)

    articles = fetch_news()
    if not articles:
        log.error("수집된 기사 없음 — 종료")
        return

    docs_blocks, _analysis = analyze_news(articles, market_context, is_weekend)

    card_date_str = f"{now_et.strftime('%Y.%m.%d %a').upper()} · {now_et.strftime('%H:%M')} ET"
    png_files, cards_data = generate_card_news(docs_blocks, card_date_str)

    print("\n[완료] 생성된 PNG:")
    for p in png_files:
        print(f"   {p}")

    # Gmail 발송 — 자동 스케줄과 동일 함수/동일 환경변수(GMAIL_ADDRESS) 사용
    if not png_files:
        log.error("PNG가 없어 Gmail 발송 생략")
        return

    try:
        from gmail_sender import send_card_news_email
        log.info("=== Gmail 발송 시작 ===")
        sent = send_card_news_email(png_files, cards_data, card_date_str)
        if sent:
            print("\n[완료] Gmail 발송 성공")
        else:
            print("\n[실패] Gmail 발송 실패 — 로그를 확인해 주세요")
    except Exception:
        log.exception("Gmail 발송 중 예외 발생")
        print("\n[실패] Gmail 발송 중 예외 — 로그를 확인해 주세요")


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        _run_test()
    else:
        _run_live()
