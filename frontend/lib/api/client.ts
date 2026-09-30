const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const API_URL = (configuredApiUrl || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "")).replace(/\/$/, "");

export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }

export function getToken() { if (typeof window === "undefined") return null; return window.localStorage.getItem("cinematch_access_token"); }
export function setToken(token: string) { window.localStorage.setItem("cinematch_access_token", token); }
export function clearToken() { window.localStorage.removeItem("cinematch_access_token"); }

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (!API_URL) {
    throw new ApiError(0, "The frontend API URL is not configured. Set NEXT_PUBLIC_API_URL and rebuild.");
  }
  const headers = new Headers(init.headers); headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = getToken(); if (token) headers.set("Authorization", `Bearer ${token}`);
  const url = `${API_URL}/api${path}`;
  let response: Response;
  try {
    response = await fetch(url, { ...init, headers, cache: "no-store" });
  } catch (error) {
    // Keep tokens out of diagnostics while making the common local setup
    // failure actionable in the browser console and UI.
    console.error("[CineMatch API] network failure", {
      method: init.method || "GET",
      path,
      message: error instanceof Error ? error.message : "Network request failed",
    });
    throw new ApiError(0, "Unable to connect to the backend. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try { const body = await response.json(); if (typeof body.detail === "string") message = body.detail; } catch { /* safe fallback */ }
    console.error("[CineMatch API] request failed", { method: init.method || "GET", path, status: response.status, message });
    if (response.status === 401) clearToken();
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
