import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 모던 미니멀 — neutral 베이스 + 단일 액센트
        bg: "#fafafa",          // 페이지 배경 (거의 흰색, 살짝 그레이)
        surface: "#ffffff",     // 카드/위젯 배경
        ink: "#0a0a0a",         // 본문 텍스트
        muted: "#737373",       // 보조 텍스트
        subtle: "#a3a3a3",      // 메타데이터 (시간, 출처)
        line: "#e5e5e5",        // 경계선
        // 상승/하락 (시장 시황 전용)
        gain: "#16a34a",        // 초록
        loss: "#dc2626",        // 빨강
        // 액센트 (CTA 버튼만)
        accent: "#171717",      // 검정 (CTA)
      },
      fontFamily: {
        sans: ["var(--font-pretendard)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      fontSize: {
        // 모바일 우선. iPhone 13 (390px)에서 잘 읽히게 조정.
        "2xs": ["10px", { lineHeight: "1.4" }],
        xs: ["11px", { lineHeight: "1.5" }],
        sm: ["13px", { lineHeight: "1.55" }],
        base: ["15px", { lineHeight: "1.6" }],
        lg: ["17px", { lineHeight: "1.55" }],
        xl: ["19px", { lineHeight: "1.4" }],
        "2xl": ["22px", { lineHeight: "1.35" }],
        "3xl": ["27px", { lineHeight: "1.25" }],
      },
      maxWidth: {
        // iPhone 13 = 390px. max-w를 그 살짝 위로 잡아서 좀 큰 폰에선
        // 좌우 여백 자연스럽게, 작은 폰에서 깨지지 않게.
        mobile: "440px",
      },
    },
  },
  plugins: [],
};

export default config;
