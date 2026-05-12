export default function Footer() {
  return (
    <footer className="mt-12 border-t border-line">
      <div className="mx-auto max-w-mobile px-5 py-6 text-center">
        <p className="text-xs text-muted">
          매일 한국시간 08:30 · 20:30 자동 업데이트
        </p>
        <p className="mt-3 text-2xs text-subtle">
          본 브리핑은 AI가 주요 외신 보도를 종합·요약한 것으로
          <br />
          투자 판단의 근거가 될 수 없습니다.
        </p>
      </div>
    </footer>
  );
}
