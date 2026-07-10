import { Portfolio, costBasis } from "../lib/api";

// Formatuje liczbe jako walute (bez symbolu - to koszt wejscia w USD).
const fmt = (n: number) =>
  n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function PortfolioCard({ portfolio }: { portfolio: Portfolio }) {
  return (
    <article className="group relative">
      {/* Narozne akcenty HUD - 4 male kaciki w rogach karty */}
      <span className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b-2 border-l-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b-2 border-r-2 border-accent" />

      <div className="cyber-chamfer border border-border bg-card transition-all duration-300 group-hover:border-accent group-hover:shadow-glow">
        {/* Pasek terminala z kropkami "sygnalizacji" */}
        <header className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-2">
          <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#ffcc00]" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          <span className="ml-2 truncate font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            ~/portfolios/{portfolio.id}
          </span>
        </header>

        <div className="p-5">
          <h2 className="font-display text-xl font-bold uppercase tracking-wide text-foreground text-glow">
            {portfolio.name}
          </h2>

          {/* Pozycje */}
          <div className="mt-4 space-y-1">
            {portfolio.positions.length === 0 ? (
              <p className="font-mono text-sm text-muted-foreground">
                <span className="text-accent">$</span> brak pozycji — pusty portfel
              </p>
            ) : (
              <>
                <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-border pb-1 font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                  <span>Ticker</span>
                  <span className="text-right">Ilosc</span>
                  <span className="text-right">Cena</span>
                </div>
                {portfolio.positions.map((pos) => (
                  <div
                    key={pos.id}
                    className="grid grid-cols-[1fr_auto_auto] gap-4 py-1 font-mono text-sm"
                  >
                    <span className="font-bold text-accent-tertiary">{pos.ticker}</span>
                    <span className="text-right text-foreground">{fmt(pos.quantity)}</span>
                    <span className="text-right text-muted-foreground">{fmt(pos.buy_price)}</span>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Podsumowanie - koszt wejscia */}
          <footer className="mt-4 flex items-baseline justify-between border-t border-border pt-3">
            <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
              Koszt wejscia
            </span>
            <span className="font-display text-lg font-bold text-accent text-glow">
              ${fmt(costBasis(portfolio))}
            </span>
          </footer>
        </div>
      </div>
    </article>
  );
}
