import { auth } from "@/auth";
import { NextResponse } from "next/server";

export const API_BASE = process.env.API_INTERNAL_URL || "http://127.0.0.1:43124";

export async function signedInUser() {
  const session = await auth();
  const email = session?.user?.email;
  if (!email) return null;
  const displayName = session.user?.name?.trim() || email.split("@")[0];
  return { email, displayName };
}

export function unauthorized() {
  return NextResponse.json({ detail: "Sign in with Google first." }, { status: 401 });
}

export async function ensureProfile() {
  const user = await signedInUser();
  if (!user) return { user: null, profile: null as { syntheticId: string } | null, error: unauthorized() };
  const res = await fetch(`${API_BASE}/api/profiles/ensure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });
  const text = await res.text();
  if (!res.ok) {
    return {
      user,
      profile: null,
      error: new NextResponse(text, {
        status: res.status,
        headers: { "content-type": res.headers.get("content-type") || "application/json" },
      }),
    };
  }
  return { user, profile: JSON.parse(text) as { syntheticId: string }, error: null };
}

export function passThrough(res: Response, body: string) {
  return new NextResponse(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") || "application/json" },
  });
}
