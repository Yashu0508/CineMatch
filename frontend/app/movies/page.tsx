"use client";
import { useState } from "react";
import { PageHeading, PageShell } from "@/components/common/page-shell";
import { ErrorState, SkeletonGrid } from "@/components/common/states";
import { MovieGrid } from "@/components/movies/movie-rail";
import { useMovies } from "@/hooks/use-api";
export default function MoviesPage() { const [kind, setKind] = useState<"trending"|"popular"|"topRated"|"upcoming">("popular"); const query = useMovies(kind); return <PageShell><PageHeading eyebrow="Browse" title="Find your next watch" description="Explore the films everyone is talking about, from timeless favorites to what is arriving next." /><div className="mb-9 flex flex-wrap gap-2">{([["popular","Popular"],["trending","Trending"],["topRated","Top rated"],["upcoming","Upcoming"]] as const).map(([value,label]) => <button key={value} onClick={() => setKind(value)} className={`rounded-full px-4 py-2 text-sm transition ${kind===value ? "bg-amber-300 font-semibold text-black" : "border border-white/10 text-white/60 hover:border-white/30 hover:text-white"}`}>{label}</button>)}</div>{query.isLoading ? <SkeletonGrid count={12} /> : query.isError ? <ErrorState /> : <MovieGrid movies={query.data.items} />}</PageShell>; }
