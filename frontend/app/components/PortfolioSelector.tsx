"use client";

import { usePortfoliosContext } from "./PortfoliosProvider";

// Jeden, wspolny wybor portfela dla calej zakladki "Moj portfel". Steruje
// selectedId w PortfoliosProvider, wiec wszystkie sekcje analityczne ponizej
// (analiza / realna / ryzyko / zachowanie / rebalans) patrza na TEN SAM portfel.
// Chowa sie przy jednym portfelu - nie ma czego wybierac.
export function PortfolioSelector() {
  const { portfolios, selectedId, setSelectedId } = usePortfoliosContext();

  if (!portfolios || portfolios.length <= 1) return null;

  return (
    <div className="cyber-chamfer border border-border bg-card px-4 py-3">
      <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
        <span className="text-accent">$</span> wybierz portfel — analiza ponizej liczy sie dla niego
      </p>
      <div className="flex flex-wrap gap-1">
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
    </div>
  );
}
