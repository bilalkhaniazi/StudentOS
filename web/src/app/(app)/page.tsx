"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, Target, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import {
  careerLabel,
  createDemoProfile,
  getCareers,
  getCourses,
  getMeta,
  getProfile,
  getSession,
} from "@/lib/api";
import type { Career, CatalogCourse, Meta, StudentProfile } from "@/lib/types";

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [careers, setCareers] = useState<Career[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [sample, setSample] = useState<CatalogCourse[]>([]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const session = await getSession();
      const [p, c, m, courses] = await Promise.all([
        session.activeProfileId ? getProfile(session.activeProfileId) : Promise.resolve(null),
        getCareers(),
        getMeta(),
        getCourses(),
      ]);
      setProfile(p);
      setCareers(c);
      setMeta(m);
      setSample(courses.courses.slice(0, 6));
    } catch (err) {
      setError(err instanceof Error ? err.message : "The API did not respond.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        title="StudentOS could not reach its catalog API"
        body={error}
        onRetry={load}
      />
    );
  }

  const completed = profile?.courses.filter((c) => c.status === "completed") ?? [];
  const career = careerLabel(profile?.targetCareer, careers);
  const isEmptyProfile = !profile || (profile.courses.length === 0 && !profile.targetCareer && profile.syntheticId === "demo-profile");

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
          Milestone 4 · Slice A
        </p>
        <h1 className="font-heading text-3xl leading-tight md:text-4xl">
          Plan the next CIS course from a real GVSU catalog.
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-muted-foreground">
          Enter an academic profile, pick Data Engineer (or Cloud, Backend, ML), and browse Computer
          Science B.S. and Applied Computer Science M.S. courses — including catalog prerequisites.
          Skill gaps and match scores are not in this slice.
        </p>
      </section>

      {isEmptyProfile ? (
        <EmptyState
          title="No demo profile filled in yet"
          body="Create a local profile, or switch to a synthetic CS student in the header. The empty B.S. and M.S. records are there on purpose."
          action={
            <div className="flex flex-wrap gap-2">
              <Button render={<Link href="/profile" />}>Open profile</Button>
              <Button
                variant="outline"
                onClick={async () => {
                  await createDemoProfile();
                  await load();
                }}
              >
                Start a blank demo profile
              </Button>
            </div>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRound className="size-4" /> {profile?.displayName}
              </CardTitle>
              <CardDescription>
                {profile?.degreeLine} · {profile?.major}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                {completed.length} completed course{completed.length === 1 ? "" : "s"} on this record.
              </p>
              <Button size="sm" variant="outline" render={<Link href="/profile" />}>
                Edit profile
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="size-4" /> Target career
              </CardTitle>
              <CardDescription>
                {career ?? "Not selected. Pick Data Engineer to walk the proposal example."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {career ? <Badge>{career}</Badge> : null}
              <div className="mt-3">
                <Button size="sm" render={<Link href="/career" />}>
                  Choose career <ArrowRight className="size-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="size-4" /> Catalog
              </CardTitle>
              <CardDescription>
                {meta?.courseCount ?? 0} courses ingested for {meta?.catalog_year ?? "the current catalog year"}.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button size="sm" render={<Link href="/courses" />}>
                Browse courses
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="font-heading text-xl">From the ingested catalog</h2>
            <p className="text-sm text-muted-foreground">
              Public CIS listings. Open any course for credits and prerequisites.
            </p>
          </div>
          <Button variant="ghost" size="sm" render={<Link href="/courses" />}>
            View all
          </Button>
        </div>
        {sample.length === 0 ? (
          <EmptyState
            title="No courses in PostgreSQL"
            body="The catalog ingest did not load any CIS courses. Run the batch pipeline, then refresh."
            action={
              <Button variant="outline" onClick={load}>
                Refresh
              </Button>
            }
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sample.map((course) => (
              <Link key={course.code} href={`/courses/${encodeURIComponent(course.code.replaceAll(" ", "-"))}`}>
                <Card className="h-full hover:ring-foreground/20">
                  <CardHeader>
                    <CardTitle className="text-sm">
                      {course.code}
                      <span className="mt-1 block font-heading text-base font-medium">{course.title}</span>
                    </CardTitle>
                    <CardDescription>
                      {course.credits_min
                        ? `${course.credits_min}${
                            course.credits_max && course.credits_max !== course.credits_min
                              ? `–${course.credits_max}`
                              : ""
                          } credits`
                        : "Credits not listed"}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
