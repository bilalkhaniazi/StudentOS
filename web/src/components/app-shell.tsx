"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { BookOpen, GraduationCap, LogOut, Menu, Route, Target, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useState } from "react";
import { PUBLIC_APP_ORIGIN } from "@/lib/auth-config";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Overview", icon: GraduationCap },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/career", label: "Career", icon: Target },
  { href: "/pathways", label: "Pathways", icon: Route },
  { href: "/courses", label: "Courses", icon: BookOpen },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const name = session?.user?.name?.trim();
  const email = session?.user?.email;

  async function onSignOut() {
    try {
      await signOut({ redirect: false, callbackUrl: `${PUBLIC_APP_ORIGIN}/login` });
    } catch {
      // Still leave the signed-in page so a failed Auth.js call cannot stick the browser on localhost.
    }
    window.location.replace(`${PUBLIC_APP_ORIGIN}/login`);
  }

  const links = (
    <nav className="flex flex-col gap-1 md:flex-row md:items-center md:gap-0.5">
      {NAV.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
              active
                ? "bg-primary/10 font-medium text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-40 border-b border-border/80 bg-[color:var(--header)] text-[color:var(--header-foreground)]">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 md:px-6">
          <Link href="/" className="flex items-center gap-2 pr-2">
            <img src="/brand/mark-white.svg" alt="" className="size-8" />
            <span className="font-heading text-lg tracking-tight">StudentOS</span>
          </Link>
          <div className="hidden flex-1 md:block">{links}</div>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden text-right lg:block">
              <p className="max-w-[200px] truncate text-sm font-medium leading-tight" title={name ?? undefined}>
                {name || "Signed in"}
              </p>
              {email ? (
                <p className="max-w-[200px] truncate text-[11px] text-white/70" title={email}>
                  {email}
                </p>
              ) : null}
            </div>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="hidden text-[color:var(--header-foreground)] hover:bg-white/10 hover:text-white md:inline-flex"
              onClick={onSignOut}
            >
              <LogOut className="size-3.5" />
              Sign out
            </Button>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger
                render={
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="text-[color:var(--header-foreground)] md:hidden"
                  />
                }
              >
                <Menu className="size-5" />
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetHeader>
                  <SheetTitle>StudentOS</SheetTitle>
                </SheetHeader>
                <div className="px-2">{links}</div>
                <div className="space-y-2 px-4">
                  {name ? <p className="text-sm font-medium">{name}</p> : null}
                  {email ? <p className="truncate text-xs text-muted-foreground">{email}</p> : null}
                  <Button type="button" variant="ghost" className="w-full" onClick={onSignOut}>
                    Sign out
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-6 md:py-10">{children}</main>
      <footer className="border-t border-border bg-card/50">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-4 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between md:px-6">
          <p>
            Course titles, credits, and prerequisites are structured fields from the GVSU public
            catalog. Not official SIS.
          </p>
          <p>Not official Grand Valley software. Campus SSO is not used here.</p>
        </div>
      </footer>
    </div>
  );
}
