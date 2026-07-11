// Przyklejony pasek nawigacji. Linki to zwykle kotwice (#portfele...) -
// dzialaja bez JS, a plynne przewijanie zalatwia scroll-behavior w globals.css.
const LINKS: [string, string][] = [
  ["portfele", "Portfele"],
  ["rynek", "Rynek"],
  ["analiza", "Analiza"],
];

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
        <div className="ml-auto flex gap-1">
          {LINKS.map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className="cyber-chamfer-sm border border-transparent px-3 py-1.5 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
            >
              {label}
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
}
