import { Argument, BlockId, CompanyAnalysis, Criterion, Grade, Outcome } from "../lib/api";

// The company card: verdict first, then pros/cons, then every criterion with its
// threshold and source. Data gaps sit above the blocks, not in a footer, so a
// verdict built from few criteria never looks as certain as a full one.

const GRADE_STYLE: Record<Grade, { dot: string; text: string; ring: string }> = {
  good: { dot: "bg-accent", text: "text-accent", ring: "border-accent" },
  mixed: { dot: "bg-[#ffcc00]", text: "text-[#ffcc00]", ring: "border-[#ffcc00]" },
  bad: { dot: "bg-destructive", text: "text-destructive", ring: "border-destructive" },
};

const GRADE_ICON: Record<Grade, string> = { good: "🟢", mixed: "🟡", bad: "🔴" };

const OUTCOME_ICON: Record<Outcome, string> = { pass: "✅", warn: "🟡", fail: "❌", na: "⚪" };
const OUTCOME_TEXT: Record<Outcome, string> = {
  pass: "text-accent",
  warn: "text-[#ffcc00]",
  fail: "text-destructive",
  na: "text-muted-foreground",
};

const BLOCK_ORDER: BlockId[] = ["trust", "dividend", "valuation", "health"];

export function CompanyCard({ analysis }: { analysis: CompanyAnalysis }) {
  const g = GRADE_STYLE[analysis.grade];
  return (
    <div className="space-y-5">
      {/* VERDICT */}
      <section className={`cyber-chamfer-sm border-2 ${g.ring} bg-card p-5`}>
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h2 className="font-display text-2xl font-bold uppercase tracking-wide text-foreground">
            {analysis.name}
          </h2>
          <span className="font-mono text-sm text-accent">{analysis.ticker}</span>
          {analysis.sic_description && (
            <span className="font-mono text-xs text-muted-foreground">
              {analysis.sic_description}
            </span>
          )}
        </div>
        <p className={`mt-4 flex items-center gap-3 font-display text-3xl font-black uppercase ${g.text}`}>
          <span aria-hidden>{GRADE_ICON[analysis.grade]}</span>
          {analysis.label}
        </p>
        <p className="mt-2 font-mono text-sm text-foreground">{analysis.reason}</p>
        <p className="mt-3 font-mono text-xs text-muted-foreground">
          Sprawdzono {analysis.coverage.checked} z {analysis.coverage.applicable} kryteriów ·
          raport roczny za okres do {analysis.fiscal_year_end ?? "—"} · {analysis.years_of_data} lat
          danych SEC
        </p>
        <p className="mt-3 border-t border-border pt-3 font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent-tertiary">{"// zastrzeżenie:"}</span> {analysis.caveat}
        </p>
      </section>

      {/* DATA GAPS */}
      {analysis.data_gaps.length > 0 && (
        <section className="cyber-chamfer-sm border border-border bg-card p-4">
          <p className="mb-2 font-mono text-xs uppercase tracking-[0.2em] text-accent-tertiary">
            Braki danych — tych kryteriów nie sprawdzono
          </p>
          <ul className="space-y-1 font-mono text-xs text-muted-foreground">
            {analysis.data_gaps.map((gap) => (
              <li key={gap.criterion}>
                ⚪ {gap.criterion}
                {gap.missing.length > 0 && <span> — brakuje: {gap.missing.join(", ")}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* PROS / CONS */}
      <section className="grid gap-4 md:grid-cols-2">
        <ArgumentList title="Za" items={analysis.pros} accent="text-accent" />
        <ArgumentList title="Przeciw" items={analysis.cons} accent="text-destructive" />
      </section>

      {/* BLOCKS */}
      {BLOCK_ORDER.map((id) => {
        const block = analysis.blocks[id];
        if (!block) return null;
        const status = block.status === "na" ? null : GRADE_STYLE[block.status];
        return (
          <section key={id} className="cyber-chamfer-sm border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-display text-lg font-bold uppercase tracking-wide text-foreground">
                {block.name}
              </h3>
              <span className={`flex items-center gap-2 font-mono text-xs ${status?.text ?? "text-muted-foreground"}`}>
                <span className={`inline-block h-2.5 w-2.5 rounded-full ${status?.dot ?? "bg-muted"}`} />
                {block.counts.pass} ✅ · {block.counts.warn} 🟡 · {block.counts.fail} ❌ ·{" "}
                {block.counts.na} ⚪
              </span>
            </div>
            <ul className="space-y-3">
              {block.criteria.map((c) => (
                <CriterionRow key={c.id} c={c} />
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

function ArgumentList({ title, items, accent }: { title: string; items: Argument[]; accent: string }) {
  return (
    <div className="cyber-chamfer-sm border border-border bg-card p-4">
      <p className={`mb-3 font-display text-sm font-bold uppercase tracking-widest ${accent}`}>
        {title}
      </p>
      {items.length === 0 ? (
        <p className="font-mono text-xs text-muted-foreground">Brak.</p>
      ) : (
        <ul className="space-y-2.5">
          {items.map((a) => (
            <li key={a.id}>
              <p className={`font-mono text-sm font-bold ${OUTCOME_TEXT[a.severity]}`}>
                {OUTCOME_ICON[a.severity]} {a.title}
              </p>
              <p className="font-mono text-xs text-muted-foreground">{a.detail}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CriterionRow({ c }: { c: Criterion }) {
  return (
    <li className="font-mono text-sm">
      <div className="flex flex-wrap items-baseline gap-x-3">
        <span aria-label={c.outcome}>{OUTCOME_ICON[c.outcome]}</span>
        <span className="text-foreground">{c.name}</span>
        <span className={`font-bold ${OUTCOME_TEXT[c.outcome]}`}>{c.display}</span>
        {c.knockout && (
          <span className="border border-destructive px-1.5 text-[11px] uppercase text-destructive">
            wyklucza
          </span>
        )}
      </div>
      <p className="ml-7 text-xs text-muted-foreground">{c.meaning}</p>
      <p className="ml-7 text-[11px] text-muted-foreground">
        <span className="text-accent-tertiary">próg:</span> {c.threshold}
      </p>
      <details className="ml-7 text-[11px] text-muted-foreground">
        <summary className="cursor-pointer select-none hover:text-accent">źródło</summary>
        <p className="mt-1">{c.source}</p>
      </details>
    </li>
  );
}
