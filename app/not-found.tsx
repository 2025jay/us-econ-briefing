import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function NotFound() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-mobile px-5 py-16 text-center">
        <p className="font-mono text-2xs text-subtle">404</p>
        <h1 className="mt-2 text-xl font-semibold text-ink">
          페이지를 찾을 수 없어요
        </h1>
        <p className="mt-3 text-sm text-muted">
          요청하신 브리핑이 아직 생성되지 않았거나
          <br />
          주소가 잘못되었을 수 있어요.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-accent text-bg px-4 py-2 text-sm font-medium"
        >
          메인으로
        </Link>
      </main>
      <Footer />
    </>
  );
}
