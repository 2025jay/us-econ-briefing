import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { auth, signIn, signOut } from "@/auth";

export default async function LoginPage() {
  const session = await auth();

  if (session?.user) {
    return (
      <>
        <Header />
        <main className="mx-auto max-w-mobile px-5 py-12 text-center">
          {session.user.image && (
            <img
              src={session.user.image}
              alt={session.user.name ?? "user"}
              className="mx-auto mb-3 h-16 w-16 rounded-full border border-line"
            />
          )}
          <p className="text-base font-medium text-ink">
            {session.user.name}
          </p>
          <p className="mt-1 text-xs text-muted">{session.user.email}</p>
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/" });
            }}
          >
            <button
              type="submit"
              className="mt-6 rounded-lg border border-line bg-surface px-4 py-2 text-sm text-muted hover:text-ink"
            >
              로그아웃
            </button>
          </form>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-mobile px-5 py-12 text-center">
        <h1 className="text-xl font-semibold text-ink">로그인</h1>
        <p className="mt-3 text-sm text-muted">
          로그인하면 새 브리핑이 올라올 때 알림을 받을 수 있어요.
          <br />
          콘텐츠는 누구나 무료로 볼 수 있어요.
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/" });
          }}
        >
          <button
            type="submit"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent text-bg px-5 py-2.5 text-sm font-medium hover:bg-ink/90 transition-colors"
          >
            Google로 로그인
          </button>
        </form>
        <p className="mt-8 text-2xs text-subtle">
          로그인 시 이메일·이름·프로필 사진을 저장합니다.
        </p>
      </main>
      <Footer />
    </>
  );
}
