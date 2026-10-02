import { NextRequest } from "next/server";
import { API_BASE, ensureProfile, passThrough, unauthorized } from "@/lib/me-server";

export async function PUT(request: NextRequest) {
  const { profile, error } = await ensureProfile();
  if (error || !profile) return error ?? unauthorized();
  const body = await request.text();
  const res = await fetch(`${API_BASE}/api/profiles/${encodeURIComponent(profile.syntheticId)}/career`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return passThrough(res, await res.text());
}
