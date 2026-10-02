import type { Career, CatalogCourse, Meta, Session, StudentProfile } from "./types";

async function parseError(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const json = JSON.parse(text) as { detail?: string };
    if (json.detail) return json.detail;
  } catch {
    /* use text */
  }
  return text || res.statusText;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const getMeta = () => api<Meta>("/api/meta");
export const getSession = () => api<Session>("/api/session");
export const setSession = (activeProfileId: string) =>
  api<Session>("/api/session", {
    method: "PUT",
    body: JSON.stringify({ activeProfileId }),
  });
export const getProfiles = () => api<StudentProfile[]>("/api/profiles");
export const getProfile = (id: string) => api<StudentProfile>(`/api/profiles/${id}`);
export const createDemoProfile = () =>
  api<StudentProfile>("/api/profiles", { method: "POST" });
export const updateProfile = (id: string, body: Partial<StudentProfile>) =>
  api<StudentProfile>(`/api/profiles/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
export const setCareer = (id: string, targetCareer: string) =>
  api<StudentProfile>(`/api/profiles/${id}/career`, {
    method: "PUT",
    body: JSON.stringify({ targetCareer }),
  });
export const getCareers = () => api<Career[]>("/api/careers");
export const getCourses = (params: Record<string, string | undefined> = {}) => {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v);
  }
  const suffix = q.toString() ? `?${q}` : "";
  return api<{ count: number; courses: CatalogCourse[] }>(`/api/courses${suffix}`);
};
export const getCourse = (code: string) =>
  api<CatalogCourse>(`/api/courses/${encodeURIComponent(code)}`);

export async function importTranscript(file: File) {
  const body = new FormData();
  body.append("file", file);
  return api<{
    accepted: boolean;
    filename: string | null;
    message: string;
    parsed: boolean;
  }>("/api/transcripts/import", { method: "POST", body });
}

export function courseHref(code: string) {
  return `/courses/${encodeURIComponent(code.replaceAll(" ", "-"))}`;
}

export function careerLabel(id: string | null | undefined, careers: Career[]) {
  return careers.find((c) => c.id === id)?.label ?? null;
}
