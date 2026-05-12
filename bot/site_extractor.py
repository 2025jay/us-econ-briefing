"""
docs_blocks(노션용 큰 JSON)에서 사이트용 5개 이슈 + intro를 추출.

Claude Haiku 1회 호출 (저렴, ~$0.005/회).
news_bot의 1차 노션 분석이 끝난 뒤 그 결과(docs_blocks)를 그대로 입력으로 받음.
따라서 RSS 재수집·재분석 없음.

반환:
{
  "briefing_intro": "오늘은 ...",
  "items": [
    { "title": "...", "body": "...", "source": "주요 외신" },
    ... 5개
  ]
}
"""

from __future__ import annotations

import os
import re
import json
import logging
import time as _time

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()


def extract_for_site(docs_blocks: list) -> dict:
    """노션용 docs_blocks → 사이트용 5개 이슈 + 인트로."""
    full_text = "\n".join(b.get("text", "") for b in docs_blocks if b.get("text"))

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=120.0)

    log.info("Claude API [사이트용] 호출 시작")
    t0 = _time.time()

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2200,
        messages=[{
            "role": "user",
            "content": (
                "아래는 오늘의 미국 경제 뉴스 브리핑 전문입니다.\n\n"
                f"{full_text}\n\n"
                "위 브리핑에서 카카오톡 오픈채팅 공유용 웹사이트에 올릴 콘텐츠를 뽑아주세요.\n"
                "MZ 친화적, 캐주얼·친근한 톤. 너무 딱딱하지 않게.\n\n"
                "반드시 아래 JSON 형식으로만 출력하세요. 다른 텍스트, 마크다운, 코드블록 없이.\n\n"
                "{\n"
                '  "briefing_intro": "오늘 미국장 분위기를 2~3문장으로 캐주얼하게 요약. \\"오늘은\\"으로 시작 추천.",\n'
                '  "items": [\n'
                '    {\n'
                '      "title": "한국어 헤드라인 (24자 이내, 한 줄)",\n'
                '      "body": "4~5문장 본문. \\"~예요\\", \\"~했어요\\" 톤. 핵심 사실 → 수치/배경 → 영향 순. 투자 권유 금지.",\n'
                '      "source": "주요 외신"\n'
                "    }\n"
                "    ... 정확히 5개\n"
                "  ]\n"
                "}\n\n"
                "엄격한 규칙:\n"
                "- items는 반드시 5개. 모자라면 가벼운 뉴스라도 채우고, 넘치면 가장 중요한 5개만.\n"
                '- source 필드는 매체명 직접 노출 금지. 무조건 "주요 외신"으로 통일.\n'
                "- title은 24자 이내 한 줄. 클릭베이트 금지. 한국어로 의역 OK.\n"
                "- body 톤: 친근한 ~요체. 예) \"발표했어요\", \"오르고 있어요\", \"눈여겨볼 만해요\".\n"
                "- body에 숫자/수치 나오면 원문 그대로 인용. 절대 만들지 말기.\n"
                "- 마크다운, 이모지, 번호 매기기, 줄바꿈 기호 사용 금지.\n"
                "- 가장 중요한 뉴스가 items[0]에 오도록 정렬.\n"
            ),
        }],
    )
    elapsed = _time.time() - t0
    log.info("Claude API [사이트용] 응답 완료 (%.1f초)", elapsed)

    raw = resp.content[0].text.strip()

    # 코드블록 래핑 제거
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("사이트용 JSON 파싱 실패: %s", exc)
        log.error("원본 (첫 500자): %s", raw[:500])
        # fallback: 빈 결과
        return {"briefing_intro": "", "items": []}

    items = data.get("items") or []
    # 무조건 source는 "주요 외신"으로 강제 (Claude가 매체명 흘려도 가림)
    for item in items:
        item["source"] = "주요 외신"
        # title 길이 제한 (혹시 길게 나왔으면 자름)
        if len(item.get("title", "")) > 30:
            item["title"] = item["title"][:28] + "…"

    # 5개로 맞춤
    items = items[:5]

    intro = data.get("briefing_intro", "")
    log.info(
        "사이트용 추출 완료: intro %d자, items %d개",
        len(intro), len(items),
    )
    return {"briefing_intro": intro, "items": items}
