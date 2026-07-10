"use client";

import { FormEvent, useState } from "react";
import { addPosition } from "../lib/api";

// Zwijany formularz dodawania pozycji do konkretnego portfela.
export function AddPositionForm({
  portfolioId,
  onChanged,
}: {
  portfolioId: number;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [ticker, setTicker] = useState("");
  const [qty, setQty] = useState("");
  const [price, setPrice] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const quantity = parseFloat(qty);
    const buy_price = parseFloat(price);
    if (!ticker.trim() || !(quantity > 0) || !(buy_price > 0)) {
      setError("Podaj ticker, ilosc > 0 i cene > 0.");
      return;
    }
    setBusy(true);
    try {
      await addPosition(portfolioId, { ticker: ticker.trim().toUpperCase(), quantity, buy_price });
      setTicker("");
      setQty("");
      setPrice("");
      setOpen(false);
      onChanged();
    } catch (err) {
      // Tu laduje np. "Nie znaleziono spolki X na rynku" z walidacji backendu.
      setError(err instanceof Error ? err.message : "Blad dodawania");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-4 w-full cyber-chamfer-sm border border-dashed border-border py-2 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
      >
        + dodaj pozycje
      </button>
    );
  }

  const inputCls =
    "cyber-chamfer-sm border border-border bg-[#0a0a0f] px-2 py-1.5 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent";

  return (
    <form onSubmit={onSubmit} className="mt-4 space-y-2 border-t border-border pt-3">
      <input
        autoFocus
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="ticker (np. NVDA)"
        maxLength={10}
        className={`${inputCls} w-full uppercase`}
      />
      <div className="grid grid-cols-2 gap-2">
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
          placeholder="cena zakupu"
          inputMode="decimal"
          className={inputCls}
        />
      </div>
      {error && <p className="font-mono text-xs text-destructive">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="cyber-chamfer-sm flex-1 border border-accent bg-accent/10 py-1.5 font-mono text-xs uppercase tracking-wider text-accent transition-all hover:shadow-glow disabled:opacity-50"
        >
          {busy ? "sprawdzam rynek..." : "dodaj"}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setError(null);
          }}
          className="cyber-chamfer-sm border border-border px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-destructive hover:text-destructive"
        >
          anuluj
        </button>
      </div>
    </form>
  );
}
