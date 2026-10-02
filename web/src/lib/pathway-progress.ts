import type { BadgeEntry, CatalogBadge, CatalogProgram, CourseEntry, StudentProfile } from "./types";

export function normalizeCourseCode(code: string | null | undefined): string {
  return (code || "").replace(/[^A-Za-z0-9]/g, "").toUpperCase();
}

export function normalizeBadgeName(name: string | null | undefined): string {
  return (name || "")
    .toLowerCase()
    .replace(/post-?baccalaureate\s+/g, "")
    .replace(/graduate\s+/g, "")
    .replace(/badge\s+in\s+/g, "")
    .replace(/^badge\s+/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const STATUS_RANK: Record<CourseEntry["status"], number> = {
  completed: 3,
  in_progress: 2,
  planned: 1,
};

export function studentCourseMap(courses: CourseEntry[] | undefined): Map<string, CourseEntry> {
  const map = new Map<string, CourseEntry>();
  for (const row of courses || []) {
    const code = normalizeCourseCode(row.code);
    if (!code) continue;
    const prev = map.get(code);
    if (!prev || STATUS_RANK[row.status] > STATUS_RANK[prev.status]) {
      map.set(code, row);
    }
  }
  return map;
}

export function courseOnRecord(
  map: Map<string, CourseEntry>,
  code: string
): CourseEntry | undefined {
  const row = map.get(normalizeCourseCode(code));
  if (!row || row.status === "planned") return undefined;
  return row;
}

export function isStudentBadge(studentBadges: BadgeEntry[] | undefined, catalog: CatalogBadge): boolean {
  const catalogName = normalizeBadgeName(catalog.name);
  if (!catalogName) return false;
  return (studentBadges || []).some((badge) => {
    if (badge.status === "none") return false;
    const name = normalizeBadgeName(badge.name);
    if (!name) return false;
    return name === catalogName || name.includes(catalogName) || catalogName.includes(name);
  });
}

export function studentBadgeFor(
  studentBadges: BadgeEntry[] | undefined,
  catalog: CatalogBadge
): BadgeEntry | undefined {
  const catalogName = normalizeBadgeName(catalog.name);
  return (studentBadges || []).find((badge) => {
    if (badge.status === "none") return false;
    const name = normalizeBadgeName(badge.name);
    return name === catalogName || name.includes(catalogName) || catalogName.includes(name);
  });
}

export function badgeCoursesOnRecord(badge: CatalogBadge, map: Map<string, CourseEntry>): CourseEntry[] {
  const seen = new Set<string>();
  const out: CourseEntry[] = [];
  for (const course of badge.courses || []) {
    const row = courseOnRecord(map, course.code);
    const code = normalizeCourseCode(course.code);
    if (!row || seen.has(code)) continue;
    seen.add(code);
    out.push(row);
  }
  return out;
}

export function preferredProgramId(
  profile: StudentProfile | null,
  programs: CatalogProgram[]
): string | undefined {
  const blob = [
    profile?.transcriptLevel,
    profile?.degreeLine,
    profile?.major,
    ...(profile?.majors || []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  if (blob.includes("master") || blob.includes("applied")) {
    return programs.find((p) => p.id === "applied-cs-ms")?.id ?? programs[0]?.id;
  }
  if (blob.includes("bachelor") || blob.includes("undergraduate")) {
    return programs.find((p) => p.id === "cs-bs")?.id ?? programs[0]?.id;
  }
  return programs.find((p) => p.id === "applied-cs-ms")?.id ?? programs[0]?.id;
}
