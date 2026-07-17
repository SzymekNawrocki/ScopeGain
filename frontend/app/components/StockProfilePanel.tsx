import { StockProfile } from "../lib/api";
import { Tooltip } from "./ui/Tooltip";

// Profil spolki: czym ona JEST, zanim spojrzysz na kurs.
// Dotad apka pokazywala sam wykres - user widzial slupki, nie wiedzac, czy
// patrzy na kopalnie uranu, czy na producenta lodow.

function bigMoney(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1e12) return `$${(n / 1e12).toFixed(1)} bln`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)} mld`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)} mln`;
  return `$${n.toFixed(0)}`;
}

function Pole({
  label,
  value,
  term,
}: {
  label: string;
  value: string;
  term?: string;
}) {
  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
        {label}
        {term && <Tooltip term={term} />}
      </p>
      <p className="mt-0.5 font-mono text-sm text-foreground">{value}</p>
    </div>
  );
}

export function StockProfilePanel({ profile }: { profile: StockProfile }) {
  return (
    <div className="cyber-chamfer-sm mb-4 border border-border bg-[#12121a] p-4">
      <div className="mb-3 flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-border pb-3">
        <h3 className="font-display text-lg font-bold uppercase tracking-wide text-foreground">
          {profile.name}
        </h3>
        <span className="font-mono text-xs text-accent">{profile.ticker}</span>
        {profile.currency && (
          // Waluta jest istotna przy cross-listingu: CCJ notowane w USD, a
          // CCO.TO (ta sama firma) w CAD.
          <span className="font-mono text-[11px] text-muted-foreground">
            {profile.currency}
          </span>
        )}
      </div>

      <div className="mb-3 grid grid-cols-2 gap-x-4 gap-y-3 md:grid-cols-4">
        <Pole
          label="Branza"
          value={profile.industry ?? profile.sector ?? "—"}
          term="sektor"
        />
        <Pole label="Kapitalizacja" value={bigMoney(profile.market_cap)} term="mcap" />
        <Pole
          label="P/E"
          value={
            profile.trailing_pe && profile.trailing_pe > 0
              ? profile.trailing_pe.toFixed(1)
              : "—"
          }
          term="pe"
        />
        <Pole
          label="Marza zysku"
          value={
            profile.profit_margins != null
              ? `${(profile.profit_margins * 100).toFixed(1)}%`
              : "—"
          }
          term="marza"
        />
      </div>

      {profile.summary && (
        // line-clamp: opisy z Yahoo potrafia miec pol strony. Trzy linie
        // wystarcza, zeby wiedziec, czym firma sie zajmuje.
        <p className="line-clamp-3 font-mono text-xs leading-relaxed text-muted-foreground">
          {profile.summary}
        </p>
      )}
    </div>
  );
}
