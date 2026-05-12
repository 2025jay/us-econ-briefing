// NextAuth.js v5 — App Router catch-all handler
// /api/auth/signin, /api/auth/callback/google, /api/auth/signout 등 자동 라우팅

import { handlers } from "@/auth";

export const { GET, POST } = handlers;
