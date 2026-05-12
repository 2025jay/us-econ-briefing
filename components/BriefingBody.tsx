/**
 * 브리핑 본문 — 모든 article 항목을 풀 콘텐츠로 렌더.
 * 메인 페이지와 상세 페이지에서 공통 사용.
 */

import { Briefing } from "@/lib/types";

type Props = {
  briefing: Briefing;
};

export default function BriefingBody({ briefing }: Props) {
  return (
    <article className="space-y-6">
      {/* 인트로 (시장 시황 및 분위기) */}
      {briefing.briefing_intro && (
        <div className="text-[15px] leading-relaxed text-ink/90 whitespace-pre-line">
          {briefing.briefing_intro}
        </div>
      )}

      {/* 모든 뉴스 항목 — 번호 + 제목 + 본문 */}
      <ol className="space-y-7">
        {briefing.items.map((item, i) => (
          <li key={i} className="border-t border-line pt-5 first:border-t-0 first:pt-0">
            <div className="flex items-start gap-3">
              <span className="font-mono text-2xs text-subtle mt-1.5 shrink-0 w-5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-semibold text-ink leading-snug">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-ink/80 whitespace-pre-line">
                  {item.body}
                </p>
                {item.source && (
                  <p className="mt-2 text-2xs text-subtle">{item.source}</p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>

      {/* 노션 전체 보기 링크 */}
      {briefing.notion_url && (
        <div className="pt-4 border-t border-line">
          <a
            href={briefing.notion_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-accent text-bg px-4 py-2.5 text-sm font-medium hover:bg-ink/90 transition-colors"
          >
            노션에서 전체 보기
            <span className="text-xs">↗</span>
          </a>
        </div>
      )}
    </article>
  );
}
