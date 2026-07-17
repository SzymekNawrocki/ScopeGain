"use client";

import { useEffect, useRef, useState } from "react";
import { searchStocks, StockSearchHit } from "../lib/api";

// Wyszukiwarka spolek z podpowiedziami.
//
// Problem, ktory rozwiazuje: dotad pole przyjmowalo TYLKO symbol, wiec zeby
// obejrzec Cameco, trzeba bylo z gory wiedziec, ze to "CCJ". Teraz wpisujesz
// "cameco" i apka podsuwa liste.
//
// UWAGA na granice zrodla: szukanie po NAZWIE dziala dobrze, ale TEMATYCZNE
// nie - "uranium" nie zwroci Cameco, mimo ze jego branza to wprost "Uranium".
// Dlatego to jest wyszukiwarka nazw, nie tematow (ADR-0002).

const DEBOUNCE_MS = 300;
const MIN_ZNAKOW = 2;

export function SearchBox({
  value,
  onPick,
}: {
  value: string; // aktualnie ogladana spolka (do pokazania, gdy pole puste)
  onPick: (ticker: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<StockSearchHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1); // podswietlony wiersz (klawiatura)
  const [loading, setLoading] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  // Debounce: bez tego strzelalibysmy do Yahoo przy KAZDYM wcisnietym
  // klawiszu ("c", "ca", "cam"...) i limit zapytan padlby po chwili.
  useEffect(() => {
    const q = query.trim();
    if (q.length < MIN_ZNAKOW) {
      setHits([]);
      setLoading(false);
      return;
    }

    let aktualne = true; // straznik: ignoruj odpowiedz starego zapytania
    setLoading(true);
    const timer = setTimeout(() => {
      searchStocks(q)
        .then((r) => {
          if (aktualne) {
            setHits(r);
            setActive(-1);
          }
        })
        .catch(() => aktualne && setHits([]))
        .finally(() => aktualne && setLoading(false));
    }, DEBOUNCE_MS);

    return () => {
      aktualne = false;
      clearTimeout(timer); // user pisze dalej -> anuluj zaplanowany strzal
    };
  }, [query]);

  // Klik poza komponentem zamyka liste. Uzywamy mousedown (nie click), bo
  // blur+click na wierszu scigalyby sie i wybor by nie zdazyl.
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  function wybierz(ticker: string) {
    onPick(ticker.toUpperCase());
    setQuery("");
    setOpen(false);
    setActive(-1);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); // nie przesuwaj kursora w polu
      if (!hits.length) return;
      setOpen(true);
      setActive((i) => {
        const next = e.key === "ArrowDown" ? i + 1 : i - 1;
        return (next + hits.length) % hits.length; // zawijanie listy
      });
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      // Podswietlony wiersz wygrywa; inaczej bierzemy surowy tekst jako
      // symbol - zeby ktos, kto zna ticker, nadal mogl go wpisac i wcisnac
      // Enter (dotychczasowe zachowanie tego pola).
      if (open && active >= 0 && hits[active]) wybierz(hits[active].ticker);
      else if (query.trim()) wybierz(query.trim());
    }
  }

  const pokazListe = open && query.trim().length >= MIN_ZNAKOW;

  return (
    <div ref={boxRef} className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-accent">
        &gt;
      </span>
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        spellCheck={false}
        // Bez uppercase: user szukajacy "cameco" widzialby "CAMECO".
        placeholder={value ? `${value} — szukaj innej...` : "cameco, uran, AAPL..."}
        aria-label="Szukaj spolki po nazwie lub symbolu"
        role="combobox"
        aria-expanded={pokazListe}
        aria-controls="wyniki-szukania"
        aria-autocomplete="list"
        aria-activedescendant={active >= 0 ? `wynik-${active}` : undefined}
        className="cyber-chamfer-sm w-72 border border-border bg-[#12121a] py-2 pl-8 pr-3 font-mono text-sm text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent focus:shadow-glow"
      />

      {pokazListe && (
        <ul
          id="wyniki-szukania"
          role="listbox"
          className="absolute left-0 top-11 z-40 max-h-80 w-96 overflow-y-auto border border-accent/40 bg-[#0a0a0f] shadow-glow"
        >
          {loading && hits.length === 0 && (
            <li className="px-3 py-2 font-mono text-xs text-muted-foreground">
              <span className="cursor-blink">&gt; szukam</span>
            </li>
          )}

          {!loading && hits.length === 0 && (
            <li className="px-3 py-2 font-mono text-xs text-muted-foreground">
              nic nie znaleziono — sprobuj nazwy firmy albo symbolu
            </li>
          )}

          {hits.map((h, i) => (
            <li
              key={`${h.ticker}-${h.exchange ?? i}`}
              id={`wynik-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => e.preventDefault()} // nie gub focusa przed klikiem
              onClick={() => wybierz(h.ticker)}
              className={`cursor-pointer border-b border-border/50 px-3 py-2 font-mono text-xs transition-colors last:border-0 ${
                i === active ? "bg-accent/10" : ""
              }`}
            >
              <div className="flex items-baseline gap-2">
                <span className="font-bold text-accent">{h.ticker}</span>
                <span className="truncate text-foreground">{h.name}</span>
                {h.quote_type === "ETF" && (
                  <span className="shrink-0 border border-accent-tertiary/50 px-1 text-[10px] uppercase text-accent-tertiary">
                    etf
                  </span>
                )}
              </div>
              <div className="mt-0.5 flex gap-2 text-[11px] text-muted-foreground">
                {/* Gielda rozroznia cross-listing (CCJ/NYSE vs CCO.TO/Toronto) -
                    bez niej to dwa identyczne wiersze "Cameco Corporation". */}
                {h.exchange && <span>{h.exchange}</span>}
                {h.industry && (
                  <>
                    <span className="text-border">|</span>
                    <span>{h.industry}</span>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
