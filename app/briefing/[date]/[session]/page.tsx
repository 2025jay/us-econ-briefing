import { notFound } from "next/navigation";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import MarketWidget from "@/components/MarketWidget";
import ShareButton from "@/components/ShareButton";
import { getBriefingByDate } from "@/lib/queries";
import {
  formatDateKor,
  formatSessionLabel,
  accentByIndex,
} from "@/lib/format";

type Props = {
  params: { date: string; session: string };
};

// 동적 라우트 — 모든 날짜/세션 조합을 SSR로 렌더 (generateStaticParams 제거)
export const revalidate = 60;
export const dynamicParams = true;

export default async function BriefingDetailPage({ params }: Props) {
  if (params.session !== "morning" && params.session !== "evening") {
    notFound();
  }
  const briefing = await getBriefingByDate(
    params.date,
    params.session as "morning" | "evening"
  );
  if (!briefing) notFound();

  const sessionEmoji = briefing.session_time === "morning" ? "🌅" : "🌙";

  return (
    <>
      <Header />

      <main className="mx-auto max-w-3xl px-5 py-6 sm:py-8">
        <Link
          href="/"
          className="mb-5 inline-flex items-center gap-1 text-sm font-semibold underline underline-offset-2"
        >
          ← 메인으로
        </Link>

        {/* 헤더 */}
        <div className="mb-6">
          <div className="font-mono text-sm opacity-70">
            {formatDateKor(briefing.session_date)} · {sessionEmoji}{" "}
            {formatSessionLabel(briefing.session_time)} KST
          </div>
          <h1 className="mt-2 font-display text-2xl leading-tight sm:text-3xl">
            오늘의 미국 경제 브리핑
          </h1>
          {briefing.briefing_intro && (
            <p className="mt-3 text-base leading-relaxed opacity-90">
              {briefing.briefing_intro}
            </p>
          )}
        </div>

        {/* 시장 시황 */}
        <MarketWidget status={briefing.market_status} />

        {/* 5개 핵심 이슈 */}
        <section className="mt-8 space-y-5">
          {briefing.items.map((item, i) => (
            <article
              key={i}
              className={`rounded-2xl border-3 border-ink p-5 shadow-brutal ${accentByIndex(
                i
              )}`}
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="rounded-md border-2 border-ink bg-white px-2 py-0.5 font-mono text-xs font-bold">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="rounded-full border-2 border-ink bg-paper px-2 py-0.5 text-[10px] font-semibold">
                  {item.source}
                </span>
              </div>
              <h2 className="font-display text-xl leading-snug">
                {item.title}
              </h2>
              <p className="mt-3 text-sm leading-relaxed sm:text-[15px]">
                {item.body}
              </p>
            </article>
          ))}
        </section>

        {/* 공유 액션 */}
        <section className="mt-10 rounded-2xl border-3 border-ink bg-white p-5 shadow-brutal">
          <div className="mb-3 font-display text-lg">
            이 브리핑이 도움됐다면 📬
          </div>
          <div className="flex flex-wrap gap-2">
            <a
              href="https://open.kakao.com/o/s5b27kqi"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md border-2 border-ink bg-accent-yellow px-3 py-2 text-sm font-bold shadow-brutal-sm"
            >
              💬 카톡으로 받기
            </a>
            <ShareButton title={`미국 경제 브리핑 — ${briefing.session_date}`} />
          </div>
        </section>

        <p className="mt-6 text-center text-xs opacity-50">
          ⓘ 본 브리핑은 AI가 주요 외신 보도를 종합·요약한 것으로 투자 판단의
          근거가 될 수 없습니다.
        </p>
      </main>

      <Footer />
    </>
  );
}
