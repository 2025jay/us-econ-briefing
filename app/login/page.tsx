import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function LoginPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-mobile px-5 py-12 text-center">
        <h1 className="text-xl font-semibold text-ink">로그인</h1>
        <p className="mt-3 text-sm text-muted">
          새 브리핑 알림을 받고 싶으면 로그인하세요.
          <br />
          콘텐츠는 누구나 무료로 볼 수 있어요.
        </p>
        <button
          type="button"
          disabled
          className="mt-6 inline-flex items-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-sm text-muted cursor-not-allowed"
        >
          Google로 로그인 (준비 중)
        </button>
        <p className="mt-8">
          <Link href="/" className="text-xs text-muted hover:text-ink">
            ← 메인으로
          </Link>
        </p>
      </main>
      <Footer />
    </>
  );
}
