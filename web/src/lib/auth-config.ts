/**
 * Canonical public origin. Must match the Google OAuth JavaScript origin
 * and redirect URI. Do not use localhost — Google treats it as a different host.
 */
export const PUBLIC_APP_ORIGIN = "http://127.0.0.1:43123";

export const GOOGLE_CALLBACK_URL = `${PUBLIC_APP_ORIGIN}/api/auth/callback/google`;

/**
 * Single place to change which emails may sign in.
 *
 * Override with ALLOWED_EMAIL_DOMAINS in `.env` (comma-separated, no @).
 * Example: ALLOWED_EMAIL_DOMAINS=mail.gvsu.edu,gvsu.edu
 */
export const DEFAULT_ALLOWED_EMAIL_DOMAINS = ["mail.gvsu.edu", "gvsu.edu"] as const;

function runtimeEnv(name: string): string {
  // Bracket access so Next.js does not inline empty values at Docker build time.
  return (process.env[name] ?? "").trim();
}

export function allowedEmailDomains(): string[] {
  const raw = runtimeEnv("ALLOWED_EMAIL_DOMAINS");
  if (!raw) {
    return [...DEFAULT_ALLOWED_EMAIL_DOMAINS];
  }
  const parsed = raw
    .split(",")
    .map((part) => part.trim().toLowerCase().replace(/^@/, ""))
    .filter(Boolean);
  return parsed.length ? parsed : [...DEFAULT_ALLOWED_EMAIL_DOMAINS];
}

export function isAllowedEmail(email: string | null | undefined): boolean {
  if (!email || !email.includes("@")) return false;
  const domain = email.split("@").pop()?.trim().toLowerCase() ?? "";
  return allowedEmailDomains().includes(domain);
}

export function isGoogleOAuthConfigured(): boolean {
  return Boolean(runtimeEnv("GOOGLE_CLIENT_ID") && runtimeEnv("GOOGLE_CLIENT_SECRET"));
}

export function googleClientId(): string {
  return runtimeEnv("GOOGLE_CLIENT_ID");
}

export function googleClientSecret(): string {
  return runtimeEnv("GOOGLE_CLIENT_SECRET");
}

export function isDevLoginEnabled(): boolean {
  return (runtimeEnv("DEV_LOGIN") || runtimeEnv("NEXT_PUBLIC_DEV_LOGIN")) === "true";
}

export function formatDomainList(domains: string[] = allowedEmailDomains()): string {
  if (domains.length === 0) return "";
  if (domains.length === 1) return `@${domains[0]}`;
  if (domains.length === 2) return `@${domains[0]} or @${domains[1]}`;
  const head = domains.slice(0, -1).map((d) => `@${d}`);
  return `${head.join(", ")}, or @${domains[domains.length - 1]}`;
}
