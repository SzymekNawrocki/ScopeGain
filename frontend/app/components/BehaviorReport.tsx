"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  addTransaction,
  BehaviorVerdict,
  deleteTransaction,
  getPortfolioBehavior,
  getTransactions,
  Portfolio,
  Severity,
  Transaction,
  TransactionSide,
} from "../lib/api";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatusPanel } from "./ui/StatusPanel";
import { fmt } from "../lib/format";

const SEV_DOT: Record<Severity, string> = {
  good: "bg-accent",
  warn: "bg-[#ffcc00]",
  bad: "bg-destructive",
};
const SEV_TEXT: Record<Severity, string> = {
  good: "text-accent",
  warn: "text-[#ffcc00]",
  bad: "text-destructive",
};

const usd = (n: number) => `${n < 0 ? "-" : ""}$${fmt(Math.abs(n))}`;
const today = () => new Date().toISOString().slice(0, 10);

// Sekcja "zachowanie" (12b): log kupna/sprzedazy + werdykt timingu sprzedazy.
// Atakuje behavior gap - czy sprzedales za wczesnie zwycieska spolke.
export function BehaviorReport({ portfolios }: { portfolios: Portfolio[] }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [behavior, setBehavior] = useState<BehaviorVerdict | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedId === null && portfolios.length > 0) {
      setSelectedId(portfolios[0].id);
    }
  }, [portfolios, selectedId]);

  const reload = useCallback((id: number) => {
    getTransactions(id)
      .then(setTxs)
      .catch((e) => setError(e.message ?? "Blad pobierania"));
    getPortfolioBehavior(id)
      .then(setBehavior)
      .catch(() => setBehavior(null));
  }, []);

  useEffect(() => {
    if (selectedId === null) return;
    setError(null);
    reload(selectedId);
  }, [selectedId, reload]);

  if (portfolios.length === 0) {
    return (
      <p className="font-mono text-sm text-muted-foreground">
        <span className="text-accent">$</span> zaloz portfel, zeby logowac transakcje i ocenic timing.
      </p>
    );
  }

  return (
    <div className="mb-12">
      <TerminalWindow title={`~/behavior${behavior ? `/${behavior.name}` : ""}`}>
        {/* Wybor portfela (jesli >1) */}
        {portfolios.length > 1 && (
          <div className="mb-5 flex flex-wrap gap-1">
            {portfolios.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedId(p.id)}
                className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
                  p.id === selectedId
                    ? "border-accent bg-accent/10 text-accent shadow-glow"
                    : "border-border text-muted-foreground hover:border-accent hover:text-accent"
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        )}

        <p className="mb-5 max-w-2xl font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent">$</span> zapisz swoje kupna i sprzedaze. Apka porowna
          cene <span className="text-foreground">sprzedazy</span> z dzisiejsza i powie, czy
          timing Ci pomogl, czy sprzedales za wczesnie (behavior gap — #1 przyczyna
          niedowazenia wyniku rynku).
        </p>

        {error && (
          <StatusPanel variant="error">
            <p className="text-foreground">{error}</p>
          </StatusPanel>
        )}

        {/* Werdykt zachowania (najpierw wniosek) */}
        {behavior && behavior.id === selectedId && <BehaviorPanel verdict={behavior} />}

        {/* Formularz + log transakcji */}
        {selectedId !== null && (
          <TransactionForm portfolioId={selectedId} onChanged={() => reload(selectedId)} />
        )}

        {txs.length > 0 && (
          <ul className="mt-5 space-y-1.5 border-t border-border pt-4">
            {txs.map((t) => (
              <li
                key={t.id}
                className="flex items-center gap-3 font-mono text-sm"
              >
                <span
                  className={`w-12 shrink-0 text-center text-xs font-bold uppercase ${
                    t.side === "SELL" ? "text-destructive" : "text-accent"
                  }`}
                >
                  {t.side}
                </span>
                <span className="w-16 shrink-0 font-bold text-foreground">{t.ticker}</span>
                <span className="text-muted-foreground">
                  {fmt(t.quantity)} × {usd(t.price)}
                </span>
                <span className="ml-auto text-xs text-muted-foreground">{t.executed_at}</span>
                <button
                  onClick={() =>
                    selectedId !== null &&
                    deleteTransaction(selectedId, t.id).then(() => reload(selectedId))
                  }
                  className="text-xs text-muted-foreground transition-colors hover:text-destructive"
                  title="usun transakcje"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </TerminalWindow>
    </div>
  );
}

// Panel werdyktu zachowania: ocena + "zostawione na stole" + wnioski + caveat.
function BehaviorPanel({ verdict }: { verdict: BehaviorVerdict }) {
  const g = verdict.grade;
  const left = verdict.total_left_on_table;
  return (
    <div className="cyber-chamfer-sm mb-5 border border-border bg-[#12121a] p-4">
      <div className="mb-3 flex items-center justify-between border-b border-border pb-3">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Werdykt zachowania — timing Twoich sprzedazy
        </p>
        <span className={`flex items-center gap-2 font-display text-sm font-bold ${SEV_TEXT[g]}`}>
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${SEV_DOT[g]}`} />
          {verdict.grade_label}
        </span>
      </div>

      {left !== 0 && (
        <p className="mb-3 font-mono text-sm">
          {left > 0 ? (
            <span className="text-destructive">
              Trzymajac sprzedane pozycje mialbys dzis o ok. {usd(left)} wiecej.
            </span>
          ) : (
            <span className="text-accent">
              Twoje wyjscia oszczedzily Ci ok. {usd(Math.abs(left))} (spadki po sprzedazy).
            </span>
          )}
        </p>
      )}

      <ul className="space-y-2.5">
        {verdict.findings.map((f, i) => (
          <li key={i} className="flex gap-3">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${SEV_DOT[f.severity]}`} />
            <div>
              <p className={`font-mono text-sm font-bold ${SEV_TEXT[f.severity]}`}>{f.title}</p>
              <p className="font-mono text-xs text-muted-foreground">{f.detail}</p>
            </div>
          </li>
        ))}
      </ul>

      <p className="mt-3 border-t border-border pt-3 font-mono text-xs italic text-muted-foreground">
        * {verdict.caveat}
      </p>
    </div>
  );
}

// Zwijany formularz logowania transakcji (kupno/sprzedaz + data).
function TransactionForm({
  portfolioId,
  onChanged,
}: {
  portfolioId: number;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [ticker, setTicker] = useState("");
  const [side, setSide] = useState<TransactionSide>("SELL");
  const [qty, setQty] = useState("");
  const [price, setPrice] = useState("");
  const [date, setDate] = useState(today());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const quantity = parseFloat(qty);
    const priceNum = parseFloat(price);
    if (!ticker.trim() || !(quantity > 0) || !(priceNum > 0) || !date) {
      setError("Podaj ticker, ilosc > 0, cene > 0 i date.");
      return;
    }
    setBusy(true);
    try {
      await addTransaction(portfolioId, {
        ticker: ticker.trim().toUpperCase(),
        side,
        quantity,
        price: priceNum,
        executed_at: date,
      });
      setTicker("");
      setQty("");
      setPrice("");
      setDate(today());
      setOpen(false);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blad zapisu");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-2 w-full cyber-chamfer-sm border border-dashed border-border py-2 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
      >
        + zapisz transakcje
      </button>
    );
  }

  const inputCls =
    "cyber-chamfer-sm border border-border bg-[#0a0a0f] px-2 py-1.5 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent";

  return (
    <form onSubmit={onSubmit} className="mt-2 space-y-2 border-t border-border pt-3">
      {/* BUY / SELL toggle */}
      <div className="flex gap-1">
        {(["BUY", "SELL"] as TransactionSide[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSide(s)}
            className={`cyber-chamfer-sm flex-1 border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
              s === side
                ? s === "SELL"
                  ? "border-destructive bg-destructive/10 text-destructive"
                  : "border-accent bg-accent/10 text-accent"
                : "border-border text-muted-foreground hover:border-accent hover:text-accent"
            }`}
          >
            {s === "BUY" ? "kupno" : "sprzedaz"}
          </button>
        ))}
      </div>
      <input
        autoFocus
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="ticker (np. NVDA)"
        maxLength={10}
        className={`${inputCls} w-full uppercase`}
      />
      <div className="grid grid-cols-3 gap-2">
        <input
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          placeholder="ilosc"
          inputMode="decimal"
          className={inputCls}
        />
        <input
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          placeholder="cena"
          inputMode="decimal"
          className={inputCls}
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          max={today()}
          className={inputCls}
        />
      </div>
      {error && <p className="font-mono text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="cyber-chamfer-sm flex-1 border border-accent bg-accent/10 py-1.5 font-mono text-sm uppercase tracking-wider text-accent transition-all hover:shadow-glow disabled:opacity-50"
        >
          {busy ? "sprawdzam rynek..." : "zapisz"}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setError(null);
          }}
          className="cyber-chamfer-sm border border-border px-3 py-1.5 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-destructive hover:text-destructive"
        >
          anuluj
        </button>
      </div>
    </form>
  );
}
