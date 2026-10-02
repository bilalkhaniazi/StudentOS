import type { NextAuthConfig } from "next-auth";
import { PUBLIC_APP_ORIGIN, toPublicAppUrl } from "@/lib/auth-config";

process.env["AUTH_URL"] = PUBLIC_APP_ORIGIN;
process.env["NEXTAUTH_URL"] = PUBLIC_APP_ORIGIN;

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
  callbacks: {
    redirect({ url }) {
      return toPublicAppUrl(url);
    },
  },
  providers: [],
} satisfies NextAuthConfig;
