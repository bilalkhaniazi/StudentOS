import type { NextAuthConfig } from "next-auth";

const localSecret =
  process.env.AUTH_SECRET ||
  process.env.NEXTAUTH_SECRET ||
  "studentos-local-dev-secret-change-me";

/** Edge-safe Auth.js options used by middleware. Providers live in `auth.ts`. */
export const authConfig = {
  trustHost: true,
  secret: localSecret,
  session: { strategy: "jwt" as const },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  providers: [],
} satisfies NextAuthConfig;
