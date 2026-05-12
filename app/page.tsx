import Header from "@/components/Header";
import Footer from "@/components/Footer";
import MarketWidget from "@/components/MarketWidget";
import BriefingCard from "@/components/BriefingCard";
import Link from "next/link";
import { getLatestBriefing, getRecentBriefings } from "@/lib/queries";

export const revalidate = 60; // 60초마다 SSR 캐시 갱신

export default async function HomePage() {
  const [latest, recentAll] = await Promise.all([
    getLatestBriefing(),
    getRecentBriefings(6),
  ]);
  // 첫번째는 메인에 표시되므로 제외
  const recent = recentAll.filter((b) => b.id !== latest.id).slice(0, 5);

  return (
    <>
      <Header />

      <main className="mx-auto max-w-3xl px-5 py-6 sm:py-8">
        {/* 시장 시황 위젯 */}
        <MarketWidget status={latest.market_status} />

        {/* 히어로 카피 */}
        <section className="my-8 text-center sm:my-10">
          <h1 className="font-display text-3xl leading-tight sm:text-4xl">
            오늘 미국장{" "}
            <span className="pen-highlight">핵심만 정리</span>
            <br />
            해봤어요 ☕
          </h1>
          <p className="mt-3 font-handwriting text-base opacity-70 sm:text-lg">
            ✏️ 매일 아침 8시 30분, 저녁 8시 30분 자동 업데이트
          </p>
        </section>

        {/* 오늘의 브리핑 카드 */}
        <BriefingCard briefing={latest} variant="full" />

        {/* 최근 브리핑 가로 스크롤 */}
        <section className="mt-10">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="font-display text-xl">최근 브리핑</h2>
            <Link
              href="/archive"
              className="text-xs font-semibold underline underline-offset-2"
            >
              전체보기 →
            </Link>
          </div>
          <div className="no-scrollbar -mx-5 flex gap-3 overflow-x-auto px-5 pb-2">
            {recent.map((b) => (
              <BriefingCard
                key={b.id}
                briefing={b}
                variant="compact"
              />
            ))}
          </div>
        </section>

        {/* 가벼운 CTA 박스 */}
        <section className="mt-10 rounded-2xl border-3 border-ink bg-accent-blue p-5 shadow-brutal">
          <div className="mb-3 font-display text-lg">
            매일 받아보고 싶다면? 📬
          </div>
          <p className="mb-4 text-sm opacity-90">
            카카오 오픈채팅에 들어오면 아침·저녁 새 브리핑이 올라올 때마다 바로
            받아볼 수 있어요.
          </p>
          <a
            href="https://open.kakao.com/o/s5b27kqi"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block rounded-md border-2 border-ink bg-accent-yellow px-4 py-2 text-sm font-bold shadow-brutal-sm"
          >
            💬 오픈채팅 들어가기
          </a>
        </section>
      </main>

      <Footer />
    </>
  );
}
