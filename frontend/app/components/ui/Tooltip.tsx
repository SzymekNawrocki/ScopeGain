"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { GLOSSARY } from "../../lib/glossary";

// Dymek "?" tlumaczacy metryke. Apka ma UCZYC, a nie tylko wyswietlac liczby:
// bez tego beta, P/E i drawdown to sciana cyfr, ktora user przewija.
//
// Czemu portal, a nie zwykly absolute? Bo karty uzywaja cyber-chamfer
// (clip-path ze scietymi rogami z design systemu), a clip-path PRZYCINA
// wszystkich potomkow - takze position:fixed. Dymek renderowany wewnatrz karty
// byl ucinany: najpierw z lewej, a po wysrodkowaniu - od dolu. Zadne
// pozycjonowanie tego nie obejdzie; dymek musi wyjsc poza poddrzewo karty.
//
// Reaguje na hover I na focus - samo :hover byloby niedostepne z klawiatury.

const SZEROKOSC = 288; // w-72; potrzebna do odbicia przy prawej krawedzi ekranu
const ODSTEP = 8;

export function Tooltip({ term }: { term: string }) {
  const entry = GLOSSARY[term];
  const [poz, setPoz] = useState<{ x: number; y: number } | null>(null);
  const trigger = useRef<HTMLSpanElement>(null);

  // Zamknij przy scrollu/resize - dymek jest position:fixed, wiec inaczej
  // zostalby "zawieszony" w miejscu, gdy tresc pod nim odjedzie.
  useEffect(() => {
    if (!poz) return;
    const zamknij = () => setPoz(null);
    window.addEventListener("scroll", zamknij, true);
    window.addEventListener("resize", zamknij);
    return () => {
      window.removeEventListener("scroll", zamknij, true);
      window.removeEventListener("resize", zamknij);
    };
  }, [poz]);

  if (!entry) return null;

  function pokaz() {
    const r = trigger.current?.getBoundingClientRect();
    if (!r) return;
    // Domyslnie wyrownanie do lewej krawedzi znaczka; przy prawej krawedzi
    // okna odbijamy w lewo, zeby dymek nie wyjechal poza ekran.
    const x = Math.min(r.left, window.innerWidth - SZEROKOSC - ODSTEP);
    setPoz({ x: Math.max(ODSTEP, x), y: r.bottom + 6 });
  }

  return (
    <>
      <span
        ref={trigger}
        tabIndex={0}
        role="button"
        aria-label={`Co to jest: ${entry.term}`}
        onMouseEnter={pokaz}
        onMouseLeave={() => setPoz(null)}
        onFocus={pokaz}
        onBlur={() => setPoz(null)}
        className="ml-1.5 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-border align-middle font-mono text-[10px] leading-none text-muted-foreground outline-none transition-colors hover:border-accent hover:text-accent focus-visible:border-accent focus-visible:text-accent focus-visible:shadow-glow"
      >
        ?
      </span>

      {poz &&
        createPortal(
          <div
            role="tooltip"
            // normal-case/tracking-normal: etykiety metryk sa uppercase z
            // duzym trackingiem - bez tego dymek dziedziczylby to przez
            // kaskade i definicja bylaby pisana wersalikami, czyli odwrotnie
            // do celu. pointer-events-none: nie przechwytuj klikniec.
            style={{ left: poz.x, top: poz.y, width: SZEROKOSC }}
            className="pointer-events-none fixed z-50 border border-accent/40 bg-[#0a0a0f] p-3 normal-case tracking-normal shadow-glow"
          >
            <p className="mb-1.5 font-mono text-xs font-bold uppercase tracking-wider text-accent">
              {entry.term}
            </p>
            <p className="font-mono text-xs leading-relaxed text-foreground">
              {entry.what}
            </p>
            <p className="mt-2 font-mono text-xs leading-relaxed text-muted-foreground">
              {entry.why}
            </p>
            {entry.diy && (
              <p className="mt-2 border-t border-border pt-2 font-mono text-[11px] leading-relaxed text-accent-tertiary">
                {"// policz sam: "}
                <span className="text-muted-foreground">{entry.diy}</span>
              </p>
            )}
          </div>,
          document.body,
        )}
    </>
  );
}
