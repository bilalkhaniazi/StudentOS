import NextAuth from "next-auth";
import { NextResponse } from "next/server";
import { authConfig } from "@/auth.config";

const { auth } = NextAuth(authConfig);

function appOrigin(req: { nextUrl: URL }) {
  return (process.env.AUTH_URL || req.nextUrl.origin).replace(/\/$/, "");
}

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const origin = appOrigin(req);
  const isLogin = pathname === "/login";
  const isAuthApi = pathname.startsWith("/api/auth");
  const isHealth = pathname === "/health";
  const isBrand = pathname.startsWith("/brand");

  if (isAuthApi || isHealth || isBrand) {
    return NextResponse.next();
  }

  if (req.auth && isLogin) {
    return NextResponse.redirect(new URL("/", origin));
  }

  if (!req.auth && !isLogin) {
    return NextResponse.redirect(new URL("/login", origin));
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|brand/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
