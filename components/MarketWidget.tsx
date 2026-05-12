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
      className="rounded-xl border border-line bg-surface p-4"
    >
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-xs font-semibold text-muted uppercase tracking-wide">
          미국장 마감
        </h2>
        <span className="font-mono text-2xs text-subtle">
          {status.as_of ?? "—"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-1">
        {TICKERS.map(({ key, name }) => {
          const t = status[key];
          const isUp = t.change_pct >= 0;
          return (
            <div key={key} className="text-center px-1">
              <div className="text-2xs font-medium text-muted">{name}</div>
              <div className="mt-1 font-mono text-base font-semibold text-ink">
                {formatNumber(t.value)}
              </div>
              <div
                className={`mt-0.5 font-mono text-xs font-medium ${
                  isUp ? "text-gain" : "text-loss"
                }`}
              >
                {isUp ? "▲" : "▼"} {formatChangePct(t.change_pct).replace("+", "")}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
