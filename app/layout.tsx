import type { Metadata } from "next";
import { Jua, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// next/font/google는 빌드 시점에 폰트를 다운로드합니다.
// Single Day는 Vercel 빌드 환경에서 가끔 fonts.gstatic.com 차단/타임아웃이 나서
// globals.css 의 <link>로 클라이언트에서 로드 (--font-single-day 변수만 노출).

const jua = Jua({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-jua",
  display: "swap",
  preload: false,         // 빌드 시 폰트 차단 회피
  adjustFontFallback: false,
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  preload: false,
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "미국 경제 AI 브리핑 ☕",
  description:
    "매일 아침 8시 30분, 저녁 8시 30분 자동 업데이트되는 미국 경제 브리핑",
  openGraph: {
    title: "미국 경제 AI 브리핑 ☕",
    description: "오늘 미국장 핵심만 정리해봤어요",
    type: "website",
    locale: "ko_KR",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="ko"
      className={`${jua.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen bg-paper bg-grid text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
