"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "./AuthProvider";

// Ekran logowania / rejestracji. Jeden formularz, przelacznik trybu.
// Pokazywany zamiast dashboardu, gdy nikt nie jest zalogowany (patrz AuthGate).
export function AuthPanel() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLogin = mode === "login";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (isLogin) await login(email.trim(), password);
      else await register(email.trim(), password);
      // sukces -> AuthProvider ustawil usera, AuthGate przelaczy na dashboard
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cos poszlo nie tak");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="cyber-chamfer border border-border bg-card p-6 sm:p-8">
        <p className="mb-1 font-mono text-xs uppercase tracking-[0.2em] text-accent">
          <span className="text-muted-foreground">$</span>{" "}
          {isLogin ? "./auth --login" : "./auth --register"}
        </p>
        <h2 className="mb-6 font-display text-2xl font-black uppercase tracking-widest text-foreground">
          {isLogin ? "Zaloguj sie" : "Zaloz konto"}
        </h2>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              email
            </span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ty@example.com"
              className="cyber-chamfer-sm border border-border bg-[#12121a] px-3 py-2 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent focus:shadow-glow"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              haslo {isLogin ? "" : "(min. 8 znakow)"}
            </span>
            <input
              type="password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="cyber-chamfer-sm border border-border bg-[#12121a] px-3 py-2 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent focus:shadow-glow"
            />
          </label>

          {error && (
            <p className="cyber-chamfer-sm border border-destructive px-3 py-2 font-mono text-xs text-destructive">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="cyber-chamfer-sm border border-accent bg-accent/10 px-4 py-2.5 font-mono text-sm uppercase tracking-wider text-accent transition-all hover:shadow-glow disabled:opacity-50"
          >
            {busy ? "..." : isLogin ? "wejdz" : "utworz konto"}
          </button>
        </form>

        <button
          onClick={() => {
            setMode(isLogin ? "register" : "login");
            setError(null);
          }}
          className="mt-5 font-mono text-xs text-muted-foreground transition-colors hover:text-accent-tertiary"
        >
          {isLogin
            ? "// nie masz konta? zaloz je →"
            : "// masz juz konto? zaloguj sie →"}
        </button>
      </div>
    </div>
  );
}
