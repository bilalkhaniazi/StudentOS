import NextAuth from "next-auth";
import { NextResponse } from "next/server";
import { authConfig } from "@/auth.config";

const { auth } = NextAuth(authConfig);

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLogin = pathname === "/login";
  const isAuthApi = pathname.startsWith("/api/auth");
  const isHealth = pathname === "/health";
  const isBrand = pathname.startsWith("/brand");

  if (isAuthApi || isHealth || isBrand) {
    return NextResponse.next();
  }

  if (req.auth && isLogin) {
    return NextResponse.redirect(new URL("/", req.nextUrl));
  }

  if (!req.auth && !isLogin) {
    return NextResponse.redirect(new URL("/login", req.nextUrl));
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|brand/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
