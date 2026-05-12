import Link from "next/link";
import { Briefing } from "@/lib/types";
import { formatDateKor, formatSessionLabel } from "@/lib/format";

type Props = {
  briefing: Briefing;
  variant?: "full" | "compact";
};

export default function BriefingCard({ briefing, variant = "full" }: Props) {
  const href = `/briefing/${briefing.session_date}/${briefing.session_time}`;
  const sessionEmoji = briefing.session_time === "morning" ? "🌅" : "🌙";

  if (variant === "compact") {
    return (
      <Link
        href={href}
        className="block min-w-[200px] rounded-xl border-2 border-ink bg-white p-3 shadow-brutal-sm transition-transform hover:-translate-y-0.5"
      >
        <div className="mb-1 font-mono text-xs opacity-60">
          {formatDateKor(briefing.session_date)}
        </div>
        <div className="font-display text-sm">
          {sessionEmoji} {formatSessionLabel(briefing.session_time)}
        </div>
        <div className="mt-2 line-clamp-2 text-xs opacity-80">
          {briefing.items[0]?.title}
        </div>
      </Link>
    );
  }

  return (
    <article className="rounded-2xl border-3 border-ink bg-accent-yellow p-5 shadow-brutal-lg sm:p-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <div className="font-mono text-xs opacity-70">
            {formatDateKor(briefing.session_date)}
          </div>
          <div className="font-display text-lg">
            {sessionEmoji} {formatSessionLabel(briefing.session_time)} 도착
          </div>
        </div>
        <span className="rounded-full border-2 border-ink bg-white px-2 py-0.5 font-mono text-[10px] font-bold">
          {briefing.session_time === "morning" ? "MORNING" : "EVENING"}
        </span>
      </header>

      {briefing.briefing_intro && (
        <p className="mb-4 text-sm leading-relaxed opacity-90">
          {briefing.briefing_intro}
        </p>
      )}

      <ol className="space-y-2.5">
        {briefing.items.map((item, i) => (
          <li
            key={i}
            className="flex gap-2.5 rounded-lg border-2 border-ink bg-white px-3 py-2"
          >
            <span className="font-mono text-sm font-bold opacity-50">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="text-sm font-medium leading-snug">
              {item.title}
            </span>
          </li>
        ))}
      </ol>

      <div className="mt-5 flex justify-end">
        <Link
          href={href}
          className="rounded-md border-2 border-ink bg-ink px-4 py-2 text-sm font-semibold text-paper shadow-brutal-sm transition-transform hover:-translate-y-0.5"
        >
          자세히 보기 →
        </Link>
      </div>
    </article>
  );
}
