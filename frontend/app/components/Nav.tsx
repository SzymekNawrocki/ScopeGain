// Przyklejony pasek nawigacji. Po plastrze 0 jest jeden ekran (Spolka);
// "Obserwowane" dojdzie w plastrze 6.
export function Nav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-3">
        <a
          href="#top"
          className="font-display text-lg font-black uppercase tracking-widest text-foreground"
        >
          Scope<span className="text-accent">Gain</span>
        </a>
      </div>
    </nav>
  );
}
