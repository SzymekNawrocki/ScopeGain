import Link from "next/link";

const LINKS: [string, string][] = [
  ["/", "Spółka"],
  ["/obserwowane", "Obserwowane"],
  ["/slownik", "Słownik"],
];

// Sticky navigation. Plain links: each screen is its own route.
export function Nav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-6 py-3">
        <Link
          href="/"
          className="font-display text-lg font-black uppercase tracking-widest text-foreground"
        >
          Scope<span className="text-accent">Gain</span>
        </Link>
        <div className="ml-auto flex gap-1">
          {LINKS.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className="cyber-chamfer-sm border border-transparent px-3 py-1.5 font-mono text-sm uppercase tracking-wider text-muted-foreground transition-all hover:border-accent hover:text-accent"
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
