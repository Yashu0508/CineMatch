"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Bookmark, BookmarkCheck, Check, Star } from "lucide-react";
import { useMovie, useMovieRail, useInteractions } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth/context";
import { calendarApi } from "@/lib/api/calendar";
import { MovieRail } from "@/components/movies/movie-rail";
import { ErrorState, SkeletonGrid } from "@/components/common/states";
import { PageShell } from "@/components/common/page-shell";

export default function MovieDetailsPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const id = Number(params.id);
  const movie = useMovie(id);
  const similar = useMovieRail("similar", id);
  const related = useMovieRail("related", id);
  const { user } = useAuth();
  const { watchlist, add, remove, rate, markWatched } = useInteractions();
  const [rating, setRating] = useState(0);
  const [reminderBusy, setReminderBusy] = useState(false);
  const [calendarMessage, setCalendarMessage] = useState(() => {
    const status = searchParams.get("calendar");
    if (status === "reminder_added") return "Reminder added to Google Calendar.";
    if (status === "connected") return "Google Calendar connected.";
    if (status === "denied") return "Google Calendar authorization was cancelled.";
    if (status === "error") return "Google Calendar could not complete the reminder.";
    return "";
  });

  if (movie.isLoading) return <PageShell><div className="skeleton h-[520px] rounded-3xl" /></PageShell>;
  if (movie.isError || !movie.data) return <PageShell><ErrorState message="That movie could not be found." /></PageShell>;

  const m = movie.data;
  const saved = watchlist.data?.items.some(x => x.movie_id === m.id) ?? false;
  const canRemind = Boolean(m.release_date && m.release_date > new Date().toISOString().slice(0, 10));
  const backdrop = m.backdrop_path ? `https://image.tmdb.org/t/p/original${m.backdrop_path}` : null;

  const setReminder = async () => {
    if (!user || !canRemind) return;
    setReminderBusy(true);
    setCalendarMessage("");
    try {
      const result = await calendarApi.start(m.id);
      if (result.authorization_url) {
        window.location.assign(result.authorization_url);
        return;
      }
      setCalendarMessage(result.message);
    } catch (error) {
      setCalendarMessage(error instanceof Error ? error.message : "Unable to set the reminder.");
    } finally {
      setReminderBusy(false);
    }
  };

  return <div>
    {backdrop && <div className="absolute inset-x-0 top-[72px] -z-10 h-[520px] opacity-35"><img src={backdrop} alt="" className="h-full w-full object-cover" /><div className="absolute inset-0 bg-gradient-to-b from-[#0b0c0f]/30 via-[#0b0c0f]/75 to-[#0b0c0f]" /></div>}
    <PageShell>
      <div className="grid gap-10 pt-10 md:grid-cols-[240px_1fr] md:pt-16">
        <div className="mx-auto w-56 md:mx-0 md:w-full">{m.poster_path ? <img src={`https://image.tmdb.org/t/p/w500${m.poster_path}`} alt={m.title} className="w-full rounded-2xl shadow-2xl" /> : <div className="aspect-[2/3] rounded-2xl bg-white/10" />}</div>
        <div className="max-w-3xl self-end">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[.25em] text-amber-200">Movie profile</p>
          <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-6xl">{m.title}</h1>
          <div className="mt-5 flex flex-wrap items-center gap-4 text-sm text-white/60"><span className="flex items-center gap-1 text-amber-200"><Star size={15} fill="currentColor" />{m.vote_average?.toFixed(1) ?? "—"}</span><span>{m.release_date?.slice(0, 4) || "Release date unknown"}</span><span>{m.runtime ? `${m.runtime} min` : "Runtime unavailable"}</span></div>
          <div className="mt-5 flex flex-wrap gap-2">{m.genres.map(g => <span key={g.id} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/65">{g.name}</span>)}</div>
          <p className="mt-7 max-w-2xl text-base leading-7 text-white/65">{m.overview || "No overview is available for this title yet."}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            {user ? <>
              <button onClick={() => saved ? remove.mutate(m.id) : add.mutate(m.id)} className="flex items-center gap-2 rounded-full bg-amber-300 px-5 py-3 text-sm font-semibold text-black">{saved ? <BookmarkCheck size={17} /> : <Bookmark size={17} />} {saved ? "In watchlist" : "Add to watchlist"}</button>
              <button onClick={() => markWatched.mutate(m.id)} className="flex items-center gap-2 rounded-full border border-white/15 px-5 py-3 text-sm text-white/80"><Check size={17} /> Mark watched</button>
              {canRemind && <button onClick={setReminder} disabled={reminderBusy} className="rounded-full border border-amber-200/50 px-5 py-3 text-sm text-amber-200 hover:bg-amber-300 hover:text-black disabled:opacity-50">{reminderBusy ? "Connecting…" : "Set reminder"}</button>}
            </> : <Link href="/login" className="rounded-full bg-amber-300 px-5 py-3 text-sm font-semibold text-black">Sign in to save this film</Link>}
          </div>
          {calendarMessage && <p className="mt-4 text-sm text-amber-200">{calendarMessage}</p>}
          {user && <div className="mt-7 flex items-center gap-2"><span className="mr-2 text-sm text-white/50">Your rating</span>{[1, 2, 3, 4, 5].map(n => <button key={n} aria-label={`Rate ${n} stars`} onClick={() => { setRating(n); rate.mutate({ id: m.id, value: n }); }} className={n <= rating ? "text-amber-200" : "text-white/25 hover:text-amber-200"}><Star size={21} fill="currentColor" /></button>)}</div>}
        </div>
      </div>
      <div className="mt-24">{similar.isLoading ? <SkeletonGrid /> : similar.data && <MovieRail title="Similar films" movies={similar.data.items} />} {related.isLoading ? <SkeletonGrid /> : related.data && <MovieRail title="You may also like" movies={related.data.items} />}</div>
    </PageShell>
  </div>;
}
