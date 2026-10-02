"use client";
import Link from "next/link";
import { Bookmark, BookmarkCheck, Star } from "lucide-react";
import { Movie } from "@/types";
import { useInteractions } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth/context";

function imageUrl(path?: string | null) { return path ? `https://image.tmdb.org/t/p/w500${path}` : null; }
export function MovieCard({ movie, compact = false }: { movie: Movie; compact?: boolean }) {
  const { user } = useAuth(); const { watchlist, add, remove } = useInteractions();
  const saved = watchlist.data?.items.some(item => item.movie_id === movie.id) ?? false;
  const poster = imageUrl(movie.poster_path);
  const toggle = (event: React.MouseEvent) => { event.preventDefault(); event.stopPropagation(); if (!user) return; saved ? remove.mutate(movie.id) : add.mutate(movie.id); };
  return <Link href={`/movies/${movie.id}`} draggable={false} className={`group block shrink-0 ${compact ? "w-[150px] sm:w-[170px] lg:w-[190px]" : ""}`}>
    <div className="relative aspect-[2/3] overflow-hidden rounded-xl border border-white/10 bg-[#1a1c20] shadow-2xl transition duration-300 group-hover:-translate-y-1 group-hover:border-amber-200/50">
      {poster ? <img src={poster} alt={movie.title} loading="lazy" className="h-full w-full object-cover transition duration-500 group-hover:scale-105" /> : <div className="flex h-full items-center justify-center p-4 text-center text-sm text-white/40">No poster available</div>}
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/90 to-transparent" />
      {user && <button aria-label={saved ? `Remove ${movie.title} from watchlist` : `Add ${movie.title} to watchlist`} onClick={toggle} className="absolute right-2 top-2 rounded-full bg-black/60 p-2 text-white backdrop-blur transition hover:bg-amber-300 hover:text-black">{saved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}</button>}
      <div className="absolute inset-x-3 bottom-3 flex items-center justify-between text-xs"><span className="flex items-center gap-1 text-amber-200"><Star size={13} fill="currentColor" />{movie.vote_average ? movie.vote_average.toFixed(1) : "—"}</span><span className="text-white/60">{movie.release_date?.slice(0, 4) || "TBA"}</span></div>
    </div>
    <h3 className="mt-3 truncate text-sm font-semibold text-white/90 group-hover:text-amber-200">{movie.title}</h3>
  </Link>;
}
