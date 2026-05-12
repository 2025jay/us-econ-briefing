import type { Metadata, Viewport } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

// 영문/숫자만 mono. 한국어 본문은 globals.css의 Pretendard.
const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  preload: false,
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "미국 경제 AI 브리핑",
  description:
    "매일 한국시간 오전 8:30, 오후 8:30에 자동 게시되는 미국 경제 브리핑",
  openGraph: {
    title: "미국 경제 AI 브리핑",
    description: "오늘 미국장 핵심 정리",
    type: "website",
    locale: "ko_KR",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1, // 모바일에서 핀치 줌으로 깨지는 거 방지
  themeColor: "#fafafa",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={jetbrains.variable}>
      <body className="min-h-screen bg-bg text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
