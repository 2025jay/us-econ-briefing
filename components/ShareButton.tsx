"use client";

type Props = {
  title: string;
};

export default function ShareButton({ title }: Props) {
  async function handleShare() {
    const url = typeof window !== "undefined" ? window.location.href : "";
    if (navigator.share) {
      try {
        await navigator.share({ title, url });
      } catch {
        /* 사용자가 취소한 경우 무시 */
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        alert(`링크가 복사되었습니다!\n${url}`);
      } catch {
        window.prompt("아래 링크를 복사하세요:", url);
      }
    }
  }

  return (
    <button
      type="button"
      onClick={handleShare}
      className="rounded-md border-2 border-ink bg-accent-pink px-3 py-2 text-sm font-bold text-white shadow-brutal-sm transition-transform hover:-translate-y-0.5"
    >
      🔗 공유하기
    </button>
  );
}
