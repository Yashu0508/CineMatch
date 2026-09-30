const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }

export function getToken() { if (typeof window === "undefined") return null; return window.localStorage.getItem("cinematch_access_token"); }
export function setToken(token: string) { window.localStorage.setItem("cinematch_access_token", token); }
export function clearToken() { window.localStorage.removeItem("cinematch_access_token"); }

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers); headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = getToken(); if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}/api${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try { const body = await response.json(); if (typeof body.detail === "string") message = body.detail; } catch { /* safe fallback */ }
    if (response.status === 401) clearToken();
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
