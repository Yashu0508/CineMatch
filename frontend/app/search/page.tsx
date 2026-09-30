"use client";
import { Search as SearchIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { moviesApi } from "@/lib/api/movies";
import { MovieGrid } from "@/components/movies/movie-rail";
import { ErrorState, EmptyState, SkeletonGrid } from "@/components/common/states";
import { PageHeading, PageShell } from "@/components/common/page-shell";

export default function SearchPage() {
  const [input, setInput] = useState("");
  const [queryText, setQueryText] = useState("");
  useEffect(() => { const timer = setTimeout(() => setQueryText(input.trim()), 450); return () => clearTimeout(timer); }, [input]);
  const results = useQuery({ queryKey: ["search", queryText], queryFn: () => moviesApi.search(queryText), enabled: queryText.length > 0 });
  const items = results.data?.items ?? [];
  return <PageShell>
    <PageHeading eyebrow="Discovery" title="Search the whole story" description="Search by title, then let CineMatch take you to the right film." />
    <div className="mb-12 flex max-w-2xl items-center gap-3 rounded-2xl border border-white/10 bg-white/[.04] px-5 py-4 focus-within:border-amber-200/60"><SearchIcon size={20} className="text-white/40" /><input autoFocus value={input} onChange={e => setInput(e.target.value)} placeholder="Try Inception, Dune, or a favorite actor" className="w-full bg-transparent text-white outline-none placeholder:text-white/30" aria-label="Search movies" /></div>
    {!queryText ? <EmptyState title="Start with a movie title" /> : results.isLoading ? <SkeletonGrid count={12} /> : results.isError ? <ErrorState message="Search is unavailable right now." /> : items.length ? <MovieGrid movies={items} /> : <EmptyState title={`No films found for “${queryText}”`} />}
  </PageShell>;
}
