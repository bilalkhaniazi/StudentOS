"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signOut, useSession } from "next-auth/react";
import { BookOpen, GraduationCap, LogOut, Menu, Target, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { createDemoProfile, getProfiles, getSession, setSession } from "@/lib/api";
import { PUBLIC_APP_ORIGIN } from "@/lib/auth-config";
import type { StudentProfile } from "@/lib/types";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Overview", icon: GraduationCap },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/career", label: "Career", icon: Target },
  { href: "/courses", label: "Courses", icon: BookOpen },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [activeId, setActiveId] = useState<string>("demo-profile");
  const [open, setOpen] = useState(false);
  const email = session?.user?.email;

  async function load() {
    const [session, list] = await Promise.all([getSession(), getProfiles()]);
    setProfiles(list);
    setActiveId(session.activeProfileId || "demo-profile");
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, [pathname]);

  async function onSwitch(id: string | null) {
    if (!id) return;
    await setSession(id);
    setActiveId(id);
    router.refresh();
  }

  async function onSignOut() {
    try {
      await signOut({ redirect: false, callbackUrl: `${PUBLIC_APP_ORIGIN}/login` });
    } catch {
      // Still leave the signed-in page so a failed Auth.js call cannot stick the browser on localhost.
    }
    window.location.replace(`${PUBLIC_APP_ORIGIN}/login`);
  }

  async function onNewDemo() {
    const created = await createDemoProfile();
    await load();
    setActiveId(created.syntheticId);
    router.push("/profile");
  }

  const synthetics = profiles.filter((p) => p.synthetic);
  const demos = profiles.filter((p) => !p.synthetic);

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
            <span className="hidden max-w-[160px] truncate text-[11px] text-white/75 lg:inline" title={email ?? undefined}>
              {email ?? "Signed in"}
            </span>
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
            <Select value={activeId} onValueChange={(value) => onSwitch(value as string)}>
              <SelectTrigger className="h-8 max-w-[220px] border-white/20 bg-white/5 text-left text-xs text-[color:var(--header-foreground)] md:max-w-[280px]">
                <SelectValue placeholder="Choose a profile" />
              </SelectTrigger>
              <SelectContent align="end" className="min-w-64">
                <SelectGroup>
                  <SelectLabel>Demo profile</SelectLabel>
                  {demos.map((p) => (
                    <SelectItem key={p.syntheticId} value={p.syntheticId}>
                      {p.displayName}
                    </SelectItem>
                  ))}
                </SelectGroup>
                <SelectGroup>
                  <SelectLabel>Synthetic CS students</SelectLabel>
                  {synthetics.map((p) => (
                    <SelectItem key={p.syntheticId} value={p.syntheticId}>
                      {p.displayName}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
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
                  {email ? <p className="truncate text-xs text-muted-foreground">{email}</p> : null}
                  <Button type="button" variant="outline" className="w-full" onClick={onNewDemo}>
                    Reset my demo profile
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    className="w-full"
                    onClick={onSignOut}
                  >
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
            Course titles, credits, and prerequisites are structured fields from the GVSU{" "}
            {profiles.length ? "2026–2027" : ""} public catalog. Not official SIS.
          </p>
          <p>Local student demo. Not official Grand Valley software. Campus SSO is not used here.</p>
        </div>
      </footer>
    </div>
  );
}
