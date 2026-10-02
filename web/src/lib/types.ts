export type CourseStatus = "completed" | "in_progress" | "planned";

export type CourseEntry = {
  subject: string;
  courseNumber: string;
  code: string;
  level?: string | null;
  title?: string | null;
  creditHours?: number | null;
  gradeLetter?: string | null;
  repeatFlag?: string | null;
  term?: string | null;
  termSource?: "Period" | "Term" | null;
  status: CourseStatus;
};

export type BadgeEntry = {
  name: string;
  kind: string;
  college?: string | null;
  status: "awarded" | "pending" | "none";
  awardedOn?: string | null;
};

export type StudentProfile = {
  syntheticId: string;
  displayName: string;
  email?: string | null;
  institution: string;
  transcriptLevel: "Undergraduate" | "Masters" | null;
  transcriptType: string;
  college?: string | null;
  degreeLine?: string | null;
  major?: string | null;
  majors: string[];
  majorAndDepartment?: string | null;
  badges: BadgeEntry[];
  catalogYear?: string | null;
  targetCareer?: string | null;
  careerInterests: string[];
  remainingCredits?: number | null;
  termCreditPreference?: string;
  summary?: string | null;
  skills: { label: string; evidence: string }[];
  projects: {
    name: string;
    summary?: string | null;
    technologies: string[];
    demonstratesSkills: string[];
  }[];
  certifications: { name: string; taggedSkills: string[] }[];
  courses: CourseEntry[];
  resumeFilename?: string | null;
  resumeReadAt?: string | null;
  editable?: boolean;
  synthetic?: boolean;
};

export type Career = {
  id: string;
  label: string;
  shortLabel: string;
  onetSoc: string;
  onetTitle: string;
  summary: string;
};

export type CatalogCourse = {
  id: string;
  code: string;
  subject: string;
  course_number: string;
  title: string;
  description: string;
  credits_min?: number | null;
  credits_max?: number | null;
  credits_text?: string | null;
  prerequisites_text?: string | null;
  prerequisite_codes: string[];
  offered?: string | null;
  source_url: string;
  catalog_year: string;
  level: string;
  topics: string[];
  programs: Record<string, string[]>;
  prerequisiteCourses?: CatalogCourse[];
  unlocksCourses?: CatalogCourse[];
};

export type Session = {
  identityId: string;
  identityLabel: string;
  activeProfileId: string | null;
  note?: string;
};

export type TranscriptImportResult = {
  accepted: boolean;
  filename: string | null;
  message: string;
  parsed: boolean;
  profileId?: string | null;
  transcriptLevel?: string | null;
  college?: string | null;
  degreeLine?: string | null;
  major?: string | null;
  majors: string[];
  badges: BadgeEntry[];
  remainingCredits?: number | null;
  method?: string | null;
  warnings: string[];
  completed: CourseEntry[];
  inProgress: CourseEntry[];
  remaining: CourseEntry[];
};

export type ResumeImportResult = {
  accepted: boolean;
  stored: boolean;
  filename: string | null;
  profileId?: string | null;
  message: string;
};

export type Meta = {
  catalog_year?: string;
  ingested_at?: string;
  attribution?: string;
  courseCount: number;
  studentCount: number;
  slice: string;
};
