export default function Footer() {
  return (
    <footer className="mt-16 border-t-3 border-ink bg-paper">
      <div className="mx-auto max-w-3xl px-5 py-8 text-center text-sm">
        <p className="mb-3 font-display text-base">
          매일 아침 8:30 · 저녁 8:30 자동 업데이트
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <a
            href="https://open.kakao.com/o/s5b27kqi"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border-2 border-ink bg-accent-yellow px-3 py-1.5 text-xs font-semibold shadow-brutal-sm"
          >
            💬 카카오 오픈채팅
          </a>
          <a
            href="#"
            className="rounded-md border-2 border-ink bg-accent-pink px-3 py-1.5 text-xs font-semibold text-white shadow-brutal-sm"
          >
            📷 인스타그램
          </a>
        </div>
        <p className="mt-6 text-xs opacity-50">
          ⓘ 본 브리핑은 AI가 주요 외신 보도를 종합·요약한 것으로 투자 판단의
          근거가 될 수 없습니다.
        </p>
      </div>
    </footer>
  );
}
