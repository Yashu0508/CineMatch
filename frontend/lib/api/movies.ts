import { apiFetch } from "./client";
import { Movie, MoviePage } from "@/types";
export const moviesApi = {
  trending: (page = 1) => apiFetch<MoviePage>(`/movies/trending?page=${page}`),
  popular: (page = 1) => apiFetch<MoviePage>(`/movies/popular?page=${page}`),
  topRated: (page = 1) => apiFetch<MoviePage>(`/movies/top-rated?page=${page}`),
  upcoming: (page = 1) => apiFetch<MoviePage>(`/movies/upcoming?page=${page}`),
  search: (query: string, page = 1) => apiFetch<MoviePage>(`/movies/search?q=${encodeURIComponent(query)}&page=${page}`),
  detail: (id: number) => apiFetch<Movie>(`/movies/${id}`),
  similar: (id: number, page = 1) => apiFetch<MoviePage>(`/movies/${id}/similar?page=${page}`),
  related: (id: number, page = 1) => apiFetch<MoviePage>(`/movies/${id}/recommendations?page=${page}`),
};
