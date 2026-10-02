export type Genre = { id: number; tmdb_id: number; name: string };
export type Movie = {
  id: number; tmdb_id: number; title: string; overview?: string | null; release_date?: string | null;
  runtime?: number | null; poster_path?: string | null; backdrop_path?: string | null; vote_average?: number | null;
  vote_count?: number | null; popularity?: number | null; original_language?: string | null; genres: Genre[];
};
export type MoviePage = { items: Movie[]; page: number; total: number; total_pages: number };
export type Recommendation = Movie & { score: number; reason_type: string; reason_value?: string | null };
export type Rating = { movie_id: number; rating: number; movie: Movie };
export type RatingPage = { items: Rating[]; page: number; total: number; total_pages: number };
export type WatchlistItem = { movie_id: number; created_at: string; movie: Movie };
export type WatchlistPage = { items: WatchlistItem[]; page: number; total: number; total_pages: number };
export type HistoryItem = { movie_id: number; watched_at: string; movie: Movie };
export type HistoryPage = { items: HistoryItem[]; page: number; total: number; total_pages: number };
export type Preferences = { preferred_genres: number[]; preferred_languages: string[]; onboarding_complete: boolean };
export type User = { id: string; email: string | null };
export type Profile = { id: string; email: string | null; avatar_type?: "upload" | "preset" | null; avatar_id?: string | null; avatar_url?: string | null; has_uploaded_avatar?: boolean };
export type TokenResponse = { access_token: string; token_type: string; refresh_token?: string | null };
export type RegisterResponse = { access_token?: string | null; token_type: string; refresh_token?: string | null; confirmation_required?: boolean; message?: string | null };
