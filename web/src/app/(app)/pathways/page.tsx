"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Check, ExternalLink, LoaderCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { courseHref, getMe, getPrograms } from "@/lib/api";
import {
  badgeCoursesOnRecord,
  courseOnRecord,
  isStudentBadge,
  preferredProgramId,
  studentBadgeFor,
  studentCourseMap,
} from "@/lib/pathway-progress";
import type {
  CatalogBadge,
  CatalogProgram,
  CourseEntry,
  PathwayCourse,
  StudentProfile,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const SECTION_LABEL: Record<string, string> = {
  foundation: "B.S. math foundation",
  required: "Required major courses",
  elective: "Major electives",
  cognate: "Required non-computing courses",
  "stats-choice": "Statistics (choose one)",
  "math-elective": "Math elective (choose one)",
  "science-lab": "Lab science (choose one with a lab)",
  "core-data-engineering": "Core · Data Engineering (choose one)",
  "core-systems-development": "Core · Management of Systems Development (choose one)",
  "core-software-engineering": "Core · Software Engineering (choose one)",
  "core-networking": "Core · Networking (choose one)",
  capstone: "Capstone",
};

function creditsOf(row: PathwayCourse) {
  if (row.credits_text) return `${row.credits_text} cr`;
  if (row.credits_min == null) return "credits in catalog";
  if (row.credits_max && row.credits_max !== row.credits_min) {
    return `${row.credits_min}–${row.credits_max} cr`;
  }
  return `${row.credits_min} cr`;
}

function statusLabel(row: CourseEntry) {
  if (row.status === "completed") {
    return row.gradeLetter ? `Completed · ${row.gradeLetter}` : "Completed";
  }
  if (row.status === "in_progress") {
    return row.term ? `In progress · ${row.term}` : "In progress";
  }
  return "On your record";
}

function CourseRows({
  rows,
  progress,
}: {
  rows: PathwayCourse[];
  progress: Map<string, CourseEntry>;
}) {
  return (
    <ul className="divide-y overflow-hidden rounded-lg border">
      {rows.map((row) => {
        const taken = courseOnRecord(progress, row.code);
        return (
          <li
            key={`${row.section}-${row.code}-${row.year ?? ""}`}
            className={cn(
              "flex items-center justify-between gap-3 px-3 py-2 text-sm",
              taken?.status === "completed" && "bg-emerald-50 dark:bg-emerald-950/40",
              taken?.status === "in_progress" && "bg-amber-50 dark:bg-amber-950/40"
            )}
          >
            <Link href={courseHref(row.code)} className="min-w-0 hover:underline">
              <span className="font-mono text-xs text-muted-foreground">{row.code}</span>{" "}
              <span>{row.title}</span>
            </Link>
            <span className="flex shrink-0 flex-wrap items-center justify-end gap-2">
              <span className="text-xs text-muted-foreground">{creditsOf(row)}</span>
              {taken ? (
                <Badge
                  variant="secondary"
                  className={cn(
                    taken.status === "completed" &&
                      "border-emerald-200 bg-emerald-100 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-50",
                    taken.status === "in_progress" &&
                      "border-amber-200 bg-amber-100 text-amber-900 dark:border-amber-900 dark:bg-amber-900/60 dark:text-amber-50"
                  )}
                >
                  {taken.status === "completed" ? (
                    <Check className="size-3" />
                  ) : (
                    <LoaderCircle className="size-3" />
                  )}
                  {statusLabel(taken)}
                </Badge>
              ) : null}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function BadgeCard({
  badge,
  progress,
  mine,
  awarded,
}: {
  badge: CatalogBadge;
  progress: Map<string, CourseEntry>;
  mine: boolean;
  awarded?: { name: string; status: string; awardedOn?: string | null };
}) {
  const taking = badgeCoursesOnRecord(badge, progress);
  const completedN = taking.filter((c) => c.status === "completed").length;
  const inProgressN = taking.filter((c) => c.status === "in_progress").length;
  return (
    <Card
      className={cn(
        mine && "ring-2 ring-primary ring-offset-2 ring-offset-background",
        taking.length > 0 && !mine && "border-primary/40"
      )}
    >
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <CardTitle className="font-heading text-lg">{badge.name}</CardTitle>
          {mine ? (
            <Badge>{awarded?.status === "awarded" ? "Your badge · awarded" : "Your badge"}</Badge>
          ) : null}
          {!mine && taking.length > 0 ? (
            <Badge variant="secondary">{taking.length} on your record</Badge>
          ) : null}
        </div>
        <CardDescription>
          {badge.kind} · {badge.course_count} courses · {badge.credits} credits
          {taking.length > 0 ? ` · ${completedN} completed, ${inProgressN} in progress` : ""}
          {awarded?.awardedOn ? ` · awarded ${awarded.awardedOn}` : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {(badge.slots || []).map((slot, index) => (
          <div key={`${badge.id}-${index}`}>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {slot.kind === "all" ? "Required" : `Choose ${slot.n} of the following`}
            </p>
            <CourseRows rows={slot.courses} progress={progress} />
          </div>
        ))}
        <a
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          href={badge.source_url}
          target="_blank"
          rel="noreferrer"
        >
          Catalog badge page <ExternalLink className="size-3" />
        </a>
      </CardContent>
    </Card>
  );
}

function ProgramPathway({
  program,
  profile,
  progress,
}: {
  program: CatalogProgram;
  profile: StudentProfile | null;
  progress: Map<string, CourseEntry>;
}) {
  const groups = useMemo(() => {
    const order = [
      "foundation",
      "required",
      "elective",
      "cognate",
      "stats-choice",
      "math-elective",
      "science-lab",
      "core-data-engineering",
      "core-systems-development",
      "core-software-engineering",
      "core-networking",
      "capstone",
    ];
    const by: Record<string, PathwayCourse[]> = {};
    for (const row of program.courses || []) {
      if (String(row.section || "").startsWith("badge-")) continue;
      by[row.section] = by[row.section] || [];
      by[row.section].push(row);
    }
    return order.filter((key) => by[key]?.length).map((key) => ({ key, rows: by[key] }));
  }, [program.courses]);

  const suggested = program.suggested_order || [];
  const years = useMemo(() => {
    const map = new Map<string, PathwayCourse[]>();
    for (const row of suggested) {
      const year = row.year || "Sequence";
      map.set(year, [...(map.get(year) || []), row]);
    }
    return [...map.entries()];
  }, [suggested]);

  const badges = program.badges || [];
  const yourBadges = badges.filter((badge) => isStudentBadge(profile?.badges, badge));
  const otherBadges = badges.filter((badge) => !isStudentBadge(profile?.badges, badge));
  const rules = program.rules || {};
  const core = (rules.core || {}) as { note?: string };
  const badgeRule = (rules.badge || {}) as { note?: string };
  const electives = (rules.electives || {}) as { note?: string };
  const capstone = (rules.capstone || {}) as { note?: string };
  const cognate = (rules.cognate || {}) as { note?: string };

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">{program.level}</p>
        <h2 className="font-heading text-2xl">{program.title}</h2>
        <p className="text-sm text-muted-foreground">
          {program.degree_line} · {program.major} · catalog {program.catalog_year}
          {typeof rules.total_credits === "number" ? ` · ${rules.total_credits} credits` : ""}
        </p>
        <a
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          href={program.source_url}
          target="_blank"
          rel="noreferrer"
        >
          Official GVSU catalog page <ExternalLink className="size-3.5" />
        </a>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {core.note ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Core / required</CardTitle>
              <CardDescription>{core.note}</CardDescription>
            </CardHeader>
          </Card>
        ) : null}
        {badgeRule.note ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Badge</CardTitle>
              <CardDescription>
                {yourBadges.length
                  ? `Your record lists ${yourBadges.map((b) => b.name).join(", ")}.`
                  : badgeRule.note}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : null}
        {electives.note ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Electives</CardTitle>
              <CardDescription>{electives.note}</CardDescription>
            </CardHeader>
          </Card>
        ) : null}
        {capstone.note ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Capstone</CardTitle>
              <CardDescription>{capstone.note}</CardDescription>
            </CardHeader>
          </Card>
        ) : null}
        {cognate.note ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Non-computing</CardTitle>
              <CardDescription>{cognate.note}</CardDescription>
            </CardHeader>
          </Card>
        ) : null}
      </div>

      {groups.map((group) => {
        const hit = group.rows.filter((row) => courseOnRecord(progress, row.code)).length;
        return (
          <section key={group.key} className="space-y-2">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="font-heading text-lg">{SECTION_LABEL[group.key] || group.key}</h3>
              <p className="text-xs text-muted-foreground">
                {hit ? `${hit} on your record · ` : ""}
                {group.rows.length} courses
              </p>
            </div>
            <CourseRows rows={group.rows} progress={progress} />
          </section>
        );
      })}

      {badges.length > 0 ? (
        <section className="space-y-4">
          <div>
            <h3 className="font-heading text-lg">Graduate badges</h3>
            <p className="text-sm text-muted-foreground">
              The Applied CS M.S. requires at least one of these nine-credit badges. Completing the three
              courses also earns the post-baccalaureate badge.
            </p>
          </div>
          {yourBadges.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Your badge</h4>
              <div className="grid gap-4 lg:grid-cols-2">
                {yourBadges.map((badge) => (
                  <BadgeCard
                    key={badge.id}
                    badge={badge}
                    progress={progress}
                    mine
                    awarded={studentBadgeFor(profile?.badges, badge)}
                  />
                ))}
              </div>
            </div>
          ) : null}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">{yourBadges.length ? "Other badges" : "All badges"}</h4>
            <div className="grid gap-4 lg:grid-cols-2">
              {otherBadges.map((badge) => (
                <BadgeCard key={badge.id} badge={badge} progress={progress} mine={false} />
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {years.length > 0 ? (
        <section className="space-y-3">
          <div>
            <h3 className="font-heading text-lg">Suggested order of coursework</h3>
            <p className="text-sm text-muted-foreground">
              From the catalog. General education and math placement still go through an advisor.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {years.map(([year, rows]) => (
              <Card key={year}>
                <CardHeader>
                  <CardTitle className="text-base">{year}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CourseRows rows={rows} progress={progress} />
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

export default function PathwaysPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [programs, setPrograms] = useState<CatalogProgram[]>([]);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [active, setActive] = useState("applied-cs-ms");
  const [choseProgram, setChoseProgram] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [list, me] = await Promise.all([getPrograms(), getMe()]);
      setPrograms(list);
      setProfile(me);
      if (!choseProgram) {
        const preferred = preferredProgramId(me, list);
        if (preferred) setActive(preferred);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load degree pathways.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const progress = useMemo(() => studentCourseMap(profile?.courses), [profile?.courses]);
  const program = programs.find((p) => p.id === active) ?? programs[0];
  const completed = profile?.courses.filter((c) => c.status === "completed").length ?? 0;
  const inProgress = profile?.courses.filter((c) => c.status === "in_progress").length ?? 0;
  const badgeNames = (profile?.badges || [])
    .filter((b) => b.status !== "none")
    .map((b) => b.name);

  if (loading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState body={error} onRetry={load} />;
  if (!program) {
    return (
      <EmptyState
        title="No programs ingested"
        body="The catalog pipeline has not loaded the Computer Science B.S. or Applied CS M.S. pathways yet."
      />
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">Degree pathways</p>
        <h1 className="mt-2 font-heading text-3xl">What you take to finish the degree</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Required courses, electives, cognates, and — for the Applied CS M.S. — the nine graduate badges.
          Course titles and credits are structured fields from the GVSU public catalog. This is not official SIS.
        </p>
      </div>

      {profile ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">On your record</CardTitle>
            <CardDescription>
              {completed || inProgress || badgeNames.length
                ? `${profile.displayName}: ${completed} completed, ${inProgress} in progress${
                    badgeNames.length ? ` · ${badgeNames.join(", ")}` : ""
                  }. Highlighted on the map below.`
                : "No Banner courses yet. Upload a transcript on Profile and this map will mark what you have already done."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2 text-xs">
            <Badge
              variant="secondary"
              className="border-emerald-200 bg-emerald-100 text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-50"
            >
              <Check className="size-3" /> Completed
            </Badge>
            <Badge
              variant="secondary"
              className="border-amber-200 bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-50"
            >
              <LoaderCircle className="size-3" /> In progress
            </Badge>
            <Badge>Your badge</Badge>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {programs.map((item) => (
          <Button
            key={item.id}
            type="button"
            variant={item.id === program.id ? "default" : "outline"}
            onClick={() => {
              setChoseProgram(true);
              setActive(item.id);
            }}
          >
            {item.id === "cs-bs" ? "Computer Science B.S." : "Applied CS M.S."}
          </Button>
        ))}
      </div>
      <ProgramPathway program={program} profile={profile} progress={progress} />
    </div>
  );
}
