import Link from "next/link";
import { auth } from "@/auth";

export default async function Header() {
  const session = await auth();

  return (
    <header className="border-b border-line bg-bg/80 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-mobile px-5 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1.5">
          <span className="text-base font-semibold tracking-tight">
            US Econ Brief
          </span>
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/archive"
            className="text-xs text-muted hover:text-ink transition-colors"
          >
            아카이브
          </Link>
          {session?.user ? (
            <Link href="/login" className="flex items-center gap-1.5">
              {session.user.image && (
                <img
                  src={session.user.image}
                  alt=""
                  className="h-6 w-6 rounded-full border border-line"
                />
              )}
              <span className="text-xs text-muted hover:text-ink">
                {session.user.name?.slice(0, 8) ?? "사용자"}
              </span>
            </Link>
          ) : (
            <Link
              href="/login"
              className="text-xs text-muted hover:text-ink transition-colors"
            >
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
