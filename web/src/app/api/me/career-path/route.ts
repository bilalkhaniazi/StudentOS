import { API_BASE, ensureProfile, passThrough, unauthorized } from "@/lib/me-server";

export async function GET() {
  const { profile, error } = await ensureProfile();
  if (error || !profile) return error ?? unauthorized();
  const res = await fetch(
    `${API_BASE}/api/profiles/${encodeURIComponent(profile.syntheticId)}/career-path`
  );
  return passThrough(res, await res.text());
}
