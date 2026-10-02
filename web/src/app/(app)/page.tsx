"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Award, BookOpen, Target, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { careerLabel, getCareers, getCourses, getMe, getMeta } from "@/lib/api";
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
      const [p, c, m, courses] = await Promise.all([getMe(), getCareers(), getMeta(), getCourses()]);
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
  const majors = profile?.majors?.length ? profile.majors : profile?.major ? [profile.major] : [];
  const badges = profile?.badges ?? [];
  const needsTranscript = !profile?.degreeLine && completed.length === 0;

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
          Your record
        </p>
        <h1 className="font-heading text-3xl leading-tight md:text-4xl">
          {profile?.displayName ? `Welcome, ${profile.displayName}.` : "Your academic profile"}
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-muted-foreground">
          This is your GVSU student record in StudentOS — degree, majors, badges, and coursework from
          a Banner advising transcript. Open Pathways for the full CS B.S. and Applied CS M.S. maps,
          then browse the CIS catalog.
        </p>
      </section>

      {needsTranscript ? (
        <EmptyState
          title="No transcript on this profile yet"
          body="Upload your Banner advising PDF on Profile. StudentOS will fill degree, majors, badges, and courses, then discard the file."
          action={
            <Button render={<Link href="/profile" />}>Open your profile</Button>
          }
        />
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserRound className="size-4" /> {profile?.displayName || "Student"}
            </CardTitle>
            <CardDescription>
              {[profile?.degreeLine, majors.join(" · ")].filter(Boolean).join(" · ") ||
                "Degree and major appear after a transcript upload."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {profile?.college ? <p>{profile.college}</p> : null}
            {profile?.email ? <p className="text-muted-foreground">{profile.email}</p> : null}
            <p>
              {completed.length} completed course{completed.length === 1 ? "" : "s"} on this record.
            </p>
            <div className="flex flex-wrap gap-1">
              {badges.length ? (
                badges.map((badge) => (
                  <Badge key={badge.name} variant="secondary">
                    {badge.kind}: {badge.name}
                  </Badge>
                ))
              ) : (
                <span className="text-muted-foreground">No Banner badge on file.</span>
              )}
            </div>
            <Button size="sm" variant="outline" render={<Link href="/profile" />}>
              View profile
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="size-4" /> Target career
            </CardTitle>
            <CardDescription>
              {career ?? "Not selected yet. Choose Data Engineer, Cloud, Backend, or ML."}
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
              {meta?.courseCount ?? 0} CIS courses ingested for {meta?.catalog_year ?? "the current catalog year"}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Award className="size-4" />
              {badges.length
                ? `${badges.length} post-baccalaureate badge${badges.length === 1 ? "" : "s"}`
                : "No badge listed"}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" render={<Link href="/pathways" />}>
                Degree pathways
              </Button>
              <Button size="sm" variant="outline" render={<Link href="/courses" />}>
                Browse courses
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

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
