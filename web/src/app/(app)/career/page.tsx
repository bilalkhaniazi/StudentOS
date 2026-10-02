"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle2, Circle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import {
  courseHref,
  getCareerPath,
  getMe,
  setMyCareer,
  submitCareerSurvey,
} from "@/lib/api";
import type {
  CareerPathPayload,
  CareerRanking,
  CareerSurveyAnswers,
  StudentProfile,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const WORK_STYLES = [
  { id: "data-systems", label: "Building data systems" },
  { id: "cloud-ops", label: "Operating cloud infrastructure" },
  { id: "product-features", label: "Shipping product features / APIs" },
  { id: "models", label: "Experimenting with models" },
] as const;

const TOOLS = [
  { id: "sql", label: "SQL" },
  { id: "python", label: "Python" },
  { id: "spark", label: "Spark / Kafka" },
  { id: "docker", label: "Docker / Kubernetes" },
  { id: "aws", label: "AWS / Azure" },
  { id: "apis", label: "APIs / React" },
  { id: "java", label: "Java / C#" },
  { id: "pytorch", label: "PyTorch / TensorFlow" },
] as const;

const HORIZONS = [
  { id: "internship", label: "Internship soon" },
  { id: "first-role", label: "First role after graduation" },
  { id: "pivot", label: "Already employed, pivoting" },
] as const;

const CONSTRAINTS = [
  { id: "remote", label: "Prefer remote-friendly" },
  { id: "open", label: "Open to any arrangement" },
] as const;

const GAP_STYLE: Record<string, string> = {
  strong: "bg-emerald-100 text-emerald-900",
  moderate: "bg-sky-100 text-sky-900",
  weak: "bg-amber-100 text-amber-950",
  missing: "bg-rose-100 text-rose-950",
};

const emptyAnswers = (): CareerSurveyAnswers => ({
  interestData: 3,
  interestCloud: 3,
  interestBackend: 3,
  interestMl: 3,
  workStyle: null,
  tools: [],
  horizon: null,
  constraint: null,
});

function InterestScale({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <Label>{label}</Label>
        <span className="text-sm tabular-nums text-muted-foreground">{value} / 5</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {[0, 1, 2, 3, 4, 5].map((n) => (
          <Button
            key={n}
            type="button"
            size="sm"
            variant={value === n ? "default" : "outline"}
            onClick={() => onChange(n)}
          >
            {n}
          </Button>
        ))}
      </div>
    </div>
  );
}

function RankingCard({
  row,
  selected,
  busy,
  onChoose,
}: {
  row: CareerRanking;
  selected: boolean;
  busy: boolean;
  onChoose: () => void;
}) {
  return (
    <Card className={cn(row.recommended && "ring-2 ring-primary", selected && "border-primary")}>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="font-heading text-xl">{row.label ?? row.careerId}</CardTitle>
            <CardDescription className="mt-1">{row.summary}</CardDescription>
          </div>
          <div className="text-right">
            <p className="font-heading text-3xl tabular-nums">{row.match}%</p>
            <p className="text-xs text-muted-foreground">Match</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {row.recommended ? <Badge>Recommended</Badge> : null}
          {row.yourInterest ? <Badge variant="secondary">Your interest</Badge> : null}
          {selected ? <Badge variant="outline">Your target</Badge> : null}
        </div>
        {row.reason ? <p className="text-sm text-muted-foreground">{row.reason}</p> : null}
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-4 gap-2 text-center text-xs">
          {(
            [
              ["S", row.factors.S, "Skills"],
              ["C", row.factors.C, "Courses"],
              ["P", row.factors.P, "Projects"],
              ["K", row.factors.K, "Certs"],
            ] as const
          ).map(([key, val, name]) => (
            <div key={key} className="rounded-md border px-2 py-2">
              <dt className="font-medium">
                {key} · {name}
              </dt>
              <dd className="mt-1 tabular-nums text-muted-foreground">{Math.round(val * 100)}%</dd>
            </div>
          ))}
        </dl>
        <Button type="button" variant={selected ? "secondary" : "default"} disabled={busy} onClick={onChoose}>
          {selected ? "Selected path" : "Choose this path"}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function CareerPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [path, setPath] = useState<CareerPathPayload | null>(null);
  const [answers, setAnswers] = useState<CareerSurveyAnswers>(emptyAnswers);
  const [submitting, setSubmitting] = useState(false);
  const [savingCareer, setSavingCareer] = useState<string | null>(null);
  const [showSurvey, setShowSurvey] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [p, payload] = await Promise.all([getMe(), getCareerPath()]);
      setProfile(p);
      setPath(payload);
      if (payload.survey?.answers) {
        setAnswers({ ...emptyAnswers(), ...payload.survey.answers, tools: payload.survey.answers.tools ?? [] });
        setShowSurvey(false);
      } else {
        setShowSurvey(payload.ready);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load career guidance.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const selectedId = useMemo(
    () => path?.selectedCareerId || path?.recommendedCareerId || null,
    [path]
  );

  async function runSurvey(confirmCareerId?: string | null) {
    setSubmitting(true);
    try {
      const next = await submitCareerSurvey(answers, confirmCareerId);
      setPath(next);
      setShowSurvey(false);
      setProfile(await getMe());
      toast.success(confirmCareerId ? "Career path saved" : "Survey scored — pick or confirm a path");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Survey failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function chooseCareer(careerId: string) {
    setSavingCareer(careerId);
    try {
      if (path?.survey?.answers) {
        const next = await submitCareerSurvey(
          { ...emptyAnswers(), ...path.survey.answers, tools: path.survey.answers.tools ?? [] },
          careerId
        );
        setPath(next);
      } else {
        await setMyCareer(careerId);
        setPath(await getCareerPath());
      }
      setProfile(await getMe());
      toast.success("Target career updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save career");
    } finally {
      setSavingCareer(null);
    }
  }

  function toggleTool(id: string) {
    setAnswers((prev) => ({
      ...prev,
      tools: prev.tools.includes(id) ? prev.tools.filter((t) => t !== id) : [...prev.tools, id],
    }));
  }

  if (loading) return <Skeleton className="h-64 w-full" />;
  if (error) return <ErrorState body={error} onRetry={load} />;
  if (!profile || !path) {
    return (
      <EmptyState
        title="Sign in to open Career"
        body="StudentOS opens your own profile after Google sign-in."
      />
    );
  }

  const gateOk = path.ready && path.gate.transcriptPresent;
  const activePath = path.path;
  const focusRanking =
    path.rankings.find((r) => r.careerId === selectedId) || path.rankings[0] || null;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
          Career guidance
        </p>
        <h1 className="mt-2 font-heading text-3xl">Find your path</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Approximate Match % from your transcript, resume signals, and a short preference survey.
          Advising aid only — not job placement or official SIS.
        </p>
      </div>

      {!gateOk ? (
        <Card>
          <CardHeader>
            <CardTitle>Before the survey</CardTitle>
            <CardDescription>
              Upload a Banner advising transcript on Profile. Zero courses is fine — we still need
              degree or program context.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 size-4 text-emerald-600" />
                <span>Signed in as {profile.displayName}</span>
              </li>
              <li className="flex items-start gap-2">
                <Circle className="mt-0.5 size-4 text-muted-foreground" />
                <span>
                  Banner transcript not on file yet.{" "}
                  <Link className="underline underline-offset-2" href="/profile">
                    Go to Profile
                  </Link>
                </span>
              </li>
              <li className="flex items-start gap-2">
                {path.evidence.hasResumeSignal ? (
                  <CheckCircle2 className="mt-0.5 size-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="mt-0.5 size-4 text-amber-600" />
                )}
                <span>
                  Resume skills / projects / experience — recommended, not required.
                  {!path.evidence.hasResumeSignal ? (
                    <>
                      {" "}
                      <Link className="underline underline-offset-2" href="/profile">
                        Add on Profile
                      </Link>
                    </>
                  ) : null}
                </span>
              </li>
            </ul>
            {path.warnings.map((w) => (
              <Alert key={w}>
                <AlertTitle>Note</AlertTitle>
                <AlertDescription>{w}</AlertDescription>
              </Alert>
            ))}
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Your evidence</CardTitle>
              <CardDescription>
                Read-only snapshot StudentOS uses for Match %. Resume is optional.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
              <div className="rounded-md border px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Courses done</p>
                <p className="mt-1 font-heading text-2xl tabular-nums">{path.evidence.courseCompleted}</p>
              </div>
              <div className="rounded-md border px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">In progress</p>
                <p className="mt-1 font-heading text-2xl tabular-nums">{path.evidence.courseInProgress}</p>
              </div>
              <div className="rounded-md border px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Skills / projects</p>
                <p className="mt-1 font-heading text-2xl tabular-nums">
                  {path.evidence.skills} / {path.evidence.projects}
                </p>
              </div>
              <div className="rounded-md border px-3 py-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Experience</p>
                <p className="mt-1 font-heading text-2xl tabular-nums">{path.evidence.experiences}</p>
              </div>
            </CardContent>
          </Card>

          {path.gate.needsProgramPick || !path.gate.programId ? (
            <Alert>
              <AlertTitle>Pick your program on Profile</AlertTitle>
              <AlertDescription>
                Degree line was unclear. Choose Applied CS M.S. or Computer Science B.S. so the path
                sketch can load.{" "}
                <Link className="underline underline-offset-2" href="/profile">
                  Open Profile
                </Link>
              </AlertDescription>
            </Alert>
          ) : null}

          {path.warnings.map((w) => (
            <Alert key={w}>
              <AlertTriangle />
              <AlertTitle>Recommended</AlertTitle>
              <AlertDescription>{w}</AlertDescription>
            </Alert>
          ))}

          {showSurvey || !path.survey ? (
            <Card>
              <CardHeader>
                <CardTitle>Preference survey</CardTitle>
                <CardDescription>
                  Interests tip rankings only when evidence is close. They never invent Match %.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-8">
                <div className="grid gap-6 md:grid-cols-2">
                  <InterestScale
                    label="Data pipelines / databases"
                    value={answers.interestData}
                    onChange={(n) => setAnswers((a) => ({ ...a, interestData: n }))}
                  />
                  <InterestScale
                    label="Cloud & infrastructure"
                    value={answers.interestCloud}
                    onChange={(n) => setAnswers((a) => ({ ...a, interestCloud: n }))}
                  />
                  <InterestScale
                    label="Backend APIs & services"
                    value={answers.interestBackend}
                    onChange={(n) => setAnswers((a) => ({ ...a, interestBackend: n }))}
                  />
                  <InterestScale
                    label="ML / analytics models"
                    value={answers.interestMl}
                    onChange={(n) => setAnswers((a) => ({ ...a, interestMl: n }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Preferred work style</Label>
                  <div className="flex flex-wrap gap-2">
                    {WORK_STYLES.map((opt) => (
                      <Button
                        key={opt.id}
                        type="button"
                        size="sm"
                        variant={answers.workStyle === opt.id ? "default" : "outline"}
                        onClick={() => setAnswers((a) => ({ ...a, workStyle: opt.id }))}
                      >
                        {opt.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Tools you enjoy</Label>
                  <div className="flex flex-wrap gap-2">
                    {TOOLS.map((opt) => (
                      <Button
                        key={opt.id}
                        type="button"
                        size="sm"
                        variant={answers.tools.includes(opt.id) ? "default" : "outline"}
                        onClick={() => toggleTool(opt.id)}
                      >
                        {opt.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Horizon</Label>
                    <div className="flex flex-wrap gap-2">
                      {HORIZONS.map((opt) => (
                        <Button
                          key={opt.id}
                          type="button"
                          size="sm"
                          variant={answers.horizon === opt.id ? "default" : "outline"}
                          onClick={() => setAnswers((a) => ({ ...a, horizon: opt.id }))}
                        >
                          {opt.label}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Constraint (note only)</Label>
                    <div className="flex flex-wrap gap-2">
                      {CONSTRAINTS.map((opt) => (
                        <Button
                          key={opt.id}
                          type="button"
                          size="sm"
                          variant={answers.constraint === opt.id ? "default" : "outline"}
                          onClick={() => setAnswers((a) => ({ ...a, constraint: opt.id }))}
                        >
                          {opt.label}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button type="button" disabled={submitting} onClick={() => runSurvey(null)}>
                    {submitting ? "Scoring…" : "See Match % rankings"}
                  </Button>
                  {path.survey ? (
                    <Button type="button" variant="ghost" onClick={() => setShowSurvey(false)}>
                      Cancel
                    </Button>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">
                Survey answered
                {path.survey.answeredAt
                  ? ` · ${new Date(path.survey.answeredAt).toLocaleString()}`
                  : ""}
              </p>
              <Button type="button" variant="outline" onClick={() => setShowSurvey(true)}>
                Retake survey
              </Button>
            </div>
          )}

          {path.rankings.length ? (
            <section className="space-y-4">
              <div>
                <h2 className="font-heading text-2xl">Ranked careers</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Evidence leads. Confirm a path or override to another career.
                </p>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                {path.rankings.map((row) => (
                  <RankingCard
                    key={row.careerId}
                    row={row}
                    selected={profile.targetCareer === row.careerId}
                    busy={savingCareer === row.careerId || submitting}
                    onChoose={() => chooseCareer(row.careerId)}
                  />
                ))}
              </div>
            </section>
          ) : null}

          {focusRanking ? (
            <section className="space-y-4">
              <div>
                <h2 className="font-heading text-2xl">
                  Skills to develop · {focusRanking.label ?? focusRanking.careerId}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Gap labels from coursework, projects, certifications, and self-reported skills.
                </p>
              </div>
              <ul className="divide-y overflow-hidden rounded-lg border">
                {focusRanking.skills.map((skill) => (
                  <li
                    key={skill.id}
                    className="flex flex-col gap-1 px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium">{skill.label}</p>
                      <p className="text-xs text-muted-foreground">
                        Demand {skill.demand}
                        {skill.sources.length
                          ? ` · evidence: ${skill.sources.join(", ")}`
                          : " · no evidence yet"}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "inline-flex w-fit rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                        GAP_STYLE[skill.gap] || "bg-muted"
                      )}
                    >
                      {skill.gap}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {activePath ? (
            <section className="space-y-4">
              <div>
                <h2 className="font-heading text-2xl">Complete path sketch</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {activePath.note ||
                    "Degree buckets plus career lean. Next-semester packing comes later."}
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {activePath.buckets.map((bucket) => (
                  <Card key={bucket.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between gap-2">
                        <CardTitle className="text-lg">{bucket.title}</CardTitle>
                        <Badge variant="secondary" className="capitalize">
                          {bucket.status}
                        </Badge>
                      </div>
                      {bucket.detail ? <CardDescription>{bucket.detail}</CardDescription> : null}
                    </CardHeader>
                    {(bucket.options?.length || bucket.openAreas?.length) ? (
                      <CardContent className="space-y-2 text-sm">
                        {bucket.options?.map((opt) => (
                          <p key={opt.id || opt.code || opt.name}>
                            {opt.code ? (
                              <Link className="underline underline-offset-2" href={courseHref(opt.code)}>
                                {opt.code}
                              </Link>
                            ) : null}{" "}
                            {opt.title || opt.name}
                          </p>
                        ))}
                        {bucket.openAreas?.map((area) => (
                          <div key={area.area}>
                            <p className="font-medium capitalize">{area.area}</p>
                            <ul className="mt-1 space-y-1 text-muted-foreground">
                              {area.options.slice(0, 4).map((opt) => (
                                <li key={opt.code}>
                                  {opt.code ? (
                                    <Link
                                      className="underline underline-offset-2"
                                      href={courseHref(opt.code)}
                                    >
                                      {opt.code}
                                    </Link>
                                  ) : null}{" "}
                                  {opt.title}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </CardContent>
                    ) : null}
                  </Card>
                ))}
              </div>

              {activePath.suggestedCourses.length ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Suggested courses for this lean</CardTitle>
                    <CardDescription>
                      Catalog courses still open that advance the career-linked list.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="divide-y overflow-hidden rounded-lg border">
                      {activePath.suggestedCourses.map((row) => (
                        <li
                          key={row.code}
                          className="flex flex-col gap-1 px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div>
                            <Link
                              className="font-medium underline-offset-2 hover:underline"
                              href={courseHref(row.code)}
                            >
                              {row.code}
                            </Link>
                            <span className="text-muted-foreground"> · {row.title}</span>
                            <p className="text-xs text-muted-foreground">{row.why}</p>
                          </div>
                          {row.credits != null ? (
                            <span className="text-xs tabular-nums text-muted-foreground">
                              {row.credits} cr
                            </span>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ) : null}
            </section>
          ) : null}

          {path.attribution ? (
            <p className="text-xs text-muted-foreground">{path.attribution}</p>
          ) : null}
        </>
      )}
    </div>
  );
}
