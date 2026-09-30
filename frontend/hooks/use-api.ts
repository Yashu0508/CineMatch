"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { moviesApi } from "@/lib/api/movies";
import { recommendationsApi } from "@/lib/api/recommendations";
import { interactionsApi } from "@/lib/api/interactions";
import { useAuth } from "@/lib/auth/context";
export const useMovies = (kind: "trending" | "popular" | "topRated" | "upcoming") => { const query = useQuery({ queryKey: ["movies", kind], queryFn: () => moviesApi[kind](), staleTime: 60_000 }); return { ...query, data: query.data ?? { items: [], page: 1, total: 0, total_pages: 0 } }; };
export const useMovie = (id: number) => useQuery({ queryKey: ["movie", id], queryFn: () => moviesApi.detail(id), enabled: Number.isFinite(id) });
export const useMovieRail = (kind: "similar" | "related", id: number) => useQuery({ queryKey: ["movies", kind, id], queryFn: () => moviesApi[kind](id), enabled: Number.isFinite(id) });
export const useRecommendations = () => { const { user } = useAuth(); const query = useQuery({ queryKey: ["recommendations"], queryFn: () => recommendationsApi.forYou(), enabled: Boolean(user) }); return { ...query, data: query.data ?? [] }; };
export function useInteractions() {
  const { user } = useAuth(); const qc = useQueryClient();
  const watchlist = useQuery({ queryKey: ["watchlist"], queryFn: () => interactionsApi.watchlist(), enabled: Boolean(user) });
  const history = useQuery({ queryKey: ["history"], queryFn: () => interactionsApi.history(), enabled: Boolean(user) });
  const ratings = useQuery({ queryKey: ["ratings"], queryFn: () => interactionsApi.ratings(), enabled: Boolean(user) });
  const add = useMutation({ mutationFn: interactionsApi.addWatchlist, onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }) });
  const remove = useMutation({ mutationFn: interactionsApi.removeWatchlist, onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }) });
  const rate = useMutation({ mutationFn: ({ id, value }: { id: number; value: number }) => interactionsApi.rate(id, value), onSuccess: () => qc.invalidateQueries({ queryKey: ["ratings"] }) });
  const markWatched = useMutation({ mutationFn: interactionsApi.markWatched, onSuccess: () => qc.invalidateQueries({ queryKey: ["history"] }) });
  return { watchlist: { ...watchlist, data: watchlist.data ?? { items: [], page: 1, total: 0, total_pages: 0 } }, history: { ...history, data: history.data ?? { items: [], page: 1, total: 0, total_pages: 0 } }, ratings: { ...ratings, data: ratings.data ?? { items: [], page: 1, total: 0, total_pages: 0 } }, add, remove, rate, markWatched };
}
