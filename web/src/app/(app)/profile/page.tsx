"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import {
  createDemoProfile,
  getCourses,
  getProfile,
  getSession,
  importTranscript,
  updateProfile,
} from "@/lib/api";
import type { CatalogCourse, CourseEntry, StudentProfile } from "@/lib/types";

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

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const session = await getSession();
      const [courses, p] = await Promise.all([
        getCourses(),
        session.activeProfileId ? getProfile(session.activeProfileId) : Promise.resolve(null),
      ]);
      setCatalog(courses.courses);
      setProfile(p);
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
      const next = await updateProfile(profile.syntheticId, {
        displayName: profile.displayName,
        transcriptLevel: profile.transcriptLevel,
        college: profile.college,
        degreeLine: profile.degreeLine,
        major: profile.major,
        catalogYear: profile.catalogYear,
        remainingCredits: profile.remainingCredits,
        careerInterests: profile.careerInterests,
        skills: profile.skills,
        courses: profile.courses,
        summary: profile.summary,
      });
      setProfile(next);
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

  async function onTranscript(file: File | undefined) {
    if (!file) return;
    try {
      const result = await importTranscript(file);
      toast.message(result.message);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    }
  }

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState body={error} onRetry={load} />;
  if (!profile) {
    return (
      <EmptyState
        title="No profile in this identity slot"
        body="Create a local demo profile. This is not a GVSU account."
        action={
          <Button
            onClick={async () => {
              setProfile(await createDemoProfile());
            }}
          >
            Create demo profile
          </Button>
        }
      />
    );
  }

  const interestsText = profile.careerInterests.join(", ");

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
            Capability 1
          </p>
          <h1 className="mt-2 font-heading text-3xl">Academic profile</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Banner-shaped fields (level, college, major, course rows with letter grades). No names,
            student IDs, or GPAs from a real transcript belong here.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={async () => {
              const created = await createDemoProfile();
              setProfile(created);
              toast.success("Demo profile reset to empty");
            }}
          >
            Reset demo profile
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save profile"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Program</CardTitle>
            <CardDescription>{profile.syntheticId}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="displayName">Display name</Label>
              <Input
                id="displayName"
                value={profile.displayName}
                onChange={(e) => patch("displayName", e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="level">Transcript level</Label>
              <select
                id="level"
                className="h-8 rounded-lg border border-input bg-transparent px-2 text-sm"
                value={profile.transcriptLevel}
                onChange={(e) => {
                  const level = e.target.value as StudentProfile["transcriptLevel"];
                  patch("transcriptLevel", level);
                  if (level === "Masters") {
                    patch("degreeLine", "Master of Science");
                    patch("major", "Applied Computer Science");
                  } else {
                    patch("degreeLine", "Bachelor of Science");
                    patch("major", "Computer Science");
                  }
                }}
              >
                <option value="Undergraduate">Undergraduate</option>
                <option value="Masters">Masters</option>
              </select>
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="college">College</Label>
              <Input
                id="college"
                value={profile.college ?? ""}
                onChange={(e) => patch("college", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="degree">Degree line</Label>
                <Input
                  id="degree"
                  value={profile.degreeLine ?? ""}
                  onChange={(e) => patch("degreeLine", e.target.value)}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="major">Major</Label>
                <Input
                  id="major"
                  value={profile.major ?? ""}
                  onChange={(e) => patch("major", e.target.value)}
                />
              </div>
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
                    patch(
                      "remainingCredits",
                      e.target.value === "" ? null : Number(e.target.value)
                    )
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
            <div className="grid gap-1.5">
              <Label htmlFor="skills">Self-reported skills (comma separated)</Label>
              <Input
                id="skills"
                value={profile.skills.map((s) => s.label).join(", ")}
                onChange={(e) =>
                  patch(
                    "skills",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                      .map((label) => ({ label, evidence: "self_report" as const }))
                  )
                }
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Transcript import</CardTitle>
            <CardDescription>
              Banner advising PDF is accepted locally and discarded. Parsing is stubbed in this slice.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => onTranscript(e.target.files?.[0])}
            />
            <p className="text-muted-foreground">
              Map courses below using catalog codes (Subject + 3-digit number). Do not paste names,
              G-numbers, or GPA lines into this form.
            </p>
          </CardContent>
        </Card>
      </div>

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
              body="Search the ingested CIS catalog above, or switch to synth-bs-data-eng to see a filled Data Engineer example."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted-foreground">
                  <tr>
                    <th className="py-2 pr-3">Code</th>
                    <th className="py-2 pr-3">Title</th>
                    <th className="py-2 pr-3">Status</th>
                    <th className="py-2 pr-3">Term</th>
                    <th className="py-2 pr-3">Grade</th>
                    <th className="py-2 pr-3">Cr</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {profile.courses.map((row, index) => (
                    <tr key={`${row.code}-${row.status}-${index}`} className="border-t">
                      <td className="py-2 pr-3 font-mono text-xs">{row.code}</td>
                      <td className="py-2 pr-3">{row.title}</td>
                      <td className="py-2 pr-3">
                        <Badge variant="outline">{row.status.replace("_", " ")}</Badge>
                      </td>
                      <td className="py-2 pr-3">{row.term}</td>
                      <td className="py-2 pr-3">{row.gradeLetter ?? "—"}</td>
                      <td className="py-2 pr-3">{row.creditHours ?? "—"}</td>
                      <td className="py-2">
                        <Button type="button" size="xs" variant="ghost" onClick={() => removeCourse(index)}>
                          Remove
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
