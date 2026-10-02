import { NextRequest } from "next/server";
import { API_BASE, ensureProfile, passThrough, signedInUser, unauthorized } from "@/lib/me-server";

export async function GET() {
  const { profile, error } = await ensureProfile();
  if (error) return error;
  return Response.json(profile);
}

export async function PUT(request: NextRequest) {
  const { profile, error } = await ensureProfile();
  if (error || !profile) return error ?? unauthorized();
  const body = await request.text();
  const res = await fetch(`${API_BASE}/api/profiles/${encodeURIComponent(profile.syntheticId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return passThrough(res, await res.text());
}

export async function HEAD() {
  const user = await signedInUser();
  return new Response(null, { status: user ? 204 : 401 });
}
