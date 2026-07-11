// Formatowanie liczb + kolory zysk/strata - wspolne dla kart portfela,
// panelu rynku i analizy, zeby nie powielac tej samej logiki w kazdym pliku.

export const fmt = (n: number) =>
  n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const withSign = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}`;

export const pnlColor = (n: number | null | undefined) =>
  n == null ? "text-muted-foreground" : n >= 0 ? "text-accent" : "text-destructive";

export const pnlSign = (n: number) => (n >= 0 ? "▲ +" : "▼ ");
