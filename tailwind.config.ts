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
        // 베이지 페이퍼 배경 (메인 톤)
        paper: "#FAF3E0",
        ink: "#1A1A1A",
        // 카드 액센트 5색 (순환 사용)
        accent: {
          pink: "#ED4983",
          lime: "#C8E853",
          yellow: "#F8D742",
          purple: "#C8B4F0",
          blue: "#A8C9E8",
        },
        // 하이라이트 (손글씨 강조, 형광펜 효과)
        highlight: {
          yellow: "#FFFC4F",
          pink: "#FF4FA3",
        },
      },
      fontFamily: {
        sans: ["var(--font-pretendard)", "system-ui", "sans-serif"],
        display: ["var(--font-jua)", "var(--font-pretendard)", "sans-serif"],
        handwriting: ["var(--font-single-day)", "cursive"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        // 네오브루탈리스트 두꺼운 드롭섀도우
        brutal: "4px 4px 0 0 #1A1A1A",
        "brutal-lg": "6px 6px 0 0 #1A1A1A",
        "brutal-sm": "2px 2px 0 0 #1A1A1A",
      },
      borderWidth: {
        "3": "3px",
      },
      backgroundImage: {
        // 베이지 위 미세한 그리드 패턴
        grid: "linear-gradient(rgba(26,26,26,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(26,26,26,0.04) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "24px 24px",
      },
    },
  },
  plugins: [],
};

export default config;
