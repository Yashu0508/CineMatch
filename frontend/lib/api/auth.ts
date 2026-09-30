import { apiFetch } from "./client";
import { Credentials } from "@/lib/auth/types";
import { TokenResponse, User } from "@/types";
export const authApi = {
  register: (body: Credentials) => apiFetch<TokenResponse>("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: Credentials) => apiFetch<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => apiFetch<User>("/auth/me"),
};
