"use client";

import { FormEvent, useState } from "react";
import {
  addObservation,
  createTheme,
  ObservationInput,
  Theme,
} from "../lib/api";

// Formularz zapisania TYPU (obserwacji) do tematu. Uzywany z dwoch miejsc:
//  - Odkrywaj: kandydat jest znany (ticker/name/origin), temat wybierasz/tworzysz.
//  - Widok tematu: temat jest znany (themeId), spolke wpisujesz recznie.
// Teza obowiazkowa; Uniewaznienie obowiazkowe, ale moze byc CENA lub WARUNEK
// (co najmniej jedno - tego uczy dyscyplina: decyzja bez warunku porazki jest
// nierozliczalna). Data i cena z momentu dodania lecą automatem po stronie API.

const inputCls =
  "cyber-chamfer-sm border border-border bg-[#0a0a0f] px-2 py-1.5 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent";

const chip = (active: boolean) =>
  `cyber-chamfer-sm border px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-all ${
    active
      ? "border-accent bg-accent/10 text-accent shadow-glow"
      : "border-border text-muted-foreground hover:border-accent hover:text-accent"
  }`;

export function AddObservationForm({
  candidate,
  themeId: fixedThemeId,
  themes,
  onDone,
  onCancel,
}: {
  // Kandydat z Odkrywaj (ticker/name/origin ustalone). Brak -> wpis reczny.
  candidate?: { ticker: string; name: string; origin: string };
  // Temat ustalony (dodajesz wewnatrz tematu). Brak -> wybierasz/tworzysz nizej.
  themeId?: number;
  themes?: Theme[];
  onDone: (themeId: number) => void;
  onCancel: () => void;
}) {
  // Reczny wpis spolki (gdy brak kandydata - np. dokladasz Cameco, ktore
  // ranking branzy pominal).
  const [ticker, setTicker] = useState(candidate?.ticker ?? "");
  const [name, setName] = useState(candidate?.name ?? "");

  // Wybor tematu (gdy nie jest ustalony): istniejacy id albo "new".
  const [target, setTarget] = useState<number | "new" | null>(
    fixedThemeId ?? null,
  );
  const [newThemeName, setNewThemeName] = useState("");

  const [thesis, setThesis] = useState("");
  const [invalMode, setInvalMode] = useState<"price" | "note">("price");
  const [invalPrice, setInvalPrice] = useState("");
  const [invalNote, setInvalNote] = useState("");
  const [entryNote, setEntryNote] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const origin = candidate?.origin ?? "recznie";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const tick = ticker.trim().toUpperCase();
    const nm = name.trim() || tick;
    if (!tick) return setError("Podaj ticker spolki.");
    if (!thesis.trim()) return setError("Teza jest obowiazkowa — dlaczego to dodajesz?");

    const price = parseFloat(invalPrice);
    if (invalMode === "price" && !(price > 0))
      return setError("Podaj cene progu uniewaznienia (> 0) albo przelacz na warunek.");
    if (invalMode === "note" && !invalNote.trim())
      return setError("Opisz warunek uniewaznienia albo przelacz na cene.");

    // Ustal temat: istniejacy albo utworz nowy.
    let themeId = fixedThemeId ?? (typeof target === "number" ? target : null);
    if (themeId == null && target !== "new")
      return setError("Wybierz temat albo utworz nowy.");

    setBusy(true);
    try {
      if (themeId == null) {
        if (!newThemeName.trim()) {
          setError("Nazwij nowy temat.");
          setBusy(false);
          return;
        }
        const t = await createTheme(newThemeName.trim());
        themeId = t.id;
      }

      const payload: ObservationInput = {
        ticker: tick,
        name: nm,
        origin,
        thesis: thesis.trim(),
        invalidation_price: invalMode === "price" ? price : null,
        invalidation_note: invalMode === "note" ? invalNote.trim() : null,
        entry_note: entryNote.trim() || null,
      };
      await addObservation(themeId, payload);
      onDone(themeId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blad zapisu");
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="cyber-chamfer-sm mt-3 space-y-3 border border-accent/40 bg-[#12121a] p-4"
    >
      {/* Kogo zapisujemy + pochodzenie */}
      {candidate ? (
        <p className="font-mono text-sm text-foreground">
          <span className="text-accent">{candidate.ticker}</span> · {candidate.name}
          <span className="ml-2 font-mono text-[11px] uppercase tracking-wider text-accent-tertiary">
            {origin}
          </span>
        </p>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          <input
            autoFocus
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="ticker (CCJ)"
            maxLength={15}
            className={`${inputCls} uppercase`}
          />
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="nazwa (opcjonalnie)"
            className={`${inputCls} col-span-2`}
          />
        </div>
      )}

      {/* Wybor tematu (tylko gdy nie jest ustalony z gory) */}
      {fixedThemeId == null && (
        <div>
          <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
            Do tematu
          </p>
          <div className="flex flex-wrap gap-1">
            {(themes ?? []).map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTarget(t.id)}
                className={chip(target === t.id)}
              >
                {t.name}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setTarget("new")}
              className={chip(target === "new")}
            >
              + nowy
            </button>
          </div>
          {target === "new" && (
            <input
              value={newThemeName}
              onChange={(e) => setNewThemeName(e.target.value)}
              placeholder="nazwa tematu (np. Uran)"
              maxLength={100}
              className={`${inputCls} mt-2 w-full`}
            />
          )}
        </div>
      )}

      {/* Teza */}
      <div>
        <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
          Teza — dlaczego to dodajesz
        </p>
        <textarea
          value={thesis}
          onChange={(e) => setThesis(e.target.value)}
          placeholder="np. deficyt podazy uranu, kontrakty dlugoterminowe reaktorow"
          rows={2}
          className={`${inputCls} w-full resize-y`}
        />
      </div>

      {/* Uniewaznienie: cena LUB warunek */}
      <div>
        <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
          Uniewaznienie — przy czym uznam, ze sie myle
        </p>
        <div className="mb-2 flex gap-1">
          <button type="button" onClick={() => setInvalMode("price")} className={chip(invalMode === "price")}>
            cena progu
          </button>
          <button type="button" onClick={() => setInvalMode("note")} className={chip(invalMode === "note")}>
            warunek
          </button>
        </div>
        {invalMode === "price" ? (
          <input
            value={invalPrice}
            onChange={(e) => setInvalPrice(e.target.value)}
            placeholder="np. 55 (spadek ponizej = mylilem sie)"
            inputMode="decimal"
            className={`${inputCls} w-full`}
          />
        ) : (
          <textarea
            value={invalNote}
            onChange={(e) => setInvalNote(e.target.value)}
            placeholder="np. jesli deficyt uranu sie nie zmaterializuje do 2027"
            rows={2}
            className={`${inputCls} w-full resize-y`}
          />
        )}
      </div>

      {/* Wejscie - opcjonalne (nie gonic kursu) */}
      <div>
        <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
          Warunek wejscia — opcjonalnie
        </p>
        <input
          value={entryNote}
          onChange={(e) => setEntryNote(e.target.value)}
          placeholder="np. czekam na cofniecie do 60"
          className={`${inputCls} w-full`}
        />
      </div>

      {error && <p className="font-mono text-sm text-destructive">{error}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="cyber-chamfer-sm flex-1 border border-accent bg-accent/10 py-1.5 font-mono text-sm uppercase tracking-wider text-accent transition-all hover:shadow-glow disabled:opacity-50"
        >
          {busy ? "zapisuje..." : "zapisz typ"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="cyber-chamfer-sm border border-border px-3 py-1.5 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-destructive hover:text-destructive"
        >
          anuluj
        </button>
      </div>
    </form>
  );
}
