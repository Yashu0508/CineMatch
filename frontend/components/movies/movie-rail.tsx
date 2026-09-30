import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Movie } from "@/types";
import { MovieCard } from "./movie-card";
export function MovieRail({ title, movies, href }: { title: string; movies: Movie[]; href?: string }) { return <section className="mb-12"><div className="mb-5 flex items-end justify-between"><h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">{title}</h2>{href && <Link href={href} className="flex items-center gap-1 text-sm text-amber-200 hover:text-amber-100">See all <ArrowRight size={15} /></Link>}</div><div className="scrollbar-hide flex gap-4 overflow-x-auto pb-2">{movies.map(movie => <MovieCard key={movie.id} movie={movie} compact />)}</div></section>; }
export function MovieGrid({ movies }: { movies: Movie[] }) { return <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">{movies.map(movie => <MovieCard key={movie.id} movie={movie} />)}</div>; }
