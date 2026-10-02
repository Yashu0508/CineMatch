"use client";
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "@/lib/api/auth";
import { clearToken, getToken, setToken } from "@/lib/api/client";
import { Credentials } from "./types";
import { RegisterResponse, User } from "@/types";

type AuthContextValue = { user: User | null; loading: boolean; login: (c: Credentials) => Promise<void>; register: (c: Credentials) => Promise<RegisterResponse>; logout: () => void };
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { if (!getToken()) { setLoading(false); return; } authApi.me().then(setUser).catch(() => { clearToken(); setUser(null); }).finally(() => setLoading(false)); }, []);
  const authenticate = async (method: (c: Credentials) => Promise<{ access_token: string }>, credentials: Credentials) => { const token = await method(credentials); setToken(token.access_token); setUser(await authApi.me()); };
  const register = async (credentials: Credentials) => { const response = await authApi.register(credentials); if (response.access_token) { setToken(response.access_token); setUser(await authApi.me()); } return response; };
  const value = useMemo(() => ({ user, loading, login: (c: Credentials) => authenticate(authApi.login, c), register, logout: () => { clearToken(); setUser(null); } }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used within AuthProvider"); return context; }
