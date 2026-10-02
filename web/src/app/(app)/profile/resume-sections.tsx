"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import type {
  EducationEntry,
  ExperienceEntry,
  LanguageEntry,
  ProjectEntry,
  StudentProfile,
} from "@/lib/types";

type Props = {
  profile: StudentProfile;
  onChange: <K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) => void;
};

function dateLine(start?: string | null, end?: string | null, current?: boolean) {
  if (!start && !end && !current) return null;
  if (current) return `${start || "Started"} – Present`;
  if (start && end) return `${start} – ${end}`;
  return start || end || null;
}

export function ResumeProfileSections({ profile, onChange }: Props) {
  const experiences = profile.experiences ?? [];
  const projects = profile.projects ?? [];
  const education = profile.education ?? [];
  const languages = profile.languages ?? [];
  const skills = profile.skills ?? [];
  const certifications = profile.certifications ?? [];

  function updateExperience(index: number, patch: Partial<ExperienceEntry>) {
    onChange(
      "experiences",
      experiences.map((row, i) => (i === index ? { ...row, ...patch } : row))
    );
  }
  function updateProject(index: number, patch: Partial<ProjectEntry>) {
    onChange(
      "projects",
      projects.map((row, i) => (i === index ? { ...row, ...patch } : row))
    );
  }
  function updateEducation(index: number, patch: Partial<EducationEntry>) {
    onChange(
      "education",
      education.map((row, i) => (i === index ? { ...row, ...patch } : row))
    );
  }
  function updateLanguage(index: number, patch: Partial<LanguageEntry>) {
    onChange(
      "languages",
      languages.map((row, i) => (i === index ? { ...row, ...patch } : row))
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>About you</CardTitle>
          <CardDescription>
            From your resume when possible. Edit freely, or fill this in by hand if you skip the upload.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="grid gap-1.5">
            <Label htmlFor="summary">Summary</Label>
            <textarea
              id="summary"
              className="min-h-24 w-full rounded-lg border bg-background px-3 py-2 text-sm"
              value={profile.summary ?? ""}
              onChange={(e) => onChange("summary", e.target.value || null)}
              placeholder="Short professional summary"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="studentType">Student residency</Label>
            <select
              id="studentType"
              className="h-9 rounded-lg border bg-background px-3 text-sm"
              value={profile.studentType ?? ""}
              onChange={(e) =>
                onChange(
                  "studentType",
                  (e.target.value || null) as StudentProfile["studentType"]
                )
              }
            >
              <option value="">Not specified</option>
              <option value="international">International student</option>
              <option value="domestic">Domestic / local student</option>
              <option value="unknown">Prefer not to say</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Resumes rarely state this clearly. Choose the option that fits you.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>Work experience</CardTitle>
            <CardDescription>Jobs, internships, and roles — title, place, and dates.</CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              onChange("experiences", [
                ...experiences,
                {
                  organization: "",
                  title: "",
                  location: "",
                  startDate: "",
                  endDate: "",
                  current: false,
                  summary: "",
                  highlights: [],
                  source: "manual",
                },
              ])
            }
          >
            Add experience
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {experiences.length === 0 ? (
            <p className="text-sm text-muted-foreground">No experience on file yet.</p>
          ) : (
            experiences.map((row, index) => (
              <div key={`exp-${index}`} className="space-y-3 rounded-lg border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-muted-foreground">
                    {dateLine(row.startDate, row.endDate, row.current) || "Dates not set"}
                    {row.source === "resume" ? " · from resume" : ""}
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      onChange(
                        "experiences",
                        experiences.filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove
                  </Button>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="grid gap-1.5">
                    <Label>Title / position</Label>
                    <Input
                      value={row.title}
                      onChange={(e) => updateExperience(index, { title: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Organization</Label>
                    <Input
                      value={row.organization}
                      onChange={(e) => updateExperience(index, { organization: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Location</Label>
                    <Input
                      value={row.location ?? ""}
                      onChange={(e) => updateExperience(index, { location: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="grid gap-1.5">
                      <Label>Start</Label>
                      <Input
                        value={row.startDate ?? ""}
                        onChange={(e) => updateExperience(index, { startDate: e.target.value })}
                        placeholder="May 2024"
                      />
                    </div>
                    <div className="grid gap-1.5">
                      <Label>End</Label>
                      <Input
                        value={row.current ? "Present" : row.endDate ?? ""}
                        disabled={!!row.current}
                        onChange={(e) => updateExperience(index, { endDate: e.target.value })}
                        placeholder="Aug 2024"
                      />
                    </div>
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!row.current}
                    onChange={(e) =>
                      updateExperience(index, {
                        current: e.target.checked,
                        endDate: e.target.checked ? null : row.endDate,
                      })
                    }
                  />
                  Currently working here
                </label>
                <div className="grid gap-1.5">
                  <Label>Highlights / description</Label>
                  <textarea
                    className="min-h-20 w-full rounded-lg border bg-background px-3 py-2 text-sm"
                    value={row.summary ?? (row.highlights || []).join("\n")}
                    onChange={(e) => updateExperience(index, { summary: e.target.value })}
                  />
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>Education</CardTitle>
            <CardDescription>Colleges and degrees from the resume, editable here.</CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              onChange("education", [
                ...education,
                {
                  institution: "",
                  degree: "",
                  field: "",
                  startDate: "",
                  endDate: "",
                  current: false,
                  source: "manual",
                },
              ])
            }
          >
            Add education
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {education.length === 0 ? (
            <p className="text-sm text-muted-foreground">No education rows yet.</p>
          ) : (
            education.map((row, index) => (
              <div key={`edu-${index}`} className="space-y-3 rounded-lg border p-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      onChange(
                        "education",
                        education.filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove
                  </Button>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="grid gap-1.5">
                    <Label>Institution / college</Label>
                    <Input
                      value={row.institution}
                      onChange={(e) => updateEducation(index, { institution: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Degree</Label>
                    <Input
                      value={row.degree ?? ""}
                      onChange={(e) => updateEducation(index, { degree: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Field</Label>
                    <Input
                      value={row.field ?? ""}
                      onChange={(e) => updateEducation(index, { field: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="grid gap-1.5">
                      <Label>Start</Label>
                      <Input
                        value={row.startDate ?? ""}
                        onChange={(e) => updateEducation(index, { startDate: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-1.5">
                      <Label>End</Label>
                      <Input
                        value={row.current ? "Present" : row.endDate ?? ""}
                        disabled={!!row.current}
                        onChange={(e) => updateEducation(index, { endDate: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!row.current}
                    onChange={(e) =>
                      updateEducation(index, {
                        current: e.target.checked,
                        endDate: e.target.checked ? null : row.endDate,
                      })
                    }
                  />
                  Currently enrolled
                </label>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>Projects</CardTitle>
            <CardDescription>Personal, academic, or work projects and the tools used.</CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() =>
              onChange("projects", [
                ...projects,
                {
                  name: "",
                  summary: "",
                  technologies: [],
                  demonstratesSkills: [],
                  source: "manual",
                },
              ])
            }
          >
            Add project
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {projects.length === 0 ? (
            <p className="text-sm text-muted-foreground">No projects on file yet.</p>
          ) : (
            projects.map((row, index) => (
              <div key={`proj-${index}`} className="space-y-3 rounded-lg border p-3">
                <div className="flex justify-end">
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      onChange(
                        "projects",
                        projects.filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove
                  </Button>
                </div>
                <div className="grid gap-1.5">
                  <Label>Project name</Label>
                  <Input
                    value={row.name}
                    onChange={(e) => updateProject(index, { name: e.target.value })}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label>Summary</Label>
                  <textarea
                    className="min-h-20 w-full rounded-lg border bg-background px-3 py-2 text-sm"
                    value={row.summary ?? ""}
                    onChange={(e) => updateProject(index, { summary: e.target.value })}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label>Technologies (comma separated)</Label>
                  <Input
                    value={(row.technologies || []).join(", ")}
                    onChange={(e) =>
                      updateProject(index, {
                        technologies: e.target.value
                          .split(",")
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <CardTitle>Technical skills</CardTitle>
              <CardDescription>Languages, tools, and frameworks.</CardDescription>
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                const label = window.prompt("Skill name");
                if (!label?.trim()) return;
                onChange("skills", [
                  ...skills,
                  { label: label.trim(), evidence: "self_report" },
                ]);
              }}
            >
              Add skill
            </Button>
          </CardHeader>
          <CardContent>
            {skills.length === 0 ? (
              <p className="text-sm text-muted-foreground">No skills listed yet.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, index) => (
                  <Badge key={`${skill.label}-${index}`} variant="secondary" className="gap-1">
                    {skill.label}
                    <button
                      type="button"
                      className="ml-1 text-xs opacity-70 hover:opacity-100"
                      onClick={() =>
                        onChange(
                          "skills",
                          skills.filter((_, i) => i !== index)
                        )
                      }
                      aria-label={`Remove ${skill.label}`}
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <CardTitle>Languages</CardTitle>
              <CardDescription>Spoken / written languages.</CardDescription>
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() =>
                onChange("languages", [
                  ...languages,
                  { name: "", proficiency: "", source: "manual" },
                ])
              }
            >
              Add language
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {languages.length === 0 ? (
              <p className="text-sm text-muted-foreground">No languages listed yet.</p>
            ) : (
              languages.map((row, index) => (
                <div key={`lang-${index}`} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
                  <div className="grid gap-1.5">
                    <Label>Language</Label>
                    <Input
                      value={row.name}
                      onChange={(e) => updateLanguage(index, { name: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Proficiency</Label>
                    <Input
                      value={row.proficiency ?? ""}
                      onChange={(e) => updateLanguage(index, { proficiency: e.target.value })}
                      placeholder="Fluent"
                    />
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      onChange(
                        "languages",
                        languages.filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle>Certifications</CardTitle>
            <CardDescription>Optional certifications from the resume or entered by hand.</CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              const name = window.prompt("Certification name");
              if (!name?.trim()) return;
              onChange("certifications", [
                ...certifications,
                { name: name.trim(), taggedSkills: [], source: "manual" },
              ]);
            }}
          >
            Add certification
          </Button>
        </CardHeader>
        <CardContent>
          {certifications.length === 0 ? (
            <p className="text-sm text-muted-foreground">No certifications listed yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {certifications.map((row, index) => (
                <li key={`${row.name}-${index}`} className="flex items-center justify-between gap-3">
                  <span>{row.name}</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      onChange(
                        "certifications",
                        certifications.filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
