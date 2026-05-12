import Header from "@/components/Header";
import Footer from "@/components/Footer";
import BriefingCard from "@/components/BriefingCard";
import { getAllBriefings } from "@/lib/queries";
import { Briefing } from "@/lib/types";

export const revalidate = 60;

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

      <main className="mx-auto max-w-mobile px-5 py-5">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          아카이브
        </h1>
        <p className="mt-1.5 text-sm text-muted">
          지난 브리핑 모음
        </p>

        {months.map((ym) => (
          <section key={ym} className="mt-8">
            <h2 className="mb-3 text-xs font-semibold text-muted uppercase tracking-wide">
              {formatMonth(ym)}
            </h2>
            <div className="space-y-2">
              {groups[ym].map((b) => (
                <BriefingCard key={b.id} briefing={b} variant="compact" />
              ))}
            </div>
          </section>
        ))}

        {months.length === 0 && (
          <div className="mt-10 rounded-lg border border-line bg-surface p-10 text-center">
            <p className="text-sm text-muted">아직 아카이브가 비어있어요.</p>
          </div>
        )}
      </main>

      <Footer />
    </>
  );
}
