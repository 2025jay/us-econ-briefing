// Phase 1 정적 모킹용 샘플 데이터.
// Phase 2에서 Supabase 쿼리로 교체됨.

import { Briefing } from "./types";

export const mockBriefings: Briefing[] = [
  {
    id: "mock-1",
    session_date: "2026-05-12",
    session_time: "morning",
    market_status: {
      sp500: { value: 5234.18, change: 21.92, change_pct: 0.42 },
      nasdaq: { value: 16789.34, change: 102.15, change_pct: 0.61 },
      dow: { value: 38492.07, change: -57.84, change_pct: -0.15 },
      as_of: "05.11 마감",
    },
    briefing_intro:
      "오늘은 중동 정세와 빅테크 AI 칩 협업이 미국장의 톤을 결정했어요. 시장은 위 아래로 출렁였지만 결국 대형 기술주가 지수를 끌어올렸습니다.",
    items: [
      {
        title: "호르무즈 해협 통항 일시 중단",
        body: "이란 혁명수비대가 호르무즈 해협 일대에서 군사 훈련을 강행하면서 일부 유조선의 통항이 6시간가량 중단됐어요. WTI 유가는 장중 한때 3.2% 급등했다가 휴전 가능성이 거론되며 1%대 상승으로 마감했습니다. 미국 정부는 5함대 자산을 추가 전개했다고 밝혔어요. 시장은 단기 변동성으로 받아들이는 분위기예요.",
        source: "주요 외신",
      },
      {
        title: "트럼프, 이란에 휴전 위반 시 추가 제재 경고",
        body: "트럼프 대통령이 이란을 향해 \"휴전 조항을 한 번이라도 더 어기면 전면적인 추가 제재를 가하겠다\"고 공개 경고했어요. 백악관은 동시에 사우디·UAE와 협의해 비축유 방출 가능성도 검토 중이라고 전했습니다. 채권시장은 안전자산 선호로 10년물 금리가 4bp 하락했어요.",
        source: "주요 외신",
      },
      {
        title: "FED 신임 의장 후보 청문회 D-1",
        body: "내일 상원 청문회를 앞둔 FED 신임 의장 후보가 \"인플레이션 둔화가 확인되기 전까지 금리 인하는 신중해야 한다\"는 입장을 청문회 사전 답변서에 담았어요. 시장이 기대했던 9월 인하 가능성은 다소 후퇴했지만, 빅테크 강세가 이를 상쇄했습니다. 12월 인하 확률은 64%로 유지됐어요.",
        source: "주요 외신",
      },
      {
        title: "구글·마블, 차세대 AI 추론 칩 공동 개발",
        body: "구글이 마블 테크놀로지와 손잡고 데이터센터용 AI 추론 칩을 공동 개발한다고 발표했어요. 첫 양산은 2027년 1분기 목표이고, 엔비디아 H100 대비 와트당 추론 성능을 1.7배 끌어올리는 게 핵심이에요. 마블 주가는 시간외 9.8% 급등, 엔비디아는 1.2% 하락했습니다.",
        source: "주요 외신",
      },
      {
        title: "FT, '새 밸류에이션 키워드: 토큰 단가' 분석",
        body: "FT가 빅테크 밸류에이션을 PER 대신 \"토큰 1조 개당 매출\"이라는 신지표로 재해석하는 칼럼을 실었어요. 마이크로소프트와 오픈AI의 토큰 단가가 18개월 만에 절반 이하로 떨어졌다는 데이터를 함께 공개했고, 일부 헤지펀드들이 이 지표를 이미 내부 모델에 반영하고 있다고 소개했어요. 클라우드 매출의 질적 분석에 새 기준이 생긴 셈이에요.",
        source: "주요 외신",
      },
    ],
    generated_at: "2026-05-12T08:30:00+09:00",
  },
  {
    id: "mock-2",
    session_date: "2026-05-11",
    session_time: "evening",
    market_status: {
      sp500: { value: 5212.26, change: 8.71, change_pct: 0.17 },
      nasdaq: { value: 16687.19, change: -22.43, change_pct: -0.13 },
      dow: { value: 38549.91, change: 41.32, change_pct: 0.11 },
      as_of: "05.10 마감",
    },
    briefing_intro:
      "주말 전 마지막 거래일은 큰 변동 없이 보합권에서 마감됐어요. 다음 주 CPI 발표 대기 모드입니다.",
    items: [
      {
        title: "CPI 발표 D-3, 시장 컨센서스 3.1%",
        body: "다음 주 화요일 발표되는 4월 CPI는 전년 대비 3.1% 상승이 컨센서스예요. 근원 CPI는 3.4%로 예상되고, 이 수치가 부합하면 9월 FED 인하 시나리오가 다시 부상할 전망이에요.",
        source: "주요 외신",
      },
      {
        title: "엔비디아, 차세대 GPU 'B200' 출하 시작",
        body: "엔비디아가 호퍼 후속 블랙웰 아키텍처 첫 양산품 B200을 주요 클라우드 고객사에 출하하기 시작했어요. 메타·MS·AWS가 첫 물량을 받았고, 단가는 H100의 약 1.6배예요.",
        source: "주요 외신",
      },
      {
        title: "보잉, 737 MAX 추가 안전 점검 결정",
        body: "FAA가 보잉 737 MAX 전 기종에 대한 추가 안전 점검을 명령했어요. 영향 받는 항공기는 약 1,200대이며, 점검 기간 일부 노선이 단축 운항될 가능성이 있어요.",
        source: "주요 외신",
      },
      {
        title: "테슬라 사이버트럭, 누적 인도 5만대 돌파",
        body: "테슬라 사이버트럭이 출시 18개월 만에 누적 인도 5만대를 돌파했어요. 다만 머스크가 예고했던 연 25만대 캐파 달성은 2027년으로 미뤄질 가능성이 커졌어요.",
        source: "주요 외신",
      },
      {
        title: "WSJ, '한국 반도체 수출 회복세' 특집",
        body: "WSJ이 한국의 4월 반도체 수출이 전년 대비 56% 증가한 점을 분석하며, AI 수요 사이클의 글로벌 수혜자 1순위로 SK하이닉스를 꼽았어요. HBM3E 출하 본격화가 키 팩터예요.",
        source: "주요 외신",
      },
    ],
    generated_at: "2026-05-11T20:30:00+09:00",
  },
  {
    id: "mock-3",
    session_date: "2026-05-11",
    session_time: "morning",
    market_status: {
      sp500: { value: 5203.55, change: 35.21, change_pct: 0.68 },
      nasdaq: { value: 16709.62, change: 158.04, change_pct: 0.96 },
      dow: { value: 38508.59, change: 84.12, change_pct: 0.22 },
      as_of: "05.08 마감",
    },
    briefing_intro: "AI 빅테크 실적 호조로 나스닥이 사흘 만에 반등했어요.",
    items: [
      {
        title: "MS 분기 실적 어닝 서프라이즈",
        body: "마이크로소프트가 분기 매출 컨센서스 대비 4.2% 상회한 실적을 발표했어요. Azure 부문이 전년 대비 31% 성장하며 클라우드 수요 강세를 다시 한번 확인시켰어요.",
        source: "주요 외신",
      },
      {
        title: "메타, AI 글래스 신제품 발표 예고",
        body: "메타가 다음 주 라스베이거스에서 차세대 AI 글래스를 공개한다고 예고했어요. 레이밴 협업 후속 모델로 추정되며, 가격대는 $499 선이 유력해요.",
        source: "주요 외신",
      },
      {
        title: "OPEC+ 감산 연장 합의",
        body: "OPEC+가 일일 220만 배럴 자발적 감산을 3분기까지 연장하기로 합의했어요. 유가는 발표 직후 1.4% 상승했어요.",
        source: "주요 외신",
      },
      {
        title: "美 4월 비농업고용 19.2만 명",
        body: "4월 비농업고용이 19.2만 명 증가해 컨센서스(17.5만)를 상회했지만, 임금 상승률은 0.2% MoM으로 둔화되며 시장은 \"긍정적인 골디락스\"로 해석했어요.",
        source: "주요 외신",
      },
      {
        title: "TSMC, 애리조나 3공장 양산 일정 발표",
        body: "TSMC가 애리조나 3공장 양산 일정을 2027년 1분기로 공식 확정했어요. 2nm 공정 기반이며, 애플과 엔비디아가 1차 고객사로 거론돼요.",
        source: "주요 외신",
      },
    ],
    generated_at: "2026-05-11T08:30:00+09:00",
  },
];

// 최신 브리핑 가져오기
export function getLatestBriefing(): Briefing {
  return mockBriefings[0];
}

// 특정 날짜/세션 브리핑 가져오기
export function getBriefingByDate(
  date: string,
  session: "morning" | "evening"
): Briefing | null {
  return (
    mockBriefings.find(
      (b) => b.session_date === date && b.session_time === session
    ) ?? null
  );
}

// 최근 N개
export function getRecentBriefings(n = 6): Briefing[] {
  return mockBriefings.slice(0, n);
}
