"use client";

import { useEffect, useState } from "react";
import {
  DiscoverCompany,
  DiscoverNode,
  getDiscoverSectors,
  getEtfHoldings,
  getIndustryCompanies,
  getSectorIndustries,
  getThemes,
  Theme,
} from "../lib/api";
import { MarketScope } from "./MarketScope";
import { AddObservationForm } from "./AddObservationForm";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatusPanel } from "./ui/StatusPanel";
import { SectionLabel } from "./ui/SectionLabel";

const chip = (active: boolean) =>
  `cyber-chamfer-sm border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
    active
      ? "border-accent bg-accent/10 text-accent shadow-glow"
      : "border-border text-muted-foreground hover:border-accent hover:text-accent"
  }`;

// Tryb "Odkrywaj": wejscie dla kogos, kto NIE zna symbolu. Dwa sposoby:
//  - PRZEGLADAJ po kategorii (sektor -> branza -> spolki) oraz rozbij ETF,
//  - SZUKAJ po nazwie (dotychczasowy MarketScope: profil, ryzyko, wykres).
// Uczciwosc (ADR-0002): lista spolek branzy to ranking "top" Yahoo, NIE pelny
// spis - gubi liderow (Cameco przy uranie). Mowimy to wprost.
export function DiscoverWorkspace() {
  const [mode, setMode] = useState<"browse" | "search">("browse");

  return (
    <section>
      <SectionLabel>Znajdź spółkę</SectionLabel>
      <p className="mb-5 max-w-2xl font-mono text-sm leading-relaxed text-muted-foreground">
        Znajdź spółki bez znajomości symbolu:{" "}
        <span className="text-foreground">przeglądaj po kategorii</span> (branża lub skład
        ETF) albo <span className="text-foreground">szukaj po nazwie</span>. Kandydatów
        składasz w <span className="text-accent">Temat</span> — to Ty decydujesz, kto wchodzi.
      </p>

      <div className="mb-5 flex gap-1">
        <button onClick={() => setMode("browse")} className={chip(mode === "browse")}>
          przeglądaj
        </button>
        <button onClick={() => setMode("search")} className={chip(mode === "search")}>
          szukaj po nazwie
        </button>
      </div>

      {mode === "browse" ? <BrowsePanel /> : <MarketScope />}
    </section>
  );
}

// --- Przegladanie: sektor -> branza -> spolki + rozbicie ETF ---------------

function BrowsePanel() {
  const [sectors, setSectors] = useState<DiscoverNode[]>([]);
  const [sectorKey, setSectorKey] = useState<string | null>(null);
  const [industries, setIndustries] = useState<DiscoverNode[]>([]);
  const [industry, setIndustry] = useState<DiscoverNode | null>(null);
  const [companies, setCompanies] = useState<DiscoverCompany[]>([]);

  const [etfInput, setEtfInput] = useState("");
  const [etfLabel, setEtfLabel] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Kandydaci pod formularzem dodania: temat wybiera sie/tworzy w formularzu,
  // wiec potrzebujemy listy tematow (odswiezanej po dodaniu).
  const [themes, setThemes] = useState<Theme[]>([]);
  const [addFor, setAddFor] = useState<DiscoverCompany | null>(null);
  const [addOrigin, setAddOrigin] = useState("");
  const [added, setAdded] = useState<Record<string, boolean>>({});

  const reloadThemes = () => getThemes().then(setThemes).catch(() => {});
  useEffect(() => {
    getDiscoverSectors().then(setSectors).catch((e) => setError(e.message));
    reloadThemes();
  }, []);

  function pickSector(key: string) {
    setSectorKey(key);
    setIndustry(null);
    setCompanies([]);
    setAddFor(null);
    setLoading(true);
    setError(null);
    getSectorIndustries(key)
      .then(setIndustries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  function pickIndustry(node: DiscoverNode) {
    setIndustry(node);
    setAddFor(null);
    setEtfLabel(null);
    setLoading(true);
    setError(null);
    getIndustryCompanies(node.key)
      .then(setCompanies)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  function loadEtf(e: React.FormEvent) {
    e.preventDefault();
    const t = etfInput.trim().toUpperCase();
    if (!t) return;
    setIndustry(null);
    setEtfLabel(t);
    setAddFor(null);
    setLoading(true);
    setError(null);
    getEtfHoldings(t)
      .then(setCompanies)
      .catch((e2) => setError(e2.message))
      .finally(() => setLoading(false));
  }

  // Skad pochodzi lista, ktora widzisz teraz (do Pochodzenia kandydata).
  const currentOrigin = etfLabel
    ? `ETF: ${etfLabel}`
    : industry
    ? `branża: ${industry.name}`
    : "";

  function openAdd(c: DiscoverCompany) {
    setAddOrigin(currentOrigin);
    setAddFor(c);
  }

  return (
    <TerminalWindow title="Przeglądaj po kategorii">
      {/* Sektory */}
      <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
        Sektor
      </p>
      <div className="mb-4 flex flex-wrap gap-1">
        {sectors.map((s) => (
          <button key={s.key} onClick={() => pickSector(s.key)} className={chip(sectorKey === s.key)}>
            {s.name}
          </button>
        ))}
      </div>

      {/* Branze wybranego sektora */}
      {industries.length > 0 && (
        <>
          <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Branża
          </p>
          <div className="mb-4 flex flex-wrap gap-1">
            {industries.map((i) => (
              <button key={i.key} onClick={() => pickIndustry(i)} className={chip(industry?.key === i.key)}>
                {i.name}
              </button>
            ))}
          </div>
        </>
      )}

      {/* Rozbicie ETF - dla tematow, ktorych nie ma jako branza (kwanty -> QTUM) */}
      <form onSubmit={loadEtf} className="mb-4 flex items-center gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-muted-foreground">
          lub rozbij ETF:
        </span>
        <input
          value={etfInput}
          onChange={(e) => setEtfInput(e.target.value)}
          placeholder="QTUM, URA..."
          maxLength={15}
          className="cyber-chamfer-sm w-32 border border-border bg-[#0a0a0f] px-2 py-1 font-mono text-sm uppercase text-accent outline-none focus:border-accent"
        />
        <button type="submit" className={chip(false)}>
          pokaż skład
        </button>
      </form>

      {/* Zastrzezenie uczciwosci - lista branzy NIE jest pelnym spisem */}
      {industry && (
        <div className="cyber-chamfer-sm mb-4 border border-[#ffcc00]/50 bg-[#ffcc00]/5 px-4 py-3">
          <p className="font-mono text-xs leading-relaxed text-[#ffcc00]">
            ⚠ To ranking „top" Yahoo dla branży <span className="font-bold">{industry.name}</span>,
            NIE pełny spis — może pomijać liderów (np. Cameco przy uranie). Luki uzupełnij
            szukaniem po nazwie albo rozbiciem ETF.
          </p>
        </div>
      )}

      {error ? (
        <StatusPanel variant="error">
          <p className="text-foreground">{error}</p>
        </StatusPanel>
      ) : loading ? (
        <p className="font-mono text-sm text-accent">
          <span className="cursor-blink">&gt; pobieranie</span>
        </p>
      ) : companies.length > 0 ? (
        <ul className="space-y-1.5">
          {companies.map((c) => (
            <li key={c.ticker} className="cyber-chamfer-sm border border-border bg-[#12121a] px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="w-20 shrink-0 font-mono text-sm font-bold text-accent">
                  {c.ticker}
                </span>
                <span className="truncate font-mono text-sm text-foreground">{c.name}</span>
                <button
                  onClick={() => (addFor?.ticker === c.ticker ? setAddFor(null) : openAdd(c))}
                  className="ml-auto shrink-0 cyber-chamfer-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
                >
                  {added[c.ticker] ? "✓ w temacie" : "+ do tematu"}
                </button>
              </div>
              {addFor?.ticker === c.ticker && (
                <AddObservationForm
                  candidate={{ ticker: c.ticker, name: c.name, origin: addOrigin }}
                  themes={themes}
                  onDone={() => {
                    setAdded((a) => ({ ...a, [c.ticker]: true }));
                    setAddFor(null);
                    reloadThemes();
                  }}
                  onCancel={() => setAddFor(null)}
                />
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="font-mono text-sm text-muted-foreground">
          <span className="text-accent">$</span> wybierz sektor i branżę albo rozbij ETF,
          żeby zobaczyć kandydatów.
        </p>
      )}
    </TerminalWindow>
  );
}
