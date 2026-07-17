import { ReactNode } from "react";
import { Severity, VerdictFinding } from "../../lib/api";

// Wspolny panel werdyktu: kropka + ocena + lista wnioskow. Byl skopiowany w
// PortfolioVsMarket i BehaviorReport; werdykt spolki bylby trzecia kopia.
//
// WAZNE: ocene slowna bierzemy WYLACZNIE z gradeLabel (czyli z backendu).
// Poprzednio PortfolioVsMarket mial wlasny slownik {good:"MOCNY", warn:
// "PRZECIETNY", bad:"SLABY"} kluczowany po severity - i ignorowal grade_label.
// Dla werdyktu RYZYKA spolki wyswietliloby to "ocena: MOCNY" przy Cameco,
// czyli porade zakupu, ktorej apka swiadomie nie wydaje (ADR-0001) - mimo
// poprawnego backendu. Dlatego tego slownika tu NIE MA i byc nie moze:
// jedno zrodlo prawdy dla oceny slownej to odpowiedz API.

const SEV_DOT: Record<Severity, string> = {
  good: "bg-accent",
  warn: "bg-[#ffcc00]",
  bad: "bg-destructive",
};

const SEV_TEXT: Record<Severity, string> = {
  good: "text-accent",
  warn: "text-[#ffcc00]",
  bad: "text-destructive",
};

export { SEV_DOT, SEV_TEXT };

export function VerdictFindings({
  title,
  grade,
  gradeLabel,
  findings,
  caveat,
  dataGaps,
  children,
}: {
  title: string;
  grade: Severity;
  gradeLabel: string;
  findings: VerdictFinding[];
  caveat?: string;
  dataGaps?: string[];
  children?: ReactNode;
}) {
  return (
    <div className="cyber-chamfer-sm mb-5 border border-border bg-[#12121a] p-4">
      <div className="mb-3 flex items-center justify-between gap-3 border-b border-border pb-3">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          {title}
        </p>
        <span
          className={`flex shrink-0 items-center gap-2 font-display text-sm font-bold uppercase ${SEV_TEXT[grade]}`}
        >
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${SEV_DOT[grade]}`} />
          {gradeLabel}
        </span>
      </div>

      {children}

      <ul className="space-y-2.5">
        {findings.map((f, i) => (
          <li key={i} className="flex gap-3">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${SEV_DOT[f.severity]}`} />
            <div>
              <p className={`font-mono text-sm font-bold ${SEV_TEXT[f.severity]}`}>{f.title}</p>
              <p className="font-mono text-xs text-muted-foreground">{f.detail}</p>
            </div>
          </li>
        ))}
      </ul>

      {/* Czego apka NIE wiedziala. Werdykt z 2 regul nie moze wygladac tak
          samo pewnie jak z 5 - bez tego bylby to falsz przez przemilczenie. */}
      {dataGaps && dataGaps.length > 0 && (
        <p className="mt-3 border-t border-border pt-3 font-mono text-xs text-muted-foreground">
          <span className="text-accent-tertiary">{"// brak danych:"}</span>{" "}
          {dataGaps.join(", ")} — te reguly pominieto.
        </p>
      )}

      {/* Zastrzezenie MUSI byc przy werdykcie, nie w stopce strony: werdykt
          o pojedynczej spolce czyta sie jak rekomendacja duzo mocniej niz
          werdykt o wlasnym portfelu. */}
      {caveat && (
        <p className="mt-3 border-t border-border pt-3 font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent-tertiary">{"// zastrzezenie:"}</span> {caveat}
        </p>
      )}
    </div>
  );
}
