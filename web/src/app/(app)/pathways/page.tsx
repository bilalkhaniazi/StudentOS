"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { courseHref, getPrograms } from "@/lib/api";
import type { CatalogBadge, CatalogProgram, PathwayCourse } from "@/lib/types";

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

function CourseRows({ rows }: { rows: PathwayCourse[] }) {
  return (
    <ul className="divide-y rounded-lg border">
      {rows.map((row) => (
        <li key={`${row.section}-${row.code}-${row.year ?? ""}`} className="flex items-baseline justify-between gap-3 px-3 py-2 text-sm">
          <Link href={courseHref(row.code)} className="min-w-0 hover:underline">
            <span className="font-mono text-xs text-muted-foreground">{row.code}</span>{" "}
            <span>{row.title}</span>
          </Link>
          <span className="shrink-0 text-xs text-muted-foreground">{creditsOf(row)}</span>
        </li>
      ))}
    </ul>
  );
}

function BadgeCard({ badge }: { badge: CatalogBadge }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-heading text-lg">{badge.name}</CardTitle>
        <CardDescription>
          {badge.kind} · {badge.course_count} courses · {badge.credits} credits
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {(badge.slots || []).map((slot, index) => (
          <div key={`${badge.id}-${index}`}>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {slot.kind === "all" ? "Required" : `Choose ${slot.n} of the following`}
            </p>
            <CourseRows rows={slot.courses} />
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

function ProgramPathway({ program }: { program: CatalogProgram }) {
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

  const rules = program.rules || {};
  const core = (rules.core || {}) as { note?: string; choose_areas?: number; of_areas?: number; credits?: number };
  const badgeRule = (rules.badge || {}) as { note?: string };
  const electives = (rules.electives || {}) as { note?: string; choose?: number; credits_min?: number; credits_max?: number };
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
              <CardDescription>{badgeRule.note}</CardDescription>
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

      {groups.map((group) => (
        <section key={group.key} className="space-y-2">
          <div className="flex items-baseline justify-between gap-3">
            <h3 className="font-heading text-lg">{SECTION_LABEL[group.key] || group.key}</h3>
            <p className="text-xs text-muted-foreground">{group.rows.length} courses</p>
          </div>
          <CourseRows rows={group.rows} />
        </section>
      ))}

      {(program.badges || []).length > 0 ? (
        <section className="space-y-3">
          <div>
            <h3 className="font-heading text-lg">Graduate badges</h3>
            <p className="text-sm text-muted-foreground">
              The Applied CS M.S. requires at least one of these nine-credit badges. Completing the three
              courses also earns the post-baccalaureate badge.
            </p>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {(program.badges || []).map((badge) => (
              <BadgeCard key={badge.id} badge={badge} />
            ))}
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
                  <CourseRows rows={rows} />
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
  const [active, setActive] = useState("applied-cs-ms");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const list = await getPrograms();
      setPrograms(list);
      if (list.some((p) => p.id === "applied-cs-ms")) setActive("applied-cs-ms");
      else if (list[0]) setActive(list[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load degree pathways.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const program = programs.find((p) => p.id === active) ?? programs[0];

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
      <div className="flex flex-wrap gap-2">
        {programs.map((item) => (
          <Button
            key={item.id}
            type="button"
            variant={item.id === program.id ? "default" : "outline"}
            onClick={() => setActive(item.id)}
          >
            {item.id === "cs-bs" ? "Computer Science B.S." : "Applied CS M.S."}
          </Button>
        ))}
      </div>
      <ProgramPathway program={program} />
    </div>
  );
}
