/**
 * 비로그인 사용자에게 보여주는 로그인 안내 화면.
 * 메인/상세/아카이브 페이지에서 session 없으면 이 컴포넌트 리턴.
 */

import Header from "./Header";
import Footer from "./Footer";
import { signIn } from "@/auth";

export default function LoginGate() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-mobile px-5 py-16 text-center">
        <div className="inline-block rounded-full border border-line bg-surface px-3 py-1 text-2xs font-medium text-muted uppercase tracking-wide">
          Members Only
        </div>
        <h1 className="mt-5 text-2xl font-semibold tracking-tight text-ink">
          오늘 미국장 핵심,
          <br />
          무료로 받아보세요
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-muted">
          매일 한국시간 08:30 / 20:30에
          <br />
          AI가 정리한 미국 경제 뉴스 브리핑을
          <br />
          Google 로그인 한 번으로 모두 보실 수 있어요.
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/" });
          }}
        >
          <button
            type="submit"
            className="mt-7 inline-flex items-center gap-2 rounded-lg bg-accent text-bg px-6 py-3 text-sm font-medium hover:bg-ink/90 transition-colors"
          >
            Google로 시작하기
          </button>
        </form>
        <p className="mt-6 text-2xs text-subtle">
          이메일·이름·프로필 사진만 저장하고
          <br />
          광고/마케팅 발송은 일절 없습니다.
        </p>
      </main>
      <Footer />
    </>
  );
}
