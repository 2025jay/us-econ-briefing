import Header from "@/components/Header";
import Footer from "@/components/Footer";
import BriefingCard from "@/components/BriefingCard";
import { getAllBriefings } from "@/lib/queries";
import { Briefing } from "@/lib/types";

export const revalidate = 60;

// 월별 그룹화 ("2026-05" → Briefing[])
function groupByMonth(items: Briefing[]): Record<string, Briefing[]> {
  return items.reduce(
    (acc, b) => {
      const ym = b.session_date.slice(0, 7);
      (acc[ym] ??= []).push(b);
      return acc;
    },
    {} as Record<string, Briefing[]>
  );
}

function formatMonth(ym: string): string {
  const [y, m] = ym.split("-");
  return `${y}년 ${parseInt(m, 10)}월`;
}

export default async function ArchivePage() {
  const all = await getAllBriefings();
  const groups = groupByMonth(all);
  const months = Object.keys(groups).sort().reverse();

  return (
    <>
      <Header />

      <main className="mx-auto max-w-3xl px-5 py-6 sm:py-8">
        <h1 className="font-display text-3xl">📚 아카이브</h1>
        <p className="mt-2 text-sm opacity-70">
          지난 미국 경제 브리핑을 한 번에 모아봤어요.
        </p>

        {months.map((ym) => (
          <section key={ym} className="mt-8">
            <h2 className="mb-3 inline-block rounded-md border-2 border-ink bg-accent-yellow px-3 py-1 font-display text-lg shadow-brutal-sm">
              {formatMonth(ym)}
            </h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {groups[ym].map((b) => (
                <BriefingCard key={b.id} briefing={b} variant="compact" />
              ))}
            </div>
          </section>
        ))}

        {months.length === 0 && (
          <div className="mt-10 rounded-2xl border-3 border-ink bg-white p-10 text-center shadow-brutal">
            <p className="font-display text-lg">아직 아카이브가 비어있어요.</p>
            <p className="mt-2 text-sm opacity-60">
              곧 첫 브리핑이 도착할 거예요!
            </p>
          </div>
        )}
      </main>

      <Footer />
    </>
  );
}
