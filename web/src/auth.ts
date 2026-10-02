import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import { authConfig } from "@/auth.config";
import {
  allowedEmailDomains,
  googleClientId,
  googleClientSecret,
  isAllowedEmail,
  isDevLoginEnabled,
  isGoogleOAuthConfigured,
  PUBLIC_APP_ORIGIN,
} from "@/lib/auth-config";

process.env["AUTH_URL"] ??= PUBLIC_APP_ORIGIN;
process.env["NEXTAUTH_URL"] ??= PUBLIC_APP_ORIGIN;

export const { handlers, auth, signIn, signOut } = NextAuth(() => {
  const providers = [];

  if (isGoogleOAuthConfigured()) {
    providers.push(
      Google({
        clientId: googleClientId(),
        clientSecret: googleClientSecret(),
        // Auth.js otherwise builds this from the request host (often "localhost"),
        // which Google rejects because the client is registered for 127.0.0.1.
        redirectProxyUrl: `${PUBLIC_APP_ORIGIN}/api/auth`,
      })
    );
  }

  if (isDevLoginEnabled()) {
    providers.push(
      Credentials({
        id: "dev",
        name: "Local demo",
        credentials: {
          intent: { label: "intent", type: "text" },
        },
        authorize: async () => {
          if (!isDevLoginEnabled()) return null;
          const domain = allowedEmailDomains()[0] ?? "mail.gvsu.edu";
          return {
            id: "local-demo",
            name: "Local demo",
            email: `demo@${domain}`,
          };
        },
      })
    );
  }

  return {
    ...authConfig,
    providers,
    callbacks: {
      async signIn({ user, account }) {
        if (account?.provider === "dev") {
          return isDevLoginEnabled();
        }
        if (!isAllowedEmail(user.email)) {
          return "/login?error=domain";
        }
        return true;
      },
    },
  };
});
