# ☕ 미국 경제 AI 브리핑

매일 한국시간 **오전 8:30**, **오후 8:30**에 새 미국 경제 브리핑이 자동으로 게시되는 웹앱.

```
GitHub Actions (cron) ──► Python 봇 ──► RSS 수집 + Claude Haiku 분석
                                          │
                                          ├──► Supabase (briefing 스키마)
                                          │      ▲
                                          │      │  Next.js SSR로 읽음
                                          ├──► Notion 페이지 (백업)
                                          ├──► 카카오톡 "내게쓰기" (사이트 링크 포함)
                                          └──► Gmail 카드뉴스 (선택)
```

---

## 📦 진행 상황

- ✅ **Phase 1** — Next.js 시안 (디자인 토큰, 메인/상세/아카이브/로그인)
- ✅ **Phase 2** — 봇 클라우드 이전 (GitHub Actions) + Supabase 연동
- ⏳ **Phase 3** — Google 로그인 + 활동 로그
- ⏳ **Phase 4** — Vercel 프로덕션 배포

---

## 🗂 파일 구조

```
미국 경제 AI 브리핑/
├── app/                          # Next.js 14 App Router
│   ├── page.tsx                  # 메인 (Supabase에서 SSR)
│   ├── briefing/[date]/[session]/page.tsx
│   ├── archive/page.tsx
│   ├── login/page.tsx            # Phase 3 placeholder
│   ├── layout.tsx                # 폰트 로딩 (Pretendard/Jua/Single Day/JBMono)
│   └── globals.css
├── components/                   # React 컴포넌트들
├── lib/
│   ├── types.ts                  # Briefing/MarketStatus TS 타입
│   ├── supabase.ts               # Supabase 클라이언트 (briefing 스키마)
│   ├── queries.ts                # 모든 SSR 쿼리 — env 없으면 mock 폴백
│   ├── mockData.ts               # 개발용 더미 (queries에서 폴백으로 씀)
│   └── format.ts
├── bot/                          # Python 봇 (GitHub Actions에서 실행)
│   ├── news_bot.py               # 메인 파이프라인 (cloud 모드 추가됨)
│   ├── site_extractor.py         # docs_blocks → 사이트용 5개 이슈
│   ├── market_fetcher.py         # yfinance로 S&P/NASDAQ/DOW
│   ├── supabase_writer.py        # briefing.briefings에 upsert
│   ├── card_news_generator.py    # PNG 7장 생성 (cardnews/index.html 필요)
│   ├── gmail_sender.py           # SMTP + 앱 비밀번호
│   ├── instagram_poster.py       # (현재 미사용)
│   └── requirements.txt
├── supabase/
│   └── schema.sql                # briefing 전용 스키마
├── .github/workflows/
│   └── bot.yml                   # KST 08:30/20:30 cron
├── tailwind.config.ts            # 디자인 토큰
├── package.json
├── .env.example
└── README.md
```

---

## 🚀 셋업 가이드 (Phase 2)

### 1단계 — Supabase 스키마 설치

1. https://supabase.com 대시보드 → 사용할 프로젝트 클릭
2. 왼쪽 메뉴 **SQL Editor** → **New query**
3. `supabase/schema.sql` 파일 전체 내용 붙여넣기 → **Run**
4. ⚠️ **중요** — **Project Settings → API → Schema Exposure** 에서 `briefing` 스키마를 노출 목록에 추가하고 저장
5. 나중에 필요한 정보 메모해두기:
   - **Project URL** (Settings → API)
   - **anon public key** (사이트용 — 읽기 전용)
   - **service_role key** (봇용 — 쓰기 권한, 절대 클라이언트 노출 금지)

### 2단계 — GitHub 레포에 푸시

```bash
cd "6시간 USA 뉴스봇"
git init
git add .
git commit -m "phase 2: cloud bot + supabase"
git branch -M main
# 새 GitHub 레포 만들고
git remote add origin https://github.com/YOUR_USERNAME/us-econ-briefing.git
git push -u origin main
```

### 3단계 — GitHub Secrets 등록

레포 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Console에서 발급 |
| `KAKAO_REST_API_KEY` | 기존에 쓰던 카카오 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 아래 4단계에서 발급 |
| `NOTION_API_KEY` | 기존 노션 Integration 토큰 |
| `NOTION_PAGE_ID` | 기존 노션 상위 페이지 ID |
| `SUPABASE_URL` | `https://xxxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key (1단계에서 메모해둔 것) |
| `SITE_BASE_URL` | Vercel 배포 URL (없으면 일단 `http://localhost:3000` 넣어두기) |
| `GMAIL_ADDRESS` | 카드뉴스 받을 Gmail 주소 (= 발신자도 동일) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 16자리 (공백 제거) |
| `UNSPLASH_ACCESS_KEY` | 카드뉴스 사진용 (없으면 placeholder 이미지로 대체) |

레포 → **Settings → Actions → General → Workflow permissions → Read and write permissions** 도 체크.

### 4단계 — Kakao Refresh Token 1회 발급

GitHub Actions는 PC 브라우저 못 띄우니까 로컬에서 한 번만:

```bash
cd bot
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export KAKAO_REST_API_KEY=...
export NOTION_API_KEY=...
export NOTION_PAGE_ID=...
python news_bot.py --auth   # 브라우저 열려서 카카오 로그인
```

성공하면 `bot/kakao_token.json` 파일이 생기는데, 거기서 `"refresh_token"` 값을 복사해서 GitHub Secret `KAKAO_REFRESH_TOKEN`에 넣으세요.

(카카오 refresh_token은 60일 유효하지만 사용 시 자동 연장돼서, 봇이 12시간마다 돌면 거의 영원히 유효해요.)

### 5단계 — 첫 실행

레포 → **Actions** 탭 → "News bot — twice daily" → **Run workflow** → **Run workflow** 클릭.

5~10분 대기 후 결과 확인:
- ✅ Actions 로그에서 "Supabase 저장 완료" 보이는지
- ✅ Supabase **Table Editor** → schema 드롭다운에서 `briefing` 선택 → `briefings` 테이블에 새 row 생겼는지
- ✅ 카카오톡에 메시지 도착했는지

이후로는 매일 KST 08:30 / 20:30 자동 실행됩니다.

### 6단계 — Next.js 사이트 띄우기 (로컬 dev)

```bash
# 루트 폴더에 .env.local 만들기
cat > .env.local <<EOF
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
EOF

npm install
npm run dev
```

→ `http://localhost:3000`에서 진짜 Supabase 데이터로 페이지가 뜸.

### 7단계 — Vercel 배포 (Phase 4)

추후 Phase 4에서 진행. 미리 준비할 것:
- GitHub 레포 → Vercel Import
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 환경변수 등록
- 배포 후 URL을 `SITE_BASE_URL` GitHub Secret에도 업데이트

---

## 🧪 로컬 테스트

### 봇만 한 번 돌려보기 (Supabase 안 건드림)

```bash
cd bot
# Supabase env 제외하고 실행 → Notion + Kakao만 동작
ANTHROPIC_API_KEY=... NOTION_API_KEY=... NOTION_PAGE_ID=... \
KAKAO_REST_API_KEY=... \
python news_bot.py briefing-once
```

### 사이트만 mock 데이터로 띄우기

```bash
# .env.local 비워두면 자동 mock 폴백
npm run dev
```

---

## 💰 월 비용 (실제)

| 항목 | 비용 |
|---|---|
| Vercel (Hobby) | $0 |
| Supabase (Free, 500MB) | $0 |
| GitHub Actions | $0 (월 사용량 ~420분 / 한도 2,000분) |
| Anthropic API (Haiku 4.5, 일 2회 × 4 calls 포함 카드뉴스) | ~$1–4 |
| Unsplash (카드뉴스 5장/회) | $0 (Demo Tier 월 50회 한도, 일 2회 = 월 300건 → 자동 fallback 처리) |
| **합계** | **~$1–4/월** |

> ⚠️ Unsplash Demo Tier는 시간당 50회 제한이 있어요. 봇 1회당 5장 검색 + retry 시 ~10건 호출 → 시간당 한도 안 넘음. 만약 hit해도 `card_news_generator.py`가 placeholder 이미지로 자동 fallback하니 메일은 정상 발송됩니다.

---

## 🆘 트러블슈팅

**Q. Actions 로그에 "Supabase 환경변수 미설정"**
→ Secrets 이름 오타 확인. 특히 `SUPABASE_URL` (NEXT_PUBLIC 접두사 ❌).

**Q. "schema 'briefing' does not exist" 에러**
→ 1단계의 schema.sql 실행이 누락됐거나 다른 프로젝트에 실행됨.

**Q. 카카오톡 메시지 안 옴, "KOE101" 에러**
→ `KAKAO_REST_API_KEY`가 잘못됨. 카카오 디벨로퍼스 → 앱 → 앱 설정 → 앱 키 → REST API 키.

**Q. 사이트에 데이터가 mock 그대로 보임**
→ `NEXT_PUBLIC_SUPABASE_URL` / `ANON_KEY` 둘 다 `.env.local`(로컬) 또는 Vercel(배포)에 있어야 함.

**Q. 카드뉴스 생성 실패 "cardnews/index.html not found"**
→ `bot/cardnews/index.html`이 있는지 확인. 사용자 zip에 포함된 디자인 템플릿 파일이 이 경로에 있어야 함.

**Q. 카드뉴스에 사진 대신 placeholder가 나옴**
→ `UNSPLASH_ACCESS_KEY` 시크릿 누락 또는 시간당 한도 초과. fallback이라 메일은 정상 발송됨. https://unsplash.com/developers 에서 Demo 앱 등록하면 무료 키 발급 가능.
