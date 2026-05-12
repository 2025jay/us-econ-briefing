import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function NotFound() {
  return (
    <>
      <Header />
      <main className="mx-auto flex max-w-md flex-col items-center px-5 py-16 text-center">
        <div className="rounded-2xl border-3 border-ink bg-accent-pink p-8 shadow-brutal-lg">
          <h1 className="font-display text-4xl text-white">404</h1>
          <p className="mt-2 font-display text-lg text-white">
            찾으시는 브리핑이 없어요 😢
          </p>
        </div>
        <Link
          href="/"
          className="mt-6 rounded-md border-2 border-ink bg-accent-yellow px-4 py-2 font-bold shadow-brutal-sm"
        >
          메인으로 돌아가기
        </Link>
      </main>
      <Footer />
    </>
  );
}
