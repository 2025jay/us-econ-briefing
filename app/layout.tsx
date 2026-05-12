import type { Metadata } from "next";
import { Jua, Single_Day, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Google Fonts (Pretendard는 globals.css에서 CDN 로드)
const jua = Jua({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-jua",
  display: "swap",
});

const singleDay = Single_Day({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-single-day",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
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
      className={`${jua.variable} ${singleDay.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen bg-paper bg-grid text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
