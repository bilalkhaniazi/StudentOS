import { redirect } from "next/navigation";
import { auth } from "@/auth";
import {
  allowedEmailDomains,
  formatDomainList,
  isDevLoginEnabled,
  isGoogleOAuthConfigured,
} from "@/lib/auth-config";
import { LoginCard } from "./login-card";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Sign in · StudentOS",
  description: "Sign in to StudentOS with a GVSU Google account.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const session = await auth();
  if (session?.user) {
    redirect("/");
  }

  const params = await searchParams;
  const domains = allowedEmailDomains();

  return (
    <LoginCard
      errorCode={params.error}
      googleConfigured={isGoogleOAuthConfigured()}
      devLogin={isDevLoginEnabled()}
      domains={domains}
      domainLabel={formatDomainList(domains)}
    />
  );
}
