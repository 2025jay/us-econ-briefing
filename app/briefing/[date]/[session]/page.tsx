import { notFound } from "next/navigation";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import MarketWidget from "@/components/MarketWidget";
import BriefingBody from "@/components/BriefingBody";
import { getBriefingByDate } from "@/lib/queries";
import { formatDateKor, formatSessionLabel } from "@/lib/format";

type Props = {
  params: { date: string; session: string };
};

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

  return (
    <>
      <Header />

      <main className="mx-auto max-w-mobile px-5 py-5">
        <Link
          href="/"
          className="inline-flex items-center text-xs text-muted hover:text-ink"
        >
          ← 메인
        </Link>

        <div className="mt-3 mb-5">
          <div className="font-mono text-2xs text-subtle">
            {formatDateKor(briefing.session_date)} ·{" "}
            {formatSessionLabel(briefing.session_time)}
          </div>
          <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">
            미국 경제 브리핑
          </h1>
        </div>

        <MarketWidget status={briefing.market_status} />

        <div className="mt-7">
          <BriefingBody briefing={briefing} />
        </div>
      </main>

      <Footer />
    </>
  );
}
