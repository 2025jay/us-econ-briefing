"""
Gmail 카드뉴스 발송 모듈

card_news_generator가 생성한 PNG 7장을 본문 인라인 이미지로 담아
Gmail SMTP로 자기 자신에게 발송.

환경변수:
  GMAIL_ADDRESS       - 발신자 Gmail 주소 (수신자도 동일)
  GMAIL_APP_PASSWORD  - Gmail 앱 비밀번호 16자리 (공백 제거)

사용법 (news_bot.py에서):
    from gmail_sender import send_card_news_email
    send_card_news_email(png_files, cards_data, date_str)
"""

import os
import smtplib
import logging
import time as _time
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid, formataddr
from email.header import Header

log = logging.getLogger(__name__)

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML 본문 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_html_body(cards_data: list, image_cids: list, date_str: str) -> str:
    """인라인 이미지(cid:...)를 참조하는 HTML 본문을 생성."""
    # 이미지 7장을 순서대로 배치
    images_html = ""
    for i, cid in enumerate(image_cids):
        cid_clean = cid.strip("<>")
        images_html += (
            f'<div style="margin-bottom:16px;">'
            f'<img src="cid:{cid_clean}" '
            f'style="width:100%;max-width:540px;border-radius:12px;display:block;" '
            f'alt="card {i+1}"></div>\n'
        )

    # 5대 뉴스 텍스트 요약 (cards_data가 있을 때만)
    news_list_html = ""
    if cards_data:
        for i, card in enumerate(cards_data[:5], 1):
            headline = card.get("headline", "").replace("\\n", " ")
            news_list_html += f'<li style="margin-bottom:8px;"><b>{i}.</b> {headline}</li>\n'

    top5_section = ""
    if news_list_html:
        top5_section = f"""
    <div style="background:white;border-radius:16px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
      <div style="font-size:13px;color:#6366F1;font-weight:700;letter-spacing:1px;margin-bottom:12px;">TODAY'S TOP 5</div>
      <ol style="padding-left:20px;margin:0;font-size:15px;line-height:1.7;color:#334155;">
        {news_list_html}
      </ol>
    </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:'Noto Sans KR','Malgun Gothic',sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:32px 20px;">

    <div style="text-align:center;margin-bottom:28px;">
      <div style="display:inline-block;background:#6366F1;color:white;font-size:13px;font-weight:700;padding:6px 16px;border-radius:20px;letter-spacing:1px;">
        GLOBAL ECONOMY AI BRIEFING
      </div>
      <h1 style="font-size:26px;font-weight:900;color:#1e293b;margin:16px 0 8px;">
        오늘의 경제 카드뉴스
      </h1>
      <div style="font-size:14px;color:#64748b;">{date_str}</div>
    </div>
    {top5_section}
    <div style="background:white;border-radius:16px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
      {images_html}
    </div>

    <div style="text-align:center;margin-top:28px;padding-top:20px;border-top:1px solid #e2e8f0;font-size:12px;color:#94a3b8;">
      Automated by News Bot · Powered by Claude AI
    </div>

  </div>
</body>
</html>"""
    return html


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메일 발송 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_card_news_email(png_paths: list, cards_data: list, date_str: str) -> bool:
    """
    카드뉴스 PNG를 인라인 이미지로 담아 Gmail 발송 (자기 자신에게).

    Args:
        png_paths: PNG 파일 경로 리스트
        cards_data: 5대 뉴스 데이터 (본문 상단 요약용, None/빈 리스트 허용)
        date_str: "2026.04.19 SUN · 18:00 ET" 형식

    Returns:
        성공 여부
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        log.error("Gmail 환경변수 미설정 (GMAIL_ADDRESS, GMAIL_APP_PASSWORD)")
        return False

    if not png_paths:
        log.error("전송할 PNG 파일이 없음")
        return False

    log.info("=== Gmail 카드뉴스 발송 시작 (%d장) ===", len(png_paths))
    t0 = _time.time()

    try:
        # ── MIME 구조: multipart/related (HTML 본문 + 인라인 이미지들) ──
        msg = MIMEMultipart("related")
        msg["Subject"] = Header(f"📊 {date_str} 오늘의 경제 카드뉴스", "utf-8")
        msg["From"] = formataddr(("News Bot", GMAIL_ADDRESS))
        msg["To"] = GMAIL_ADDRESS  # 자기 자신에게 발송

        # ── PNG 파일들을 Content-ID로 첨부 ──
        image_cids = []
        image_parts = []
        for i, png_path in enumerate(png_paths):
            png_path_obj = Path(png_path)
            if not png_path_obj.exists():
                log.warning("PNG 파일 없음 — 건너뜀: %s", png_path_obj)
                continue

            with open(png_path_obj, "rb") as f:
                img = MIMEImage(f.read(), _subtype="png")

            cid = make_msgid(domain="newsbot.local")
            img.add_header("Content-ID", cid)
            img.add_header("Content-Disposition", "inline", filename=png_path_obj.name)
            image_parts.append(img)
            image_cids.append(cid)

        if not image_cids:
            log.error("첨부된 이미지가 없음")
            return False

        # ── HTML 본문 생성 ──
        html_body = _build_html_body(cards_data, image_cids, date_str)

        # ── multipart/alternative (HTML + plain text fallback) ──
        alt = MIMEMultipart("alternative")
        plain = MIMEText(
            f"{date_str} 오늘의 경제 카드뉴스\n"
            f"이메일 클라이언트에서 HTML 보기를 활성화해주세요.",
            "plain", "utf-8"
        )
        html = MIMEText(html_body, "html", "utf-8")
        alt.attach(plain)
        alt.attach(html)

        # multipart/related의 첫 part는 본문(alternative), 그 뒤로 이미지들
        msg.attach(alt)
        for img_part in image_parts:
            msg.attach(img_part)

        # ── SMTP 발송 ──
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)

        log.info(
            "=== Gmail 발송 완료 (%.1f초, 이미지 %d장, 받는사람: %s) ===",
            _time.time() - t0, len(image_cids), GMAIL_ADDRESS
        )
        return True

    except smtplib.SMTPAuthenticationError as exc:
        log.error(
            "Gmail 인증 실패: %s — GMAIL_APP_PASSWORD가 맞는지, "
            "2단계 인증이 켜져있는지 확인하세요.", exc
        )
        return False
    except Exception as exc:
        log.exception("Gmail 발송 중 오류: %s", exc)
        return False


# 단독 테스트용
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("⚠️  환경변수 GMAIL_ADDRESS, GMAIL_APP_PASSWORD를 먼저 설정하세요.")
        exit(1)

    # card_news_output 폴더에서 최신 PNG 7장을 찾아서 테스트 발송
    base_dir = Path(__file__).parent
    card_dir = base_dir / "card_news_output"
    png_files = sorted(card_dir.glob("card_*.png"))

    if not png_files:
        print(f"⚠️  {card_dir}에 PNG 파일이 없습니다. 먼저 카드뉴스를 생성해주세요.")
        exit(1)

    print(f"테스트 발송 시작: {len(png_files)}장")
    success = send_card_news_email(
        png_paths=[str(p) for p in png_files],
        cards_data=None,  # 5대 뉴스 텍스트는 생략
        date_str="테스트 발송",
    )
    print(f"결과: {'✅ 성공' if success else '❌ 실패'}")
