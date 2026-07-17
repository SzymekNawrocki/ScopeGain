"use client";

import { useState } from "react";

// Instrukcja dla kogos, kto wchodzi PIERWSZY raz. Tlumaczy, czym apka jest
// (dziennik inwestora, nie research), i prowadzi przez trzy tryby z paska:
// Odkrywaj -> Tematy -> Moj portfel. Zwijana - kto zna apke, chowa jednym
// klikiem (stan w pamieci, bez localStorage, zeby nie migotalo przy hydracji).
const STEPS: { num: string; tab: string; color: string; body: React.ReactNode }[] = [
  {
    num: "01",
    tab: "Odkrywaj",
    color: "text-accent",
    body: (
      <>
        Znajdź spółkę bez znajomości symbolu: <b className="text-foreground">przeglądaj po
        branży</b> lub rozbij ETF, albo <b className="text-foreground">szukaj po nazwie</b>.
        Zobaczysz, czym firma się zajmuje, jej ryzyko i wykres.
      </>
    ),
  },
  {
    num: "02",
    tab: "Tematy",
    color: "text-accent-secondary",
    body: (
      <>
        Zapisz swój pomysł: dodaj spółkę do tematu („Uran", „Kwanty") z{" "}
        <b className="text-foreground">tezą</b> (dlaczego) i{" "}
        <b className="text-foreground">unieważnieniem</b> (kiedy uznasz, że się mylisz).
        Apka później sprawdzi, czy miałeś rację.
      </>
    ),
  },
  {
    num: "03",
    tab: "Mój portfel",
    color: "text-accent-tertiary",
    body: (
      <>
        Śledź, co realnie masz: <b className="text-foreground">zysk po prowizji i podatku</b>,
        ryzyko (ile możesz stracić w zły dzień) i czy Twój timing kupna/sprzedaży Ci pomaga.
      </>
    ),
  },
];

export function HowItWorks() {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="cyber-chamfer-sm mb-10 border border-border px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
      >
        ? jak to działa
      </button>
    );
  }

  return (
    <section className="cyber-chamfer mb-10 border border-border bg-card p-6 sm:p-8">
      <div className="mb-4 flex items-center justify-between gap-4">
        <p className="font-mono text-sm uppercase tracking-[0.2em] text-accent">
          <span className="text-muted-foreground">//</span> jak to działa
        </p>
        <button
          onClick={() => setOpen(false)}
          aria-label="Zwiń instrukcję"
          className="font-mono text-xs uppercase tracking-wider text-muted-foreground transition-colors hover:text-destructive"
        >
          [ ukryj ]
        </button>
      </div>

      <p className="mb-6 max-w-3xl font-mono text-sm leading-relaxed text-muted-foreground">
        ScopeGain to Twój <span className="text-foreground">dziennik inwestora</span> — nie
        kolejny research (od tego masz internet), tylko miejsce, które{" "}
        <span className="text-foreground">pamięta Twoje decyzje</span> i{" "}
        <span className="text-foreground">uczciwie liczy Twoje wyniki</span>. Trzy kroki, po
        kolei przez zakładki u góry:
      </p>

      <ol className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {STEPS.map((s) => (
          <li key={s.num} className="cyber-chamfer-sm border border-border bg-background/40 p-4">
            <div className="mb-2 flex items-baseline gap-3">
              <span className={`font-display text-2xl font-black ${s.color}`}>{s.num}</span>
              <span className="font-mono text-sm uppercase tracking-wider text-foreground">
                {s.tab}
              </span>
            </div>
            <p className="font-mono text-xs leading-relaxed text-muted-foreground">{s.body}</p>
          </li>
        ))}
      </ol>

      <p className="mt-6 max-w-3xl font-mono text-xs leading-relaxed text-muted-foreground">
        <span className="text-accent-tertiary">Ważne:</span> apka nigdy nie mówi „kup / sprzedaj"
        i <span className="text-foreground">nie zmyśla</span> — gdy czegoś nie wie, mówi to wprost.
        Jej wartość rośnie, im dłużej jej używasz (dziennik zapełnia się Twoimi decyzjami).
      </p>
    </section>
  );
}
