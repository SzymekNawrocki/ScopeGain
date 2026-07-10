"use client";

import { FormEvent, useState } from "react";
import { createPortfolio } from "../lib/api";

// Zwijany formularz "nowy portfel". Domyslnie tylko przycisk; klik -> pole.
export function NewPortfolioForm({ onChanged }: { onChanged: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const n = name.trim();
    if (!n) return;
    setBusy(true);
    setError(null);
    try {
      await createPortfolio(n);
      setName("");
      setOpen(false);
      onChanged(); // odswiez liste portfeli u rodzica
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blad tworzenia");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="cyber-chamfer-sm mb-6 border border-border px-4 py-2 font-mono text-xs uppercase tracking-wider text-accent transition-all hover:border-accent hover:shadow-glow"
      >
        + nowy portfel
      </button>
    );
  }

  return (
    <form onSubmit={onSubmit} className="mb-6 flex flex-wrap items-center gap-2">
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-accent">
          &gt;
        </span>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="nazwa portfela"
          maxLength={100}
          className="cyber-chamfer-sm w-64 border border-border bg-[#12121a] py-2 pl-8 pr-3 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent focus:shadow-glow"
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className="cyber-chamfer-sm border border-accent bg-accent/10 px-4 py-2 font-mono text-xs uppercase tracking-wider text-accent transition-all hover:shadow-glow disabled:opacity-50"
      >
        {busy ? "..." : "utworz"}
      </button>
      <button
        type="button"
        onClick={() => {
          setOpen(false);
          setError(null);
        }}
        className="cyber-chamfer-sm border border-border px-4 py-2 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-destructive hover:text-destructive"
      >
        anuluj
      </button>
      {error && <span className="font-mono text-xs text-destructive">{error}</span>}
    </form>
  );
}
