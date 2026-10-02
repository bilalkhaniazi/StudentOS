"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { courseHref, getCourses, getMe } from "@/lib/api";
import type { CatalogCourse, StudentProfile } from "@/lib/types";

const LEVELS = [
  { id: "", label: "All levels" },
  { id: "undergraduate", label: "Undergraduate" },
  { id: "graduate", label: "Graduate" },
];

const PROGRAMS = [
  { id: "", label: "All programs" },
  { id: "cs-bs", label: "CS B.S." },
  { id: "applied-cs-ms", label: "Applied CS M.S." },
];

export default function CoursesPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courses, setCourses] = useState<CatalogCourse[]>([]);
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("");
  const [program, setProgram] = useState("");
  const [profile, setProfile] = useState<StudentProfile | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [list, me] = await Promise.all([getCourses(), getMe()]);
      setCourses(list.courses);
      setProfile(me);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the catalog.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return courses.filter((c) => {
      if (level && c.level !== level) return false;
      if (program && !(c.programs && program in c.programs)) return false;
      if (!needle) return true;
      return (
        c.code.toLowerCase().includes(needle) ||
        (c.title || "").toLowerCase().includes(needle) ||
        (c.description || "").toLowerCase().includes(needle)
      );
    });
  }, [courses, query, level, program]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }
  if (error) return <ErrorState body={error} onRetry={load} />;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
          Capability 5 · browse
        </p>
        <h1 className="mt-2 font-heading text-3xl">Explore GVSU CIS courses</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Structured fields from the public 2026–2027 catalog: code, title, credits, description, and
          prerequisites when the course page lists them. Course intelligence (skills and career
          contribution) arrives in a later slice.
        </p>
      </div>

      {profile?.targetCareer ? (
        <p className="text-sm text-muted-foreground">
          Viewing as <span className="text-foreground">{profile.displayName}</span> with target{" "}
          <Badge variant="secondary">{profile.targetCareer.replace("-", " ")}</Badge>. This list is
          the catalog, not a ranked recommendation.
        </p>
      ) : null}

      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-2.5 left-2.5 size-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search code, title, or description — try Database or CIS 660"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {LEVELS.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant={level === item.id ? "default" : "outline"}
              onClick={() => setLevel(item.id)}
            >
              {item.label}
            </Button>
          ))}
          {PROGRAMS.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant={program === item.id ? "secondary" : "outline"}
              onClick={() => setProgram(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </div>

      {courses.length === 0 ? (
        <EmptyState
          title="No courses ingested"
          body="PostgreSQL has no course nodes. Run python pipeline/ingest.py and restart the API."
          action={
            <Button variant="outline" onClick={load}>
              Refresh
            </Button>
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          title="No courses match these filters"
          body="Clear the search or switch back to all levels to see the full CIS list."
          action={
            <Button
              variant="outline"
              onClick={() => {
                setQuery("");
                setLevel("");
                setProgram("");
              }}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {visible.map((course) => (
            <Link key={course.code} href={courseHref(course.code)}>
              <Card className="h-full hover:ring-foreground/20">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle>
                      <span className="font-mono text-xs text-muted-foreground">{course.code}</span>
                      <span className="mt-1 block font-heading text-lg">{course.title}</span>
                    </CardTitle>
                    <Badge variant="outline">
                      {course.credits_min
                        ? `${course.credits_min}${
                            course.credits_max && course.credits_max !== course.credits_min
                              ? `–${course.credits_max}`
                              : ""
                          } cr`
                        : "n/a"}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-3">
                    {course.description || "No description stored for this listing."}
                  </CardDescription>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {course.programs?.["cs-bs"] ? <Badge variant="secondary">CS B.S.</Badge> : null}
                    {course.programs?.["applied-cs-ms"] ? (
                      <Badge variant="secondary">Applied CS M.S.</Badge>
                    ) : null}
                    {course.prerequisite_codes?.length ? (
                      <Badge variant="outline">
                        Prereq {course.prerequisite_codes.join(", ")}
                      </Badge>
                    ) : null}
                  </div>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
      <p className="text-xs text-muted-foreground">{visible.length} courses shown.</p>
    </div>
  );
}
