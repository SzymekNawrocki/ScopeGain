import { Tooltip } from "./Tooltip";

// Pojedynczy kafelek metryki: etykieta + duza wartosc + opcjonalna podpowiedz.
// Ten sam ksztalt byl zduplikowany jako StatTile (MarketScope) i RiskTile
// (PortfolioVsMarket) - teraz jedna wspolna wersja. Server Component.
//
// term: klucz ze slownika (lib/glossary.ts). Gdy podany, przy etykiecie
// pojawia sie dymek "?" tlumaczacy metryke - dzieki temu edukacja wchodzi do
// istniejacych kafelkow bez przepisywania ich. Bez term kafelek zachowuje sie
// dokladnie jak dotad.
export function StatTile({
  label,
  value,
  className,
  hint,
  term,
}: {
  label: string;
  value: string;
  className?: string;
  hint?: string;
  term?: string;
}) {
  return (
    <div className="cyber-chamfer-sm border border-border bg-[#12121a] px-4 py-3">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
        {label}
        {term && <Tooltip term={term} />}
      </p>
      <p className={`mt-1 font-display text-xl font-bold ${className ?? "text-foreground"}`}>
        {value}
      </p>
      {hint && <p className="mt-0.5 font-mono text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
