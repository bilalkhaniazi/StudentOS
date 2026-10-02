import type {
  Career,
  CareerPathPayload,
  CareerSurveyAnswers,
  CatalogCourse,
  CatalogProgram,
  Meta,
  ResumeImportResult,
  StudentProfile,
  TranscriptImportResult,
} from "./types";

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
export const getMe = () => api<StudentProfile>("/api/me");
export const updateMe = (body: Partial<StudentProfile>) =>
  api<StudentProfile>("/api/me", {
    method: "PUT",
    body: JSON.stringify(body),
  });
export const setMyCareer = (targetCareer: string) =>
  api<StudentProfile>("/api/me/career", {
    method: "PUT",
    body: JSON.stringify({ targetCareer }),
  });
export const getCareerPath = () => api<CareerPathPayload>("/api/me/career-path");
export const submitCareerSurvey = (
  answers: CareerSurveyAnswers,
  confirmCareerId?: string | null
) =>
  api<CareerPathPayload>("/api/me/career-survey", {
    method: "POST",
    body: JSON.stringify({ answers, confirmCareerId: confirmCareerId ?? null }),
  });
export const getCareers = () => api<Career[]>("/api/careers");
export const getPrograms = () => api<CatalogProgram[]>("/api/programs");
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
  return api<TranscriptImportResult>("/api/me/transcript", { method: "POST", body });
}

export async function importResume(file: File) {
  const body = new FormData();
  body.append("file", file);
  return api<ResumeImportResult>("/api/me/resume", { method: "POST", body });
}

export function courseHref(code: string) {
  return `/courses/${encodeURIComponent(code.replaceAll(" ", "-"))}`;
}

export function careerLabel(id: string | null | undefined, careers: Career[]) {
  return careers.find((c) => c.id === id)?.label ?? null;
}
