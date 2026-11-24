import { Nav } from "../components/Nav";
import { GLOSSARY, GlossaryEntry } from "../lib/glossary";

// Server Component: static content, rendered at build time.
const GROUPS: GlossaryEntry["group"][] = [
  "Zaufanie",
  "Zdrowie",
  "Wycena",
  "Dywidenda",
  "Podatki",
  "Dane",
  "Poza ScopeGain",
];

export default function GlossaryPage() {
  const entries = Object.entries(GLOSSARY);
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-12">
        <h1 className="mb-3 font-display text-4xl font-black uppercase tracking-widest text-foreground">
          Słownik
        </h1>
        <p className="mb-10 max-w-2xl font-mono text-sm leading-relaxed text-muted-foreground">
          Skąd wzięła się każda liczba i co znaczy dla decyzji. Czego ScopeGain nie liczy, to
          odsyła do darmowych narzędzi. Wzory i progi:{" "}
          <span className="text-accent-tertiary">docs/METHODOLOGY.md</span> w repozytorium.
        </p>
        {GROUPS.map((group) => (
          <section key={group} className="mb-10">
            <h2 className="mb-4 border-b border-border pb-2 font-display text-xl font-bold uppercase tracking-wide text-accent">
              {group}
            </h2>
            <dl className="space-y-6">
              {entries
                .filter(([, e]) => e.group === group)
                .map(([id, e]) => (
                  <div key={id} id={id} className="scroll-mt-20">
                    <dt className="flex flex-wrap items-baseline gap-3">
                      <span className="font-mono text-base font-bold text-foreground">{e.term}</span>
                      <span
                        className={`border px-1.5 font-mono text-[11px] uppercase ${
                          e.computed === "tak"
                            ? "border-accent text-accent"
                            : "border-border text-muted-foreground"
                        }`}
                      >
                        {e.computed === "tak" ? "liczy ScopeGain" : "poza ScopeGain"}
                      </span>
                    </dt>
                    <dd className="mt-1 space-y-2 font-mono text-sm leading-relaxed">
                      <p className="text-foreground">{e.what}</p>
                      <p className="text-muted-foreground">{e.why}</p>
                      {e.links && e.links.length > 0 && (
                        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                          {e.links.map((l) => (
                            <li key={l.url}>
                              <a
                                href={l.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-accent-tertiary hover:underline"
                              >
                                {l.name} ↗
                              </a>
                              {l.note && <span className="text-muted-foreground"> — {l.note}</span>}
                            </li>
                          ))}
                        </ul>
                      )}
                    </dd>
                  </div>
                ))}
            </dl>
          </section>
        ))}
      </main>
    </>
  );
}
