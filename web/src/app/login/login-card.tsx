"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { AlertCircle, Ban, Loader2, ShieldAlert, WifiOff } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09A6.6 6.6 0 0 1 5.5 12c0-.72.13-1.43.34-2.09V7.07H2.18A11 11 0 0 0 1 12c0 1.78.43 3.46 1.18 4.93z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53"
      />
    </svg>
  );
}

function errorCopy(
  code: string | undefined,
  domainLabel: string,
  googleConfigured: boolean
): { title: string; body: string; icon: "cancel" | "domain" | "config" | "network" | "generic" } | null {
  if (!code) return null;
  const normalized = code.toLowerCase();

  if (normalized === "domain" || normalized === "accessdenied") {
    if (normalized === "domain") {
      return {
        icon: "domain",
        title: "That Google account is not a GVSU student email",
        body: `StudentOS only accepts ${domainLabel}. Sign out of the other Google account in the browser if needed, then try again with your university address.`,
      };
    }
    return {
      icon: "cancel",
      title: "Google sign-in was cancelled",
      body: "Nothing was saved. Use Continue with Google when you are ready.",
    };
  }

  if (normalized === "configuration" || normalized === "missing-config") {
    if (googleConfigured) {
      return {
        icon: "generic",
        title: "Google sign-in hit a configuration error",
        body: "The Google keys are on this PC. Open http://127.0.0.1:43123 (not localhost) and try Continue with Google again.",
      };
    }
    return {
      icon: "config",
      title: "Google sign-in is not set up on this PC yet",
      body: "The login page still works. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to the .env file, then stop and start StudentOS. The Google callback URL is http://127.0.0.1:43123/api/auth/callback/google",
    };
  }

  if (
    normalized === "oauthcallback" ||
    normalized === "oauthsignin" ||
    normalized === "callback" ||
    normalized === "oauthcreateaccount"
  ) {
    return {
      icon: "generic",
      title: "Google sign-in did not finish",
      body: "This is often a closed Google window, or the callback URL in Google Cloud does not match http://127.0.0.1:43123/api/auth/callback/google. Try again.",
    };
  }

  if (normalized === "network") {
    return {
      icon: "network",
      title: "Could not reach Google",
      body: "Check this PC’s internet connection, then try Continue with Google again.",
    };
  }

  return {
    icon: "generic",
    title: "Could not sign in",
    body: "StudentOS could not complete Google sign-in. Try again. If this keeps happening, confirm the Google client ID and secret, then restart StudentOS.",
  };
}

export function LoginCard({
  errorCode,
  googleConfigured,
  devLogin,
  domains,
  domainLabel,
}: {
  errorCode?: string;
  googleConfigured: boolean;
  devLogin: boolean;
  domains: string[];
  domainLabel: string;
}) {
  const [busy, setBusy] = useState<"google" | "dev" | null>(null);
  const [localError, setLocalError] = useState<string | undefined>();
  const shown = errorCopy(localError ?? errorCode, domainLabel, googleConfigured);
  const Icon =
    shown?.icon === "domain"
      ? ShieldAlert
      : shown?.icon === "cancel"
        ? Ban
        : shown?.icon === "network"
          ? WifiOff
          : AlertCircle;

  async function onGoogle() {
    if (!googleConfigured) return;
    setBusy("google");
    setLocalError(undefined);
    try {
      await signIn("google", { callbackUrl: "/" });
    } catch {
      setLocalError("network");
      setBusy(null);
    }
  }

  async function onDev() {
    setBusy("dev");
    setLocalError(undefined);
    try {
      const result = await signIn("dev", {
        intent: "local",
        callbackUrl: "/",
        redirect: false,
      });
      if (result?.error) {
        setLocalError(result.error);
        setBusy(null);
        return;
      }
      window.location.assign(result?.url ?? "/");
    } catch {
      setLocalError("network");
      setBusy(null);
    }
  }

  return (
    <div className="relative flex min-h-screen flex-1 flex-col overflow-hidden bg-[color:var(--gvsu-midnight)] text-white">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(1200px 600px at 12% -10%, color-mix(in srgb, var(--gvsu-blue) 88%, white) 0%, transparent 55%), radial-gradient(900px 500px at 110% 10%, color-mix(in srgb, var(--gvsu-link) 28%, transparent) 0%, transparent 50%), linear-gradient(160deg, var(--gvsu-midnight) 0%, var(--gvsu-blue) 58%, color-mix(in srgb, var(--gvsu-blue) 70%, black) 100%)",
        }}
      />
      <img
        src="/brand/mark-white.svg"
        alt=""
        className="pointer-events-none absolute -right-16 top-24 size-[28rem] opacity-[0.07] md:size-[36rem]"
      />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-5 py-8 md:px-10 md:py-12">
        <header className="flex items-center justify-between gap-4">
          <img
            src="/brand/markleft-white.svg"
            alt="Grand Valley State University"
            className="hidden h-10 w-auto md:block md:h-12"
          />
          <img
            src="/brand/mark-white.svg"
            alt="Grand Valley State University"
            className="h-12 w-12 md:hidden"
          />
          <p className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-white/80">
            Local student demo
          </p>
        </header>

        <div className="grid flex-1 items-center gap-10 py-10 md:grid-cols-[1.05fr_0.95fr] md:gap-16 md:py-8">
          <section className="max-w-xl space-y-5">
            <p className="text-xs font-medium uppercase tracking-[0.28em] text-[color:var(--gvsu-link)]">
              Grand Valley · Computer Science
            </p>
            <h1 className="font-heading text-4xl leading-[1.05] tracking-tight md:text-5xl lg:text-[3.4rem]">
              StudentOS
            </h1>
            <p className="max-w-md text-base leading-relaxed text-white/80 md:text-lg">
              Sign in with your GVSU Google account to open your academic profile
              and the Computer Science catalog.
            </p>
            <p className="text-sm text-white/65">
              Use {domainLabel}. This is a student project demo. It is not Banner,
              not course registration, and not official university software.
            </p>
          </section>

          <section className="w-full">
            <div className="rounded-3xl bg-white p-6 text-[color:var(--gvsu-midnight)] shadow-[0_24px_80px_-20px_rgba(0,0,0,0.45)] ring-1 ring-black/5 md:p-8">
              <div className="mb-6 flex items-center gap-3">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-[color:var(--gvsu-blue)]">
                  <img src="/brand/mark-white.svg" alt="" className="size-8" />
                </span>
                <div>
                  <p className="font-heading text-xl leading-tight">Student sign-in</p>
                  <p className="text-sm text-muted-foreground">Google only · GVSU email</p>
                </div>
              </div>

              {shown ? (
                <Alert variant="destructive" className="mb-5 border-destructive/30 bg-destructive/5 text-destructive">
                  <Icon />
                  <AlertTitle>{shown.title}</AlertTitle>
                  <AlertDescription>{shown.body}</AlertDescription>
                </Alert>
              ) : null}

              {!googleConfigured ? (
                <Alert className="mb-5 border-[color:var(--gvsu-blue)]/20 bg-[color:var(--gvsu-blue)]/5">
                  <AlertCircle className="text-[color:var(--gvsu-blue)]" />
                  <AlertTitle>Google is not connected on this PC yet</AlertTitle>
                  <AlertDescription>
                    This page still works. Add <span className="font-medium">GOOGLE_CLIENT_ID</span> and{" "}
                    <span className="font-medium">GOOGLE_CLIENT_SECRET</span> to the{" "}
                    <span className="font-medium">.env</span> file in the StudentOS folder, then stop and
                    start StudentOS. Authorized redirect URI:{" "}
                    <span className="break-all font-medium">
                      http://127.0.0.1:43123/api/auth/callback/google
                    </span>
                  </AlertDescription>
                </Alert>
              ) : null}

              <Button
                type="button"
                size="lg"
                disabled={!googleConfigured || busy !== null}
                onClick={onGoogle}
                className="h-12 w-full gap-3 rounded-xl border border-[#dadce0] bg-white text-[15px] font-medium text-[#3c4043] hover:bg-[#f8f9fa] hover:text-[#3c4043] disabled:opacity-60"
              >
                {busy === "google" ? (
                  <Loader2 className="size-5 animate-spin" />
                ) : (
                  <GoogleMark />
                )}
                Continue with Google
              </Button>

              <p className="mt-4 text-center text-xs leading-relaxed text-muted-foreground">
                Allowed domains: {domains.map((d) => `@${d}`).join(" · ")}
              </p>

              {devLogin ? (
                <div className="mt-6 border-t border-border pt-5">
                  <Button
                    type="button"
                    variant="outline"
                    className="h-10 w-full"
                    disabled={busy !== null}
                    onClick={onDev}
                  >
                    {busy === "dev" ? <Loader2 className="size-4 animate-spin" /> : null}
                    Continue as local demo
                  </Button>
                  <p className="mt-2 text-center text-[11px] text-muted-foreground">
                    Development bypass is on. Turn off NEXT_PUBLIC_DEV_LOGIN for real Google-only sign-in.
                  </p>
                </div>
              ) : null}
            </div>
          </section>
        </div>

        <footer className="mt-auto flex flex-col gap-1 border-t border-white/15 pt-5 text-xs text-white/60 md:flex-row md:items-center md:justify-between">
          <p>Local student demo for GVSU Computer Science. Not official Grand Valley software.</p>
          <p>Wordmark from the public gvsu.edu website.</p>
        </footer>
      </div>
    </div>
  );
}
