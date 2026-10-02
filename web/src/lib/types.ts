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

export type ProjectEntry = {
  name: string;
  summary?: string | null;
  technologies: string[];
  demonstratesSkills: string[];
  source?: string | null;
};

export type ExperienceEntry = {
  organization: string;
  title: string;
  location?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  current?: boolean;
  summary?: string | null;
  highlights?: string[];
  source?: string | null;
};

export type EducationEntry = {
  institution: string;
  degree?: string | null;
  field?: string | null;
  location?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  current?: boolean;
  source?: string | null;
};

export type LanguageEntry = {
  name: string;
  proficiency?: string | null;
  source?: string | null;
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
  studentType?: "international" | "domestic" | "unknown" | null;
  skills: { label: string; evidence: string }[];
  projects: ProjectEntry[];
  experiences: ExperienceEntry[];
  education: EducationEntry[];
  languages: LanguageEntry[];
  certifications: { name: string; taggedSkills: string[]; source?: string | null }[];
  courses: CourseEntry[];
  resumeFilename?: string | null;
  resumeReadAt?: string | null;
  resumeParsed?: {
    method?: string;
    warnings?: string[];
    emailsFound?: number;
    phonesFound?: number;
  } | null;
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
  badges?: string[];
};

export type PathwayCourse = {
  code: string;
  title: string;
  credits_min?: number | null;
  credits_max?: number | null;
  credits_text?: string | null;
  section: string;
  year?: string;
  badge_id?: string;
};

export type BadgeSlot = {
  kind: "all" | "choose_n";
  n: number;
  courses: PathwayCourse[];
};

export type CatalogBadge = {
  id: string;
  name: string;
  kind: string;
  credits: number;
  course_count: number;
  source_url: string;
  slots: BadgeSlot[];
  courses: PathwayCourse[];
};

export type CatalogProgram = {
  id: string;
  title: string;
  degree_line: string;
  major: string;
  level: string;
  source_url: string;
  catalog_year: string;
  overview?: string[];
  courses: PathwayCourse[];
  suggested_order?: PathwayCourse[];
  badges?: CatalogBadge[];
  rules?: Record<string, unknown>;
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
  parsed?: boolean;
  filename: string | null;
  profileId?: string | null;
  message: string;
  method?: string | null;
  warnings?: string[];
  summary?: string | null;
  experienceCount?: number;
  projectCount?: number;
  skillCount?: number;
  educationCount?: number;
  languageCount?: number;
  certificationCount?: number;
  studentTypeHint?: string | null;
};

export type Meta = {
  catalog_year?: string;
  ingested_at?: string;
  attribution?: string;
  courseCount: number;
  studentCount: number;
  slice: string;
};
