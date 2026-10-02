"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/empty-state";
import { getCareers, getProfile, getSession, setCareer } from "@/lib/api";
import type { Career, StudentProfile } from "@/lib/types";
import { toast } from "sonner";

export default function CareerPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [careers, setCareers] = useState<Career[]>([]);
  const [saving, setSaving] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const session = await getSession();
      if (!session.activeProfileId) {
        setProfile(null);
        setCareers(await getCareers());
        return;
      }
      const [p, c] = await Promise.all([getProfile(session.activeProfileId), getCareers()]);
      setProfile(p);
      setCareers(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load careers.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function pick(id: string) {
    if (!profile) return;
    setSaving(id);
    try {
      const next = await setCareer(profile.syntheticId, id);
      setProfile(next);
      toast.success(`Target career set to ${careers.find((c) => c.id === id)?.label}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save career.");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <Skeleton className="h-64 w-full" />;
  if (error) return <ErrorState body={error} onRetry={load} />;
  if (!profile) {
    return (
      <EmptyState
        title="No profile selected"
        body="Switch to a synthetic CS student or create a demo profile before choosing a career."
      />
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">Capability 2</p>
        <h1 className="mt-2 font-heading text-3xl">Select a target career</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          These four paths are the locked prototype careers. Match scores and skill-gap labels are not
          computed yet — this slice only stores the choice on the student record.
        </p>
      </div>
      <p className="text-sm">
        Active profile: <span className="font-medium">{profile.displayName}</span>
        {profile.targetCareer ? (
          <>
            {" "}
            · current target{" "}
            <Badge>{careers.find((c) => c.id === profile.targetCareer)?.label}</Badge>
          </>
        ) : (
          <span className="text-muted-foreground"> · no career selected</span>
        )}
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {careers.map((career) => {
          const selected = profile.targetCareer === career.id;
          return (
            <Card key={career.id} className={selected ? "ring-2 ring-primary" : undefined}>
              <CardHeader>
                <CardTitle className="font-heading text-xl">{career.label}</CardTitle>
                <CardDescription>
                  O*NET {career.onetSoc} · {career.onetTitle}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-relaxed">{career.summary}</p>
                <Button
                  type="button"
                  variant={selected ? "secondary" : "default"}
                  disabled={saving === career.id}
                  onClick={() => pick(career.id)}
                >
                  {selected ? "Selected" : `Set ${career.shortLabel} as target`}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
