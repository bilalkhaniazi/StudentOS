/**
 * Single place to change which emails may sign in.
 *
 * Override with ALLOWED_EMAIL_DOMAINS in `.env` (comma-separated, no @).
 * Example: ALLOWED_EMAIL_DOMAINS=mail.gvsu.edu,gvsu.edu
 */
export const DEFAULT_ALLOWED_EMAIL_DOMAINS = ["mail.gvsu.edu", "gvsu.edu"] as const;

export function allowedEmailDomains(): string[] {
  const raw = process.env.ALLOWED_EMAIL_DOMAINS?.trim();
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
  return Boolean(process.env.GOOGLE_CLIENT_ID?.trim() && process.env.GOOGLE_CLIENT_SECRET?.trim());
}

export function isDevLoginEnabled(): boolean {
  const flag = process.env.DEV_LOGIN ?? process.env.NEXT_PUBLIC_DEV_LOGIN;
  return flag === "true";
}

export function formatDomainList(domains: string[] = allowedEmailDomains()): string {
  if (domains.length === 0) return "";
  if (domains.length === 1) return `@${domains[0]}`;
  if (domains.length === 2) return `@${domains[0]} or @${domains[1]}`;
  const head = domains.slice(0, -1).map((d) => `@${d}`);
  return `${head.join(", ")}, or @${domains[domains.length - 1]}`;
}
