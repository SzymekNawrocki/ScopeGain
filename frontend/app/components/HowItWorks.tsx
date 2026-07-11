"use client";

import { useState } from "react";

// Onboarding: nowy uzytkownik ladowal na "terminalu" bez pojecia co apka robi
// ani od czego zaczac. Ten panel tlumaczy 3 kroki i sekcje "Rynek". Zwijany -
// wlasciciel, ktory zna apke, chowa go jednym klikiem (stan tylko w pamieci,
// bez localStorage, zeby nie migotalo przy hydracji).
const STEPS: [string, string, React.ReactNode][] = [
  [
    "01",
    "Stworz portfel",
    <>
      Kliknij <span className="text-accent">+ nowy portfel</span> i nazwij go
      (np. „Emerytura", „Spekulacje"). To Twoj koszyk pozycji.
    </>,
  ],
  [
    "02",
    "Dodaj pozycje",
    <>
      W karcie portfela podaj <span className="text-accent-tertiary">ticker</span>{" "}
      (AAPL, MSFT, VOO...), liczbe sztuk i cene zakupu. Ticker jest sprawdzany na
      rynku — literowka zostanie odrzucona.
    </>,
  ],
  [
    "03",
    "Czytaj analize",
    <>
      Sekcja <span className="text-accent-secondary">Analiza</span> liczy na zywo:
      wycene i P&amp;L netto (po prowizji i podatku Belka), ryzyko vs S&amp;P 500,
      korelacje i werdykt 🟢🟡🔴 — po ludzku, co z liczb wynika.
    </>,
  ],
];

export function HowItWorks() {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="cyber-chamfer-sm mb-12 border border-border px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
      >
        ? jak to dziala
      </button>
    );
  }

  return (
    <section className="cyber-chamfer mb-12 border border-border bg-card p-6 sm:p-8">
      <div className="mb-5 flex items-center justify-between gap-4">
        <p className="font-mono text-sm uppercase tracking-[0.2em] text-accent">
          <span className="text-muted-foreground">//</span> jak to dziala
        </p>
        <button
          onClick={() => setOpen(false)}
          aria-label="Zwin instrukcje"
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground transition-colors hover:text-destructive"
        >
          [ ukryj ]
        </button>
      </div>

      <p className="mb-6 max-w-2xl font-mono text-sm leading-relaxed text-muted-foreground">
        ScopeGain to terminal analizy Twojego portfela: dokladasz spolki, ktore
        masz, a apka pobiera kursy z rynku i mowi, ile realnie zarabiasz i czym
        ryzykujesz. Zacznij od trzech krokow:
      </p>

      <ol className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {STEPS.map(([num, title, body]) => (
          <li
            key={num}
            className="cyber-chamfer-sm border border-border bg-background/40 p-4"
          >
            <div className="mb-2 flex items-baseline gap-3">
              <span className="font-display text-2xl font-black text-accent">
                {num}
              </span>
              <span className="font-mono text-sm uppercase tracking-wider text-foreground">
                {title}
              </span>
            </div>
            <p className="font-mono text-xs leading-relaxed text-muted-foreground">
              {body}
            </p>
          </li>
        ))}
      </ol>

      <p className="mt-6 max-w-2xl font-mono text-xs leading-relaxed text-muted-foreground">
        <span className="text-accent-tertiary">Tip:</span> sekcja{" "}
        <span className="text-foreground">Rynek</span> to podglad dowolnej spolki
        (swiece + metryki) bez dodawania jej do portfela — do researchu, zanim
        kupisz.
      </p>
    </section>
  );
}
