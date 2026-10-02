import { apiFetch } from "./client";

export type CalendarStartResponse = {
  authorization_url?: string | null;
  reminder_created: boolean;
  message: string;
};

export type CalendarReminder = {
  movie_id: number;
  google_event_id: string;
  release_date: string;
  created_at: string;
  created: boolean;
};

export const calendarApi = {
  start: (movieId: number) => apiFetch<CalendarStartResponse>(`/calendar/oauth/start?movie_id=${movieId}`),
  addReminder: (movieId: number) => apiFetch<CalendarReminder>("/calendar/reminders", { method: "POST", body: JSON.stringify({ movie_id: movieId }) }),
};
