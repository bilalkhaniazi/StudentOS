"use client";

import { SessionProvider } from "next-auth/react";
import { ThemeProvider } from "next-themes";
import { OriginGuard } from "@/components/origin-guard";
import { Toaster } from "@/components/ui/sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider basePath="/api/auth">
      <OriginGuard />
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
        <div className="flex min-h-screen flex-1 flex-col">{children}</div>
        <Toaster />
      </ThemeProvider>
    </SessionProvider>
  );
}
