import NextAuth from "next-auth";
import { NextResponse } from "next/server";
import type { NextFetchEvent, NextRequest } from "next/server";
import { authConfig } from "@/auth.config";
import { isLoopbackAlias, PUBLIC_APP_ORIGIN, publicOriginFromRequest } from "@/lib/auth-config";

const { auth } = NextAuth(authConfig);

const gated = auth((req) => {
  const { pathname } = req.nextUrl;

  const isLogin = pathname === "/login";
  const isAuthApi = pathname.startsWith("/api/auth");
  const isHealth = pathname === "/health";
  const isBrand = pathname.startsWith("/brand");

  if (isAuthApi || isHealth || isBrand) {
    return NextResponse.next();
  }

  if (req.auth && isLogin) {
    return NextResponse.redirect(new URL("/", PUBLIC_APP_ORIGIN));
  }

  if (!req.auth && !isLogin) {
    return NextResponse.redirect(new URL("/login", PUBLIC_APP_ORIGIN));
  }

  return NextResponse.next();
});

export default function middleware(req: NextRequest, event: NextFetchEvent) {
  // Bounce before Auth.js runs. Its wrapper treats localhost as a different host
  // than AUTH_URL (127.0.0.1) and redirects to /login?error=Configuration.
  if (isLoopbackAlias(req.nextUrl.hostname)) {
    return NextResponse.redirect(publicOriginFromRequest(req.nextUrl.pathname, req.nextUrl.search));
  }
  return gated(req, event as never);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|brand/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
