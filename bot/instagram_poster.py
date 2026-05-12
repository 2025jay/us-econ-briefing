"""
인스타그램 캐러셀 자동 게시 모듈

Meta Graph API를 사용하여 카드뉴스 이미지를 캐러셀 포스트로 업로드.

환경변수:
  INSTAGRAM_ACCESS_TOKEN  - Meta Graph API 장기 액세스 토큰
  INSTAGRAM_ACCOUNT_ID    - 인스타그램 비즈니스 계정 ID
  IMGBB_API_KEY           - imgbb 이미지 호스팅 API 키

사전 준비:
  1. 인스타 계정을 비즈니스/크리에이터로 전환
  2. Facebook 페이지 생성 + 인스타 연결
  3. Meta for Developers에서 앱 생성
  4. Instagram Graph API 권한 활성화
  5. 장기 액세스 토큰 발급
"""

import os
import json
import logging
import time as _time
from pathlib import Path
from datetime import datetime

import requests

log = logging.getLogger(__name__)

INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이미지 호스팅 (imgbb 무료 업로드)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Meta Graph API는 공개 URL이 필요하므로 로컬 파일을 임시 호스팅해야 함.

IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "").strip()


def upload_image_to_imgbb(image_path: str) -> str:
    """이미지를 imgbb에 업로드하고 공개 URL을 반환."""
    if not IMGBB_API_KEY:
        log.error("IMGBB_API_KEY 미설정")
        return ""

    try:
        import base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": image_data,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        url = data["data"]["url"]
        log.info("imgbb 업로드 완료: %s → %s", Path(image_path).name, url)
        return url
    except Exception as exc:
        log.error("imgbb 업로드 실패 (%s): %s", image_path, exc)
        return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Instagram Graph API — 캐러셀 게시
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _create_media_container(image_url: str, is_carousel_item: bool = True) -> str:
    """단일 이미지의 미디어 컨테이너를 생성. container ID 반환."""
    params = {
        "image_url": image_url,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    if is_carousel_item:
        params["is_carousel_item"] = "true"

    resp = requests.post(
        f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
        data=params,
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    log.info("미디어 컨테이너 생성: %s", container_id)
    return container_id


def _create_carousel_container(children_ids: list, caption: str) -> str:
    """캐러셀 컨테이너를 생성. container ID 반환."""
    resp = requests.post(
        f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    log.info("캐러셀 컨테이너 생성: %s", container_id)
    return container_id


def _publish_container(container_id: str) -> str:
    """컨테이너를 실제로 게시. 게시물 ID 반환."""
    resp = requests.post(
        f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    post_id = resp.json()["id"]
    log.info("인스타그램 게시 완료: %s", post_id)
    return post_id


def _wait_for_container(container_id: str, max_wait: int = 60):
    """컨테이너가 준비될 때까지 대기."""
    for _ in range(max_wait // 5):
        resp = requests.get(
            f"{GRAPH_API_BASE}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15,
        )
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            log.error("컨테이너 에러: %s", resp.json())
            return False
        _time.sleep(5)
    log.error("컨테이너 준비 타임아웃: %s", container_id)
    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 통합 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_caption(cards_data: list = None) -> str:
    """인스타그램 캡션 생성."""
    now = datetime.now()
    date_str = now.strftime("%Y.%m.%d")

    caption = (
        f"📊 {date_str} 글로벌 경제 AI 브리핑\n"
        f"\n"
        f"AI가 매일 4회 정리하는 글로벌 경제 핵심 뉴스\n"
        f"밀어서 오늘의 브리핑을 확인하세요 👉\n"
        f"\n"
    )

    if cards_data:
        for i, card in enumerate(cards_data[:5], 1):
            headline = card.get("headline", "").replace("\\n", " ")
            caption += f"{i}️⃣ {headline}\n"
        caption += "\n"

    caption += (
        "💬 매일 실시간 브리핑을 받고 싶다면?\n"
        "카카오 오픈채팅 → '글로벌 경제 AI 브리핑' 검색\n"
        "\n"
        "#경제뉴스 #글로벌경제 #AI브리핑 #투자 #주식 #MZ재테크 "
        "#나스닥 #환율 #부동산 #경제공부 #재테크 #금융 "
        "#오늘의경제 #경제브리핑 #인스타경제"
    )
    return caption


def post_carousel_to_instagram(png_paths: list, cards_data: list = None) -> str:
    """
    PNG 이미지 리스트를 인스타그램 캐러셀로 게시.
    게시물 ID를 반환.

    사용법 (news_bot.py에서):
        from instagram_poster import post_carousel_to_instagram
        post_id = post_carousel_to_instagram(png_files, cards_data)
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        log.error("인스타그램 환경변수 미설정 (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)")
        return ""

    log.info("=== 인스타그램 게시 시작 (%d장) ===", len(png_paths))
    t0 = _time.time()

    # 1. 이미지를 imgbb에 업로드 (Meta API에는 공개 URL 필요)
    image_urls = []
    for path in png_paths:
        url = upload_image_to_imgbb(path)
        if url:
            image_urls.append(url)

    if len(image_urls) < 2:
        log.error("업로드된 이미지가 2장 미만 — 캐러셀 게시 불가")
        return ""

    # 2. 각 이미지의 미디어 컨테이너 생성
    children_ids = []
    for url in image_urls:
        cid = _create_media_container(url)
        children_ids.append(cid)

    # 3. 캐러셀 컨테이너 생성
    caption = generate_caption(cards_data)
    carousel_id = _create_carousel_container(children_ids, caption)

    # 4. 준비 대기
    if not _wait_for_container(carousel_id):
        log.error("캐러셀 컨테이너 준비 실패")
        return ""

    # 5. 게시
    post_id = _publish_container(carousel_id)

    log.info("=== 인스타그램 게시 완료 (%.1f초) ===", _time.time() - t0)
    return post_id
