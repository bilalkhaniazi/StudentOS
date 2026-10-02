import { API_BASE, ensureProfile, passThrough, unauthorized } from "@/lib/me-server";

export async function POST(request: Request) {
  const { profile, error } = await ensureProfile();
  if (error || !profile) return error ?? unauthorized();
  const incoming = await request.formData();
  const file = incoming.get("file");
  if (!(file instanceof File)) {
    return Response.json({ detail: "Choose a resume file first." }, { status: 400 });
  }
  const body = new FormData();
  body.append("file", file, file.name);
  const res = await fetch(
    `${API_BASE}/api/resumes/import?profile_id=${encodeURIComponent(profile.syntheticId)}`,
    { method: "POST", body }
  );
  return passThrough(res, await res.text());
}
