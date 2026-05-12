import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b-3 border-ink bg-paper">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="rounded-md border-2 border-ink bg-accent-yellow px-2 py-1 font-display text-lg leading-none shadow-brutal-sm">
            ☕
          </span>
          <span className="font-display text-xl leading-none">
            오늘 미국장
          </span>
        </Link>

        <Link
          href="/login"
          className="rounded-md border-2 border-ink bg-white px-3 py-1.5 text-sm font-semibold shadow-brutal-sm transition-transform hover:-translate-y-0.5"
        >
          Google 로그인
        </Link>
      </div>
    </header>
  );
}
