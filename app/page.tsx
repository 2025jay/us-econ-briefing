import Header from "@/components/Header";
import Footer from "@/components/Footer";
import MarketWidget from "@/components/MarketWidget";
import BriefingBody from "@/components/BriefingBody";
import BriefingCard from "@/components/BriefingCard";
import Link from "next/link";
import { getLatestBriefing, getRecentBriefings } from "@/lib/queries";
import { formatDateKor, formatSessionLabel } from "@/lib/format";

export const revalidate = 60;

export default async function HomePage() {
  const [latest, recentAll] = await Promise.all([
    getLatestBriefing(),
    getRecentBriefings(8),
  ]);
  const recent = recentAll.filter((b) => b.id !== latest.id).slice(0, 6);

  return (
    <>
      <Header />

      <main className="mx-auto max-w-mobile px-5 py-5">
        {/* 페이지 헤더 — 날짜·세션 */}
        <div className="mb-5">
          <div className="font-mono text-2xs text-subtle">
            {formatDateKor(latest.session_date)} ·{" "}
            {formatSessionLabel(latest.session_time)}
          </div>
          <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">
            오늘의 미국 경제 브리핑
          </h1>
        </div>

        {/* 시장 시황 */}
        <MarketWidget status={latest.market_status} />

        {/* 본문 — 모든 뉴스 풀 콘텐츠 */}
        <div className="mt-7">
          <BriefingBody briefing={latest} />
        </div>

        {/* 최근 브리핑 (아카이브 미리보기) */}
        {recent.length > 0 && (
          <section className="mt-10">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-ink">최근 브리핑</h2>
              <Link
                href="/archive"
                className="text-xs text-muted hover:text-ink"
              >
                전체 →
              </Link>
            </div>
            <div className="space-y-2">
              {recent.map((b) => (
                <BriefingCard key={b.id} briefing={b} variant="compact" />
              ))}
            </div>
          </section>
        )}
      </main>

      <Footer />
    </>
  );
}
