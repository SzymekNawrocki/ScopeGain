"use client";

import { GLOSSARY } from "../../lib/glossary";

// Dymek "?" tlumaczacy metryke. Apka ma UCZYC, a nie tylko wyswietlac liczby:
// bez tego VaR, beta i P/E to sciana cyfr, ktora user przewija.
//
// Czemu "use client", skoro nie ma stanu? Bo dymek musi reagowac na hover I na
// focus (klawiatura, czytnik ekranu). Samo :hover byloby niedostepne dla kogos,
// kto nie uzywa myszy. Cala mechanika to jednak CSS (group-hover/
// group-focus-within) - zero JS poza dyrektywa.
export function Tooltip({ term }: { term: string }) {
  const entry = GLOSSARY[term];
  if (!entry) return null;

  return (
    <span className="group relative ml-1.5 inline-block align-middle">
      <span
        tabIndex={0}
        role="button"
        aria-label={`Co to jest: ${entry.term}`}
        className="inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-border font-mono text-[10px] leading-none text-muted-foreground outline-none transition-colors hover:border-accent hover:text-accent focus-visible:border-accent focus-visible:text-accent focus-visible:shadow-glow"
      >
        ?
      </span>

      {/* pointer-events-none: dymek nie moze przechwytywac klikniec w tresc pod nim */}
      <span
        role="tooltip"
        className="pointer-events-none invisible absolute left-1/2 top-6 z-30 w-72 -translate-x-1/2 border border-accent/40 bg-[#0a0a0f] p-3 opacity-0 shadow-glow transition-all group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 sm:w-80"
      >
        <span className="mb-1.5 block font-mono text-xs font-bold uppercase tracking-wider text-accent">
          {entry.term}
        </span>
        <span className="block font-mono text-xs leading-relaxed text-foreground">
          {entry.what}
        </span>
        <span className="mt-2 block font-mono text-xs leading-relaxed text-muted-foreground">
          {entry.why}
        </span>
        {entry.diy && (
          <span className="mt-2 block border-t border-border pt-2 font-mono text-[11px] leading-relaxed text-accent-tertiary">
            {"// policz sam: "}
            <span className="text-muted-foreground">{entry.diy}</span>
          </span>
        )}
      </span>
    </span>
  );
}
