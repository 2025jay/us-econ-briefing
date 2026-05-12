import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function LoginPage() {
  return (
    <>
      <Header />

      <main className="mx-auto flex max-w-md flex-col items-center px-5 py-12">
        <div className="w-full rounded-2xl border-3 border-ink bg-white p-8 shadow-brutal-lg">
          <h1 className="text-center font-display text-2xl">
            👋 환영해요
          </h1>
          <p className="mt-2 text-center text-sm opacity-70">
            로그인하면 새 브리핑이 도착할 때 알림을 받을 수 있어요.
            <br />
            (콘텐츠는 누구나 무료로 볼 수 있어요)
          </p>

          <button
            type="button"
            disabled
            className="mt-6 flex w-full items-center justify-center gap-3 rounded-md border-2 border-ink bg-white px-4 py-3 font-semibold shadow-brutal-sm transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="text-lg">🔑</span>
            <span>Google로 로그인 (Phase 3 예정)</span>
          </button>

          <p className="mt-6 text-center text-xs opacity-50">
            NextAuth + Google OAuth는 Phase 3에서 연결됩니다.
          </p>

          <div className="mt-6 text-center">
            <Link
              href="/"
              className="text-sm font-semibold underline underline-offset-2"
            >
              ← 메인으로 돌아가기
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
}
