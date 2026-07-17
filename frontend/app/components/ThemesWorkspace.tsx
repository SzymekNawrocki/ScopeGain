"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createTheme,
  deleteObservation,
  deleteTheme,
  getThemeReckoning,
  getThemes,
  Observation,
  Reckoning,
  ReckoningRow,
  Theme,
  toggleObservationActed,
} from "../lib/api";
import { AddObservationForm } from "./AddObservationForm";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { SectionLabel } from "./ui/SectionLabel";
import { pnlColor, withSign } from "../lib/format";

const chip = (active: boolean) =>
  `cyber-chamfer-sm border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
    active
      ? "border-accent bg-accent/10 text-accent shadow-glow"
      : "border-border text-muted-foreground hover:border-accent hover:text-accent"
  }`;

// Tryb "Tematy": koszyki kuratorowane (ADR-0002). Tu zyje srodek petli decyzji:
// zapisany TYP (teza + uniewaznienie) i jego ROZLICZENIE (Etap 5) - hit rate na
// calej puli, neutralnie, nigdy "trzeba bylo kupic".
export function ThemesWorkspace() {
  const [themes, setThemes] = useState<Theme[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    getThemes()
      .then((list) => {
        setThemes(list);
        setSelectedId((cur) =>
          cur !== null && list.some((t) => t.id === cur) ? cur : list[0]?.id ?? null,
        );
      })
      .catch((e) => setError(e.message ?? "Blad pobierania"));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const selected = themes?.find((t) => t.id === selectedId) ?? null;

  return (
    <section>
      <SectionLabel>Twoje tematy</SectionLabel>
      <p className="mb-5 max-w-2xl font-mono text-sm leading-relaxed text-muted-foreground">
        Twoje pomysły inwestycyjne jako koszyki. Do każdej spółki zapisujesz{" "}
        <span className="text-accent">tezę</span> i{" "}
        <span className="text-accent">unieważnienie</span> — a apka później rozlicza Cię z
        własnych typów (nie żeby żałować, tylko żeby zobaczyć swój hit rate).
      </p>

      {error && (
        <StatusPanel variant="error">
          <p className="text-foreground">{error}</p>
        </StatusPanel>
      )}

      {/* Pasek tematow + tworzenie */}
      <div className="mb-5 flex flex-wrap items-center gap-2">
        {(themes ?? []).map((t) => (
          <button key={t.id} onClick={() => setSelectedId(t.id)} className={chip(selectedId === t.id)}>
            {t.name}
            <span className="ml-2 text-[11px] text-muted-foreground">{t.observations.length}</span>
          </button>
        ))}
        <NewThemeButton onCreated={reload} onSelect={setSelectedId} />
      </div>

      {themes && themes.length === 0 ? (
        <StatusPanel variant="empty">
          <p>
            <span className="text-accent">$</span> brak tematów. Utwórz pierwszy albo dodaj
            spółkę z zakładki <span className="text-accent">Odkrywaj</span>.
          </p>
        </StatusPanel>
      ) : (
        selected && <ThemeDetail theme={selected} onChanged={reload} onDeleted={reload} />
      )}
    </section>
  );
}

function NewThemeButton({
  onCreated,
  onSelect,
}: {
  onCreated: () => void;
  onSelect: (id: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    try {
      const t = await createTheme(name.trim());
      setName("");
      setOpen(false);
      onCreated();
      onSelect(t.id);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className={chip(false)}>
        + nowy temat
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-1">
      <input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="nazwa (Uran)"
        maxLength={100}
        className="cyber-chamfer-sm w-32 border border-border bg-[#0a0a0f] px-2 py-1.5 font-mono text-sm text-accent outline-none focus:border-accent"
      />
      <button type="submit" disabled={busy} className={chip(true)}>
        utwórz
      </button>
      <button type="button" onClick={() => setOpen(false)} className={chip(false)}>
        x
      </button>
    </form>
  );
}

// --- Szczegoly tematu: obserwacje + rozliczenie ----------------------------

function ThemeDetail({
  theme,
  onChanged,
  onDeleted,
}: {
  theme: Theme;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const [reckoning, setReckoning] = useState<Reckoning | null>(null);
  const [adding, setAdding] = useState(false);

  const loadReckoning = useCallback(() => {
    getThemeReckoning(theme.id)
      .then(setReckoning)
      .catch(() => setReckoning(null));
  }, [theme.id]);

  useEffect(() => {
    loadReckoning();
  }, [loadReckoning, theme.observations.length]);

  async function removeTheme() {
    await deleteTheme(theme.id);
    onDeleted();
  }

  return (
    <TerminalWindow
      title={theme.name}
      actions={
        <button
          onClick={removeTheme}
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground transition-colors hover:text-destructive"
          title="usuń temat"
        >
          [ usuń temat ]
        </button>
      }
    >
      {/* Rozliczenie: hit rate na calej puli */}
      {reckoning && reckoning.summary.total > 0 && (
        <ReckoningPanel reckoning={reckoning} />
      )}

      {/* Obserwacje (typy) */}
      {theme.observations.length > 0 ? (
        <ul className="space-y-2">
          {theme.observations.map((o) => (
            <ObservationRow
              key={o.id}
              obs={o}
              row={reckoning?.rows.find((r) => r.id === o.id) ?? null}
              onActed={() => toggleObservationActed(theme.id, o.id).then(onChanged)}
              onDelete={() => deleteObservation(theme.id, o.id).then(onChanged)}
            />
          ))}
        </ul>
      ) : (
        <p className="mb-3 font-mono text-sm text-muted-foreground">
          <span className="text-accent">$</span> temat pusty — dodaj spółkę poniżej albo z
          zakładki Odkrywaj.
        </p>
      )}

      {/* Dodanie reczne (np. Cameco, ktore ranking branzy pominal) */}
      {adding ? (
        <AddObservationForm
          themeId={theme.id}
          onDone={() => {
            setAdding(false);
            onChanged();
          }}
          onCancel={() => setAdding(false)}
        />
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="mt-3 w-full cyber-chamfer-sm border border-dashed border-border py-2 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
        >
          + dodaj spółkę ręcznie
        </button>
      )}
    </TerminalWindow>
  );
}

function ReckoningPanel({ reckoning }: { reckoning: Reckoning }) {
  const s = reckoning.summary;
  return (
    <div className="mb-5 border-b border-border pb-5">
      <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
        Rozliczenie — Twój hit rate na całej puli
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="Typów" value={String(s.total)} className="text-foreground" />
        <StatTile
          label="Na plusie / minusie"
          value={`${s.up} / ${s.down}`}
          hint={`policzalne: ${s.priced}`}
          className="text-accent-tertiary"
        />
        <StatTile label="Unieważnione" value={String(s.invalidated)} className="text-destructive" />
        <StatTile label="Kupione" value={`${s.acted} / ${s.total}`} className="text-accent" />
      </div>
      <p className="mt-3 font-mono text-xs italic leading-relaxed text-muted-foreground">
        * {reckoning.caveat}
      </p>
    </div>
  );
}

function ObservationRow({
  obs,
  row,
  onActed,
  onDelete,
}: {
  obs: Observation;
  row: ReckoningRow | null;
  onActed: () => void;
  onDelete: () => void;
}) {
  return (
    <li className="cyber-chamfer-sm border border-border bg-[#12121a] px-4 py-3">
      <div className="mb-1.5 flex items-baseline gap-3">
        <span className="font-mono text-sm font-bold text-accent">{obs.ticker}</span>
        <span className="truncate font-mono text-sm text-foreground">{obs.name}</span>
        <span className="font-mono text-[11px] uppercase tracking-wider text-accent-tertiary">
          {obs.origin}
        </span>
        <button
          onClick={onDelete}
          className="ml-auto shrink-0 font-mono text-xs text-muted-foreground transition-colors hover:text-destructive"
          title="usuń typ"
        >
          ✕
        </button>
      </div>

      {/* Teza + uniewaznienie + wejscie */}
      <p className="mb-1 font-mono text-xs leading-relaxed text-muted-foreground">
        <span className="text-foreground">Teza:</span> {obs.thesis}
      </p>
      <p className="font-mono text-xs leading-relaxed text-muted-foreground">
        <span className="text-foreground">Unieważnienie:</span>{" "}
        {obs.invalidation_price != null
          ? `poniżej $${obs.invalidation_price}`
          : obs.invalidation_note}
        {obs.entry_note && (
          <>
            {" · "}
            <span className="text-foreground">Wejście:</span> {obs.entry_note}
          </>
        )}
      </p>

      {/* Rozliczenie tego typu (neutralnie) */}
      {row && (
        <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border pt-2 font-mono text-xs">
          <span className="text-muted-foreground">
            dodano {row.added_at}
            {row.added_price != null && ` @ $${row.added_price}`}
          </span>
          {row.move_pct != null ? (
            <span className={pnlColor(row.move_pct)}>ruch {withSign(row.move_pct)}%</span>
          ) : (
            <span className="text-muted-foreground">ruch: brak ceny</span>
          )}
          {row.invalidation_triggered === true && (
            <span className="text-destructive">⚠ unieważnienie przebite</span>
          )}
          {row.invalidation_triggered === false && (
            <span className="text-accent">teza trzyma (próg nienaruszony)</span>
          )}
          {row.invalidation_triggered === null && (
            <span className="text-muted-foreground">warunek opisowy — oceń sam</span>
          )}
          <button
            onClick={onActed}
            className={`ml-auto cyber-chamfer-sm border px-2 py-0.5 uppercase tracking-wider transition-all ${
              obs.acted
                ? "border-accent bg-accent/10 text-accent"
                : "border-border text-muted-foreground hover:border-accent hover:text-accent"
            }`}
          >
            {obs.acted ? "✓ kupione" : "kupiłem?"}
          </button>
        </div>
      )}
    </li>
  );
}
