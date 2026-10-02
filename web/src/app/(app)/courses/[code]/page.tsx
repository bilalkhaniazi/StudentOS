"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { courseHref, getCourse } from "@/lib/api";
import type { CatalogCourse } from "@/lib/types";

export default function CourseDetailPage() {
  const params = useParams<{ code: string }>();
  const raw = decodeURIComponent(params.code || "").replaceAll("-", " ");
  const [course, setCourse] = useState<CatalogCourse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setCourse(await getCourse(raw));
    } catch (err) {
      setCourse(null);
      setError(err instanceof Error ? err.message : "Course not found.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [raw]);

  if (loading) return <Skeleton className="h-80 w-full" />;
  if (error) {
    return (
      <div className="space-y-4">
        <ErrorState title="Course not in the catalog" body={error} onRetry={load} />
        <Button variant="outline" render={<Link href="/courses" />}>
          Back to courses
        </Button>
      </div>
    );
  }
  if (!course) {
    return (
      <EmptyState
        title="No course loaded"
        body="This code is missing from PostgreSQL."
        action={
          <Button variant="outline" render={<Link href="/courses" />}>
            Browse catalog
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-sm text-muted-foreground">{course.code}</p>
        <h1 className="font-heading text-3xl">{course.title}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge>
            {course.credits_min
              ? `${course.credits_min}${
                  course.credits_max && course.credits_max !== course.credits_min
                    ? `–${course.credits_max}`
                    : ""
                } credits`
              : "Credits not listed"}
          </Badge>
          <Badge variant="secondary">{course.level}</Badge>
          {course.programs?.["cs-bs"] ? <Badge variant="outline">CS B.S. {course.programs["cs-bs"].join(", ")}</Badge> : null}
          {course.programs?.["applied-cs-ms"] ? (
            <Badge variant="outline">Applied CS M.S. {course.programs["applied-cs-ms"].join(", ")}</Badge>
          ) : null}
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Catalog description</CardTitle>
          <CardDescription>
            {course.catalog_year} public catalog
            {course.offered ? ` · ${course.offered}` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed">
          <p>{course.description || "No description was published on the course page snapshot."}</p>
          {course.prerequisites_text ? (
            <p>
              <span className="font-medium">Prerequisites. </span>
              {course.prerequisites_text}
            </p>
          ) : (
            <p className="text-muted-foreground">No prerequisite sentence stored for this course.</p>
          )}
          {course.source_url ? (
            <p>
              <a className="underline" href={course.source_url} target="_blank" rel="noreferrer">
                Open the GVSU catalog page
              </a>
            </p>
          ) : null}
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Prerequisite of this course</CardTitle>
            <CardDescription>Locked relation: course → prerequisite of → course</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {(course.prerequisiteCourses || []).length === 0 ? (
              <p className="text-muted-foreground">No catalog-code prerequisites linked.</p>
            ) : (
              course.prerequisiteCourses!.map((item) => (
                <Link key={item.code} href={courseHref(item.code)} className="block hover:underline">
                  {item.code} — {item.title}
                </Link>
              ))
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>This course is a prerequisite for</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {(course.unlocksCourses || []).length === 0 ? (
              <p className="text-muted-foreground">No later CIS courses point at this one in the snapshot.</p>
            ) : (
              course.unlocksCourses!.map((item) => (
                <Link key={item.code} href={courseHref(item.code)} className="block hover:underline">
                  {item.code} — {item.title}
                </Link>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
