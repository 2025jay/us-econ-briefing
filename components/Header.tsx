import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-line bg-bg/80 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-mobile px-5 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1.5">
          <span className="text-base font-semibold tracking-tight">
            US Econ Brief
          </span>
        </Link>
        <Link
          href="/archive"
          className="text-xs text-muted hover:text-ink transition-colors"
        >
          아카이브
        </Link>
      </div>
    </header>
  );
}
