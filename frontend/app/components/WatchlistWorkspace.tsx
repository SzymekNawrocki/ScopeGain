"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import {
  addToWatchlist,
  getVerdictChanges,
  getWatchlist,
  Grade,
  refreshWatchlist,
  removeFromWatchlist,
  updateWatchNote,
  VerdictChange,
  WatchItem,
} from "../lib/api";
import { StatusPanel } from "./ui/StatusPanel";
import { TerminalWindow } from "./ui/TerminalWindow";

const GRADE: Record<Grade, { icon: string; label: string; text: string }> = {
  good: { icon: "🟢", label: "Warto rozważyć", text: "text-accent" },
  mixed: { icon: "🟡", label: "Na granicy", text: "text-[#ffcc00]" },
  bad: { icon: "🔴", label: "Nie warto", text: "text-destructive" },
};

function gradeText(g: Grade | null) {
  return g ? `${GRADE[g].icon} ${GRADE[g].label}` : "⚪ nie sprawdzono";
}

function day(iso: string | null) {
  return iso ? new Date(iso).toLocaleDateString("pl-PL") : "—";
}

export function WatchlistWorkspace() {
  const [items, setItems] = useState<WatchItem[] | null>(null);
  const [changes, setChanges] = useState<VerdictChange[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [ticker, setTicker] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    let current = true;
    Promise.all([getWatchlist(), getVerdictChanges()])
      .then(([w, c]) => {
        if (!current) return;
        setItems(w);
        setChanges(c);
      })
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Błąd");
    } finally {
      setBusy(false);
    }
  }

  function onAdd(e: FormEvent) {
    e.preventDefault();
    const t = ticker.trim().toUpperCase();
    if (!t) return;
    run(async () => {
      const added = await addToWatchlist(t, note);
      setItems((prev) => [...(prev ?? []), added].sort((a, b) => a.ticker.localeCompare(b.ticker)));
      setTicker("");
      setNote("");
    });
  }

  function onRefresh() {
    run(async () => {
      const out = await refreshWatchlist();
      setItems(out.items);
      setChanges(await getVerdictChanges());
    });
  }

  function onRemove(t: string) {
    run(async () => {
      await removeFromWatchlist(t);
      setItems((prev) => (prev ?? []).filter((i) => i.ticker !== t));
    });
  }

  function onNote(t: string, value: string) {
    run(async () => {
      const updated = await updateWatchNote(t, value);
      setItems((prev) => (prev ?? []).map((i) => (i.ticker === t ? updated : i)));
    });
  }

  return (
    <div className="space-y-6">
      <TerminalWindow title="Lista">
        <form onSubmit={onAdd} className="mb-5 flex flex-wrap gap-3">
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Ticker, np. KO"
            className="cyber-chamfer-sm w-36 border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none focus:border-accent"
          />
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Notatka (opcjonalnie)"
            maxLength={500}
            className="cyber-chamfer-sm min-w-60 flex-1 border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={busy}
            className="cyber-chamfer-sm border border-accent px-4 py-2 font-mono text-sm uppercase tracking-wider text-accent hover:bg-accent/10 disabled:opacity-50"
          >
            Dodaj
          </button>
          <button
            type="button"
            onClick={onRefresh}
            disabled={busy || !items?.length}
            className="cyber-chamfer-sm border border-accent-tertiary px-4 py-2 font-mono text-sm uppercase tracking-wider text-accent-tertiary hover:bg-accent-tertiary/10 disabled:opacity-50"
          >
            {busy ? "Pracuję…" : "Odśwież werdykty"}
          </button>
        </form>

        {error && <StatusPanel variant="error">{error}</StatusPanel>}
        {!items && !error && <StatusPanel variant="loading">Wczytuję listę…</StatusPanel>}
        {items && items.length === 0 && (
          <StatusPanel variant="empty">
            Lista jest pusta. Dodaj ticker albo kliknij „Obserwuj” na karcie spółki.
          </StatusPanel>
        )}

        {items && items.length > 0 && (
          <ul className="divide-y divide-border">
            {items.map((i) => (
              <li key={i.ticker} className="flex flex-wrap items-start gap-4 py-3 font-mono text-sm">
                <Link href={`/?t=${encodeURIComponent(i.ticker)}`} className="w-20 font-bold text-accent hover:underline">
                  {i.ticker}
                </Link>
                <span className={`w-40 ${i.grade ? GRADE[i.grade].text : "text-muted-foreground"}`}>
                  {gradeText(i.grade)}
                </span>
                <input
                  defaultValue={i.note}
                  onBlur={(e) => e.target.value !== i.note && onNote(i.ticker, e.target.value)}
                  placeholder="notatka"
                  maxLength={500}
                  className="min-w-48 flex-1 border-b border-transparent bg-transparent text-xs text-muted-foreground outline-none focus:border-accent"
                />
                <span className="text-xs text-muted-foreground">sprawdzono {day(i.checked_at)}</span>
                <button
                  onClick={() => onRemove(i.ticker)}
                  disabled={busy}
                  className="text-xs text-muted-foreground hover:text-destructive"
                >
                  usuń
                </button>
                {i.last_change && (
                  <p className="basis-full pl-24 text-xs text-accent-tertiary">
                    ostatnia zmiana {day(i.last_change.at)}: {gradeText(i.last_change.from_grade)} →{" "}
                    {gradeText(i.last_change.to_grade)}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </TerminalWindow>

      <TerminalWindow title="Zmiany werdyktów">
        {changes.length === 0 ? (
          <p className="font-mono text-xs text-muted-foreground">
            Jeszcze żadnych zmian. Pierwsze sprawdzenie spółki ustala punkt odniesienia; zmiana
            pojawi się, gdy werdykt się przesunie (np. po nowym raporcie).
          </p>
        ) : (
          <ul className="space-y-4">
            {changes.map((c, n) => (
              <li key={`${c.ticker}-${c.at}-${n}`} className="font-mono text-sm">
                <p>
                  <span className="font-bold text-accent">{c.ticker}</span>{" "}
                  <span className="text-muted-foreground">{day(c.at)}</span> ·{" "}
                  {gradeText(c.from_grade)} → {gradeText(c.to_grade)}
                </p>
                <ul className="ml-4 list-disc text-xs text-muted-foreground">
                  {c.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </TerminalWindow>
    </div>
  );
}
