"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PageHeading, PageShell } from "@/components/common/page-shell";
import { ErrorState, SkeletonGrid } from "@/components/common/states";
import { interactionsApi } from "@/lib/api/interactions";
import { useAuth } from "@/lib/auth/context";
import { useInteractions } from "@/hooks/use-api";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Preferences } from "@/types";

const blankPreferences: Preferences = { preferred_genres: [], preferred_languages: [], onboarding_complete: false };

export default function ProfilePage() {
  const { user } = useAuth(); const router = useRouter(); const qc = useQueryClient();
  const prefsQuery = useQuery({ queryKey: ["preferences"], queryFn: interactionsApi.preferences, enabled: Boolean(user) });
  const prefs = prefsQuery.data ?? blankPreferences;
  const { ratings, watchlist, history } = useInteractions(); const [complete, setComplete] = useState<boolean>();
  const save = useMutation({ mutationFn: () => interactionsApi.updatePreferences({ preferred_genres: prefs.preferred_genres, preferred_languages: prefs.preferred_languages, onboarding_complete: complete ?? prefs.onboarding_complete }), onSuccess: () => qc.invalidateQueries({ queryKey: ["preferences"] }) });
  if (!user) return <PageShell><div className="rounded-2xl border border-white/10 p-8 text-center">Sign in to view your profile.<button onClick={() => router.push("/login")} className="ml-3 rounded-full bg-amber-300 px-4 py-2 text-sm font-semibold text-black">Sign in</button></div></PageShell>;
  return <PageShell><PageHeading eyebrow="Your space" title="Profile" description="Your CineMatch account, signals, and preferences." />
    {prefsQuery.isLoading ? <SkeletonGrid count={3} /> : prefsQuery.isError ? <ErrorState /> : <div className="grid gap-5 lg:grid-cols-[1.3fr_.7fr]"><section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><p className="text-xs uppercase tracking-[.2em] text-amber-200">Account</p><h2 className="mt-3 text-2xl font-semibold">{user.email}</h2><p className="mt-2 text-sm text-white/45">Member of CineMatch</p><div className="mt-8 grid grid-cols-3 gap-3"><Stat label="Ratings" value={ratings.data.total} /><Stat label="Saved" value={watchlist.data.total} /><Stat label="Watched" value={history.data.total} /></div></section><section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><p className="text-xs uppercase tracking-[.2em] text-amber-200">Preferences</p><label className="mt-6 flex items-center gap-3 text-sm text-white/70"><input type="checkbox" checked={complete ?? prefs.onboarding_complete} onChange={e => setComplete(e.target.checked)} className="size-4 accent-amber-300" /> Personalization complete</label><button onClick={() => save.mutate()} disabled={save.isPending} className="mt-7 rounded-full bg-amber-300 px-5 py-2 text-sm font-semibold text-black disabled:opacity-50">{save.isPending ? "Saving…" : "Save preferences"}</button></section></div>}
  </PageShell>;
}
function Stat({ label, value }: { label: string; value: number }) { return <div className="rounded-xl bg-white/[.04] p-4"><p className="text-2xl font-semibold text-white">{value}</p><p className="mt-1 text-xs text-white/45">{label}</p></div>; }
