// Blokowy panel stanu: ladowanie / blad / pusto. Ten sam "cyber-chamfer"
// container byl kopiowany osobno w page.tsx, MarketScope i PortfolioVsMarket -
// teraz jeden komponent z wariantem koloru. Server Component (brak stanu).
const VARIANT = {
  loading: "border border-border text-accent",
  error: "border-2 border-destructive text-destructive shadow-[0_0_20px_#ff336640]",
  empty: "border border-border text-muted-foreground",
} as const;

export function StatusPanel({
  variant,
  children,
}: {
  variant: keyof typeof VARIANT;
  children: React.ReactNode;
}) {
  return (
    <div className={`cyber-chamfer bg-card p-8 font-mono text-sm ${VARIANT[variant]}`}>
      {children}
    </div>
  );
}
