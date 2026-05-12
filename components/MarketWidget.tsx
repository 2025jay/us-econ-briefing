import { MarketStatus } from "@/lib/types";
import { formatNumber, formatChangePct } from "@/lib/format";

type Props = {
  status: MarketStatus;
};

const TICKERS = [
  { key: "sp500" as const, name: "S&P 500" },
  { key: "nasdaq" as const, name: "NASDAQ" },
  { key: "dow" as const, name: "DOW" },
];

export default function MarketWidget({ status }: Props) {
  return (
    <section
      aria-label="미국 시장 시황"
      className="rounded-2xl border-3 border-ink bg-white p-5 shadow-brutal"
    >
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="font-display text-xl">📊 미국장 마감</h2>
        <span className="font-mono text-xs opacity-60">
          {status.as_of ?? "—"} ET
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        {TICKERS.map(({ key, name }) => {
          const t = status[key];
          const isUp = t.change_pct >= 0;
          return (
            <div
              key={key}
              className={`rounded-xl border-2 border-ink p-3 ${
                isUp ? "bg-accent-lime" : "bg-accent-pink"
              }`}
            >
              <div className="text-xs font-semibold opacity-70">{name}</div>
              <div className="mt-1 font-mono text-base font-bold sm:text-lg">
                {formatNumber(t.value)}
              </div>
              <div
                className={`mt-0.5 font-mono text-xs font-bold ${
                  isUp ? "text-green-900" : "text-red-900"
                }`}
              >
                {isUp ? "▲" : "▼"} {formatChangePct(t.change_pct)}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
