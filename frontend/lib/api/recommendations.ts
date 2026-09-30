import { apiFetch } from "./client";
import { Recommendation } from "@/types";
export const recommendationsApi = {
  forYou: (limit = 20) => apiFetch<Recommendation[]>(`/recommendations/for-you?limit=${limit}`),
  similar: (id: number, limit = 20) => apiFetch<Recommendation[]>(`/recommendations/similar/${id}?limit=${limit}`),
  becauseLiked: (id: number, limit = 20) => apiFetch<Recommendation[]>(`/recommendations/because-you-liked/${id}?limit=${limit}`),
};
