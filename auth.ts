/**
 * NextAuth.js v5 (Auth.js) — Google OAuth + Supabase 사용자 저장.
 *
 * 환경변수:
 *   AUTH_SECRET                - 랜덤 32+ 문자열 (세션 암호화)
 *   AUTH_GOOGLE_ID             - Google OAuth Client ID
 *   AUTH_GOOGLE_SECRET         - Google OAuth Client Secret
 *   NEXT_PUBLIC_SUPABASE_URL   - 이미 사이트용으로 설정됨
 *   SUPABASE_SERVICE_ROLE_KEY  - 서버 전용. briefing.users 테이블에 upsert 권한
 *   (Vercel은 AUTH_URL, AUTH_TRUST_HOST 자동 처리)
 */

import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

// briefing 스키마에 쓰기 권한 가진 server-side admin 클라이언트
const supabaseAdmin =
  SUPABASE_URL && SERVICE_ROLE_KEY
    ? createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
        auth: { persistSession: false },
        db: { schema: "briefing" },
      })
    : null;

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async signIn({ user, profile }) {
      // 로그인 성공 시 Supabase briefing.users 테이블에 upsert
      if (!supabaseAdmin || !user.email || !profile?.sub) return true;
      try {
        await supabaseAdmin.from("users").upsert(
          {
            google_id: profile.sub,
            email: user.email,
            name: user.name ?? null,
            avatar_url: user.image ?? null,
            last_login: new Date().toISOString(),
          },
          { onConflict: "google_id" }
        );
      } catch (e) {
        // 저장 실패해도 로그인은 통과 — 차단하지 않음
        console.error("[auth] supabase user upsert 실패:", e);
      }
      return true;
    },
    async session({ session, token }) {
      if (token.sub && session.user) {
        // @ts-expect-error — extend session.user with google_id
        session.user.google_id = token.sub;
      }
      return session;
    },
  },
  session: { strategy: "jwt" },
});
