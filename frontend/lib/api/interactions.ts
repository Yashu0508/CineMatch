import { apiFetch } from "./client";
import { HistoryPage, Preferences, Rating, RatingPage, WatchlistPage } from "@/types";
export const interactionsApi = {
  watchlist: (page = 1) => apiFetch<WatchlistPage>(`/watchlist?page=${page}`),
  addWatchlist: (id: number) => apiFetch(`/watchlist/${id}`, { method: "POST" }),
  removeWatchlist: (id: number) => apiFetch(`/watchlist/${id}`, { method: "DELETE" }),
  ratings: (page = 1) => apiFetch<RatingPage>(`/ratings?page=${page}`),
  rate: (movie_id: number, rating: number) => apiFetch<Rating>("/ratings", { method: "POST", body: JSON.stringify({ movie_id, rating }) }),
  updateRating: (movie_id: number, rating: number) => apiFetch<Rating>(`/ratings/${movie_id}`, { method: "PUT", body: JSON.stringify({ movie_id, rating }) }),
  deleteRating: (id: number) => apiFetch(`/ratings/${id}`, { method: "DELETE" }),
  history: (page = 1) => apiFetch<HistoryPage>(`/history?page=${page}`),
  markWatched: (id: number) => apiFetch(`/history/${id}`, { method: "POST" }),
  preferences: () => apiFetch<Preferences>("/users/preferences"),
  updatePreferences: (body: Preferences) => apiFetch<Preferences>("/users/preferences", { method: "PUT", body: JSON.stringify(body) }),
};
