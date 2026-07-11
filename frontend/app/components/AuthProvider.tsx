"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister, User } from "../lib/api";

// Jedno zrodlo prawdy o zalogowanym userze. Na starcie pyta /auth/me:
// jest cookie -> user, brak -> null. Login/register/logout aktualizuja stan,
// zeby cala apka (brama + pasek) natychmiast widziala zmiane.
type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthCtx | null>(null);

export function useAuth(): AuthCtx {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth musi byc uzyte wewnatrz AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  // loading = "jeszcze nie wiem, kto to" - zanim /auth/me odpowie, nie
  // pokazujemy ani dashboardu, ani ekranu logowania (unikamy migotania).
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setUser(await apiLogin(email, password));
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    setUser(await apiRegister(email, password));
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
