"""
사이트용 콘텐츠 추출 — 노션 docs_blocks를 그대로 미러링.

추가 Claude 호출 없음. 노션과 동일 콘텐츠 그대로 사이트에 표시되도록
docs_blocks를 파싱해서 항목 리스트(title/body/source)로 펼침.
"""

from __future__ import annotations

import re
import logging

log = logging.getLogger(__name__)


def extract_for_site(docs_blocks: list) -> dict:
    """
    docs_blocks → { briefing_intro, items: [{title, body, source}, ...] }

    파싱 규칙:
    - section "시장 시황 및 분위기" 아래의 body들을 briefing_intro로 합침
    - article 블록을 만나면 새 item 시작 (앞쪽 "1. " 같은 번호는 제거)
    - 이어지는 body 블록들은 해당 item의 body로 누적
    - source 블록은 "주요 외신"으로 통일 (매체명 노출 금지)
    - section "주목할 일정"/"섹터별 동향" 등은 별도 항목으로 처리하지 않고 흘려보냄
    """
    items: list[dict] = []
    intro_parts: list[str] = []
    current: dict | None = None
    current_section = ""

    for block in docs_blocks:
        btype = block.get("type", "")
        text = (block.get("text") or "").strip()
        if not text:
            continue

        if btype == "section":
            # article 누적 중이면 마무리
            if current and current.get("title"):
                items.append(current)
                current = None
            current_section = text
            continue

        if btype == "article":
            # 새 article 시작 — 앞 번호 제거 ("1. 트럼프..." → "트럼프...")
            if current and current.get("title"):
                items.append(current)
            title = re.sub(r"^\d+\.\s*", "", text).strip()
            current = {"title": title, "body": "", "source": "주요 외신"}
            continue

        if btype == "body":
            # 시장 시황 섹션이면 intro에 합침
            if "시장 시황" in current_section or "시장 분위기" in current_section:
                intro_parts.append(text)
                continue

            # 그 외에는 현재 article의 body에 누적
            if current is not None:
                if current["body"]:
                    current["body"] += "\n\n" + text
                else:
                    current["body"] = text
            else:
                # article이 아직 없는 body — intro로 흡수
                intro_parts.append(text)
            continue

        if btype == "source":
            # 매체명은 노출하지 않음 — "주요 외신" 통일 (이미 기본값)
            continue

        if btype == "title":
            # 표제는 무시
            continue

    # 마지막 article 마무리
    if current and current.get("title"):
        items.append(current)

    # intro는 처음 1~2 문단만 (너무 길지 않게)
    briefing_intro = "\n\n".join(intro_parts[:2])
    if len(briefing_intro) > 600:
        briefing_intro = briefing_intro[:600].rsplit(" ", 1)[0] + "…"

    log.info(
        "사이트용 추출 (노션 미러): intro %d자, items %d개",
        len(briefing_intro), len(items),
    )
    return {"briefing_intro": briefing_intro, "items": items}
