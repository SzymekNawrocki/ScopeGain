"use client";

// Mapa cieplna korelacji. Kolor komorki niesie sens:
// niska korelacja (blisko 0/ujemna) = neon zielony = dobra dywersyfikacja,
// wysoka (blisko +1) = magenta = spolki chodza razem = skupione ryzyko.
function cellBg(v: number): string {
  const t = Math.max(0, Math.min(1, (v + 1) / 2)); // -1..1 -> 0..1
  const low = [0, 255, 136]; // #00ff88 (zielen)
  const high = [255, 0, 255]; // #ff00ff (magenta)
  const mix = low.map((c, i) => Math.round(c + (high[i] - c) * t));
  return `rgba(${mix[0]}, ${mix[1]}, ${mix[2]}, 0.20)`;
}

export function CorrelationMatrix({
  tickers,
  matrix,
}: {
  tickers: string[];
  matrix: number[][];
}) {
  if (tickers.length < 2) {
    return (
      <p className="font-mono text-sm text-muted-foreground">
        <span className="text-accent">$</span> korelacje potrzebuja min. 2 roznych spolek w portfelu.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1 font-mono text-sm">
        <thead>
          <tr>
            <th className="p-2" />
            {tickers.map((t) => (
              <th key={t} className="p-2 font-bold uppercase text-accent-tertiary">
                {t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={tickers[i]}>
              <th className="p-2 text-left font-bold uppercase text-accent-tertiary">
                {tickers[i]}
              </th>
              {row.map((v, j) => (
                <td
                  key={j}
                  className="cyber-chamfer-sm min-w-[3.5rem] p-2 text-center font-bold"
                  style={{
                    background: i === j ? "rgba(42,42,58,0.4)" : cellBg(v),
                    color: i === j ? "#9ca3af" : "#e0e0e0",
                  }}
                >
                  {v.toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
