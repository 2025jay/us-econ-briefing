import Link from "next/link";
import { Briefing } from "@/lib/types";
import { formatDateKor, formatSessionLabel } from "@/lib/format";

type Props = {
  briefing: Briefing;
  variant?: "full" | "compact";
};

/**
 * compact: 아카이브/최근 슬라이더용 가벼운 카드
 * full: 메인 페이지에서 오늘의 브리핑 미리보기 (현재 미사용 — 메인 페이지가 본문 직접 렌더)
 */
export default function BriefingCard({ briefing, variant = "compact" }: Props) {
  const href = `/briefing/${briefing.session_date}/${briefing.session_time}`;

  return (
    <Link
      href={href}
      className="block rounded-lg border border-line bg-surface p-4 transition-colors hover:border-ink/30"
    >
      <div className="flex items-baseline justify-between gap-2 mb-2">
        <span className="font-mono text-2xs text-subtle">
          {formatDateKor(briefing.session_date)}
        </span>
        <span className="text-2xs text-muted">
          {formatSessionLabel(briefing.session_time)}
        </span>
      </div>
      <div className="text-sm font-medium text-ink line-clamp-2">
        {briefing.items[0]?.title ?? briefing.briefing_intro.slice(0, 60)}
      </div>
      <div className="mt-2 text-2xs text-subtle">
        {briefing.items.length}개 항목
      </div>
    </Link>
  );
}
