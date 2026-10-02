"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { FileText, FileUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { getCourses, getMe, importResume, importTranscript, updateMe } from "@/lib/api";
import type { CatalogCourse, CourseEntry, StudentProfile } from "@/lib/types";
import { ResumeProfileSections } from "./resume-sections";

function normalizeProfile(p: StudentProfile): StudentProfile {
  return {
    ...p,
    skills: p.skills ?? [],
    projects: p.projects ?? [],
    experiences: p.experiences ?? [],
    education: p.education ?? [],
    languages: p.languages ?? [],
    certifications: p.certifications ?? [],
    courses: p.courses ?? [],
    badges: p.badges ?? [],
    majors: p.majors ?? [],
    careerInterests: p.careerInterests ?? [],
  };
}

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [catalog, setCatalog] = useState<CatalogCourse[]>([]);
  const [courseQuery, setCourseQuery] = useState("");
  const [grade, setGrade] = useState("B");
  const [term, setTerm] = useState("Fall 2026");
  const [status, setStatus] = useState<CourseEntry["status"]>("completed");
  const [importing, setImporting] = useState(false);
  const [resumeBusy, setResumeBusy] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [courses, p] = await Promise.all([getCourses(), getMe()]);
      setCatalog(courses.courses);
      setProfile(normalizeProfile(p));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the profile.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const matches = useMemo(() => {
    const needle = courseQuery.trim().toLowerCase();
    if (needle.length < 2) return [];
    return catalog
      .filter(
        (c) =>
          c.code.toLowerCase().includes(needle) ||
          (c.title || "").toLowerCase().includes(needle)
      )
      .slice(0, 8);
  }, [catalog, courseQuery]);

  function patch<K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) {
    setProfile((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function save() {
    if (!profile) return;
    setSaving(true);
    try {
      const next = await updateMe({
        catalogYear: profile.catalogYear,
        remainingCredits: profile.remainingCredits,
        careerInterests: profile.careerInterests,
        programId: profile.programId ?? null,
        skills: profile.skills,
        courses: profile.courses,
        summary: profile.summary,
        studentType: profile.studentType,
        experiences: profile.experiences,
        education: profile.education,
        projects: profile.projects,
        languages: profile.languages,
        certifications: profile.certifications,
      });
      setProfile(normalizeProfile(next));
      toast.success("Profile saved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  function addCourse(course: CatalogCourse) {
    if (!profile) return;
    if (profile.courses.some((c) => c.code === course.code && c.status === status)) {
      toast.message(`${course.code} is already on the record with that status.`);
      return;
    }
    const [subject, courseNumber] = course.code.split(" ");
    const entry: CourseEntry = {
      subject,
      courseNumber,
      code: course.code,
      title: course.title,
      creditHours: course.credits_min ?? null,
      gradeLetter: status === "completed" ? grade : null,
      term,
      termSource: status === "in_progress" ? "Term" : "Period",
      status,
      level: course.level === "graduate" ? "G" : null,
    };
    patch("courses", [...profile.courses, entry]);
    setCourseQuery("");
  }

  function removeCourse(index: number) {
    if (!profile) return;
    patch(
      "courses",
      profile.courses.filter((_, i) => i !== index)
    );
  }

  async function onTranscript(file: File | undefined, input: HTMLInputElement) {
    if (!file) return;
    setImporting(true);
    try {
      const result = await importTranscript(file);
      input.value = "";
      if (!result.parsed) {
        toast.error(result.message);
        return;
      }
      setProfile(normalizeProfile(await getMe()));
      toast.success(result.message);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setImporting(false);
    }
  }

  async function onResume(file: File | undefined, input: HTMLInputElement) {
    if (!file) return;
    setResumeBusy(true);
    try {
      const result = await importResume(file);
      input.value = "";
      setProfile(normalizeProfile(await getMe()));
      toast.success(result.message);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Resume upload failed");
    } finally {
      setResumeBusy(false);
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState body={error} onRetry={load} />;
  if (!profile) {
    return (
      <EmptyState
        title="Sign in to open your profile"
        body="StudentOS uses the Google account you signed in with. There is no demo student to pick."
      />
    );
  }

  const majors = profile.majors?.length ? profile.majors : profile.major ? [profile.major] : [];
  const badges = profile.badges ?? [];
  const interestsText = profile.careerInterests.join(", ");

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
            Your profile
          </p>
          <h1 className="mt-2 font-heading text-3xl">{profile.displayName}</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            {profile.email ?? "Signed-in GVSU student"}. Degree and majors come from a Banner
            advising transcript. Resume details can be uploaded or entered by hand below. Uploads are
            read in memory and discarded.
          </p>
        </div>
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save profile"}
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Degree and majors</CardTitle>
            <CardDescription>
              Filled from Banner. Your name stays the Google sign-in name.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Name</p>
              <p className="font-heading text-lg">{profile.displayName}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Current degree</p>
              <p className="text-base">
                {profile.degreeLine || "Not on file yet — upload a transcript."}
              </p>
              {profile.transcriptLevel ? (
                <p className="text-muted-foreground">{profile.transcriptLevel}</p>
              ) : null}
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="program">Program for pathways / career path</Label>
              <select
                id="program"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                value={profile.programId ?? ""}
                onChange={(e) =>
                  patch(
                    "programId",
                    e.target.value === ""
                      ? null
                      : (e.target.value as StudentProfile["programId"])
                  )
                }
              >
                <option value="">Detect from transcript</option>
                <option value="applied-cs-ms">Applied Computer Science M.S.</option>
                <option value="cs-bs">Computer Science B.S.</option>
              </select>
              <p className="text-xs text-muted-foreground">
                Use this if Banner OCR missed the degree line. Career survey still needs a transcript
                upload first.
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Major</p>
              {majors.length ? (
                <ul className="mt-1 space-y-1">
                  {majors.map((major) => (
                    <li key={major}>{major}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">No major listed yet.</p>
              )}
            </div>
            {profile.college ? <p>{profile.college}</p> : null}
            <Separator />
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Banner badge</p>
              {badges.length ? (
                <ul className="mt-2 space-y-2">
                  {badges.map((badge) => (
                    <li key={badge.name} className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">{badge.kind}</Badge>
                      <span>{badge.name}</span>
                      {badge.awardedOn ? (
                        <span className="text-muted-foreground">Awarded {badge.awardedOn}</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-muted-foreground">
                  No post-baccalaureate badge on this transcript. If you earned one, it appears under
                  Awarded on the Banner advising PDF.
                </p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="year">Catalog year</Label>
                <Input
                  id="year"
                  value={profile.catalogYear ?? ""}
                  onChange={(e) => patch("catalogYear", e.target.value)}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="remaining">Remaining credits</Label>
                <Input
                  id="remaining"
                  type="number"
                  value={profile.remainingCredits ?? ""}
                  onChange={(e) =>
                    patch("remainingCredits", e.target.value === "" ? null : Number(e.target.value))
                  }
                />
              </div>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="interests">Career interests (comma separated)</Label>
              <Input
                id="interests"
                value={interestsText}
                onChange={(e) =>
                  patch(
                    "careerInterests",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                }
              />
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Transcript import</CardTitle>
              <CardDescription>
                Upload your own Banner advising PDF. The file is read, then thrown away.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <Alert>
                <FileUp />
                <AlertTitle>How to get the PDF from Banner</AlertTitle>
                <AlertDescription>
                  <ol className="mt-2 list-decimal space-y-1 pl-4 text-muted-foreground">
                    <li>
                      Open{" "}
                      <a
                        className="font-medium text-foreground underline-offset-2 hover:underline"
                        href="https://www.gvsu.edu/banner/"
                        target="_blank"
                        rel="noreferrer"
                      >
                        https://www.gvsu.edu/banner/
                      </a>
                    </li>
                    <li>Sign in with your GVSU email and password (on Banner, not in StudentOS).</li>
                    <li>Choose Student, then Student Records, then View Academic Transcript.</li>
                    <li>
                      Select Transcript Level (Undergraduate or Masters) and Transcript Type (Advising).
                    </li>
                    <li>Print the page and save it as a PDF. Name it whatever you like.</li>
                    <li>Upload that PDF here.</li>
                  </ol>
                </AlertDescription>
              </Alert>
              <div className="grid gap-1.5">
                <Label htmlFor="transcript">PDF file</Label>
                <Input
                  id="transcript"
                  type="file"
                  accept="application/pdf,.pdf"
                  disabled={importing}
                  onChange={(e) => onTranscript(e.target.files?.[0], e.currentTarget)}
                />
              </div>
              {importing ? (
                <p className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  Reading the transcript. The file is not being saved.
                </p>
              ) : (
                <p className="text-muted-foreground">
                  Completed, in-progress, and still-needed catalog courses are listed below.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resume</CardTitle>
              <CardDescription>
                Upload a PDF, Word, or text resume. StudentOS extracts experience, projects, skills,
                education, and languages into the sections below, then discards the file. You can also
                skip the upload and enter everything manually.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <Alert>
                <FileText />
                <AlertTitle>How to upload a resume</AlertTitle>
                <AlertDescription>
                  Prefer a text-based PDF or .docx. Scanned PDFs are OCR’d when needed. Different
                  layouts are supported when sections use common headings (Experience, Projects,
                  Skills). The file is not stored on this PC’s StudentOS folder or in git.
                </AlertDescription>
              </Alert>
              <div className="grid gap-1.5">
                <Label htmlFor="resume">Resume file</Label>
                <Input
                  id="resume"
                  type="file"
                  accept="application/pdf,.pdf,.doc,.docx,.txt,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  disabled={resumeBusy}
                  onChange={(e) => onResume(e.target.files?.[0], e.currentTarget)}
                />
              </div>
              {resumeBusy ? (
                <p className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  Reading and parsing the resume. The file is not being saved.
                </p>
              ) : profile.resumeFilename ? (
                <div className="space-y-1">
                  <p>
                    Last resume read: <span className="font-medium">{profile.resumeFilename}</span>
                    <span className="text-muted-foreground"> · file discarded</span>
                  </p>
                  {profile.resumeParsed?.method ? (
                    <p className="text-muted-foreground">
                      Extracted via {profile.resumeParsed.method}
                      {(profile.experiences?.length || 0) +
                        (profile.projects?.length || 0) +
                        (profile.skills?.length || 0) >
                      0
                        ? ` · ${(profile.experiences || []).length} experience(s), ${(profile.projects || []).length} project(s), ${(profile.skills || []).length} skill(s)`
                        : ""}
                    </p>
                  ) : null}
                  {(profile.resumeParsed?.warnings || []).length ? (
                    <ul className="list-disc pl-4 text-muted-foreground">
                      {profile.resumeParsed!.warnings!.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : (
                <p className="text-muted-foreground">
                  No resume read yet. Upload one, or fill the resume sections below by hand.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <ResumeProfileSections profile={profile} onChange={patch} />

      <Card>
        <CardHeader>
          <CardTitle>Coursework</CardTitle>
          <CardDescription>
            Join key is catalog code. Completed rows keep a letter grade for the later ≥ 2.0 rule.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="md:col-span-2">
              <Label>Add from catalog</Label>
              <Input
                placeholder="Type CIS 353 or Database"
                value={courseQuery}
                onChange={(e) => setCourseQuery(e.target.value)}
              />
            </div>
            <div>
              <Label>Status</Label>
              <select
                className="mt-0 h-8 w-full rounded-lg border border-input bg-transparent px-2 text-sm"
                value={status}
                onChange={(e) => setStatus(e.target.value as CourseEntry["status"])}
              >
                <option value="completed">Completed</option>
                <option value="in_progress">In progress</option>
                <option value="planned">Planned</option>
              </select>
            </div>
            <div>
              <Label>Term / grade</Label>
              <div className="flex gap-2">
                <Input value={term} onChange={(e) => setTerm(e.target.value)} />
                <Input
                  className="w-16"
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  disabled={status !== "completed"}
                />
              </div>
            </div>
          </div>
          {matches.length > 0 ? (
            <ul className="divide-y rounded-lg border">
              {matches.map((course) => (
                <li key={course.code} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                  <span>
                    <span className="font-mono text-xs">{course.code}</span> {course.title}
                  </span>
                  <Button type="button" size="sm" variant="outline" onClick={() => addCourse(course)}>
                    Add
                  </Button>
                </li>
              ))}
            </ul>
          ) : courseQuery.trim().length >= 2 ? (
            <p className="text-sm text-muted-foreground">No catalog match for “{courseQuery}”.</p>
          ) : null}

          <Separator />

          {profile.courses.length === 0 ? (
            <EmptyState
              title="No courses on this record"
              body="Upload a Banner advising transcript, or search the ingested CIS catalog above."
            />
          ) : (
            <div className="space-y-6">
              <CourseGroup
                title="Completed"
                empty="No completed courses on this record."
                rows={profile.courses
                  .map((row, index) => ({ row, index }))
                  .filter(({ row }) => row.status === "completed")}
                onRemove={removeCourse}
              />
              <CourseGroup
                title="In progress"
                empty="No in-progress courses. Banner lists these under Course(s) in Progress."
                rows={profile.courses
                  .map((row, index) => ({ row, index }))
                  .filter(({ row }) => row.status === "in_progress")}
                onRemove={removeCourse}
              />
              <CourseGroup
                title="Still needed"
                empty="No remaining required catalog courses. Electives are not listed as required."
                rows={profile.courses
                  .map((row, index) => ({ row, index }))
                  .filter(({ row }) => row.status === "planned")}
                onRemove={removeCourse}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CourseGroup({
  title,
  empty,
  rows,
  onRemove,
}: {
  title: string;
  empty: string;
  rows: { row: CourseEntry; index: number }[];
  onRemove: (index: number) => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <h3 className="font-heading text-base">{title}</h3>
        <p className="text-xs text-muted-foreground">{rows.length}</p>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr>
                <th className="py-2 pr-3">Code</th>
                <th className="py-2 pr-3">Title</th>
                <th className="py-2 pr-3">Term</th>
                <th className="py-2 pr-3">Grade</th>
                <th className="py-2 pr-3">Cr</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map(({ row, index }) => (
                <tr key={`${row.code}-${row.status}-${index}`} className="border-t">
                  <td className="py-2 pr-3 font-mono text-xs">{row.code}</td>
                  <td className="py-2 pr-3">{row.title}</td>
                  <td className="py-2 pr-3">{row.term ?? "—"}</td>
                  <td className="py-2 pr-3">{row.gradeLetter ?? "—"}</td>
                  <td className="py-2 pr-3">{row.creditHours ?? "—"}</td>
                  <td className="py-2">
                    <Button type="button" size="xs" variant="ghost" onClick={() => onRemove(index)}>
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
