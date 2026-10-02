import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import { authConfig } from "@/auth.config";
import {
  allowedEmailDomains,
  isAllowedEmail,
  isDevLoginEnabled,
  isGoogleOAuthConfigured,
} from "@/lib/auth-config";

export const { handlers, auth, signIn, signOut } = NextAuth(() => {
  const providers = [];

  if (isGoogleOAuthConfigured()) {
    providers.push(
      Google({
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
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
