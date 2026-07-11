// Ramka "okna terminala": pasek z trzema kropkami + tytul, potem tresc.
// Uzywana przez karty portfela, panel rynku i panel analizy - wczesniej ten
// sam markup byl skopiowany w kazdym z tych plikow osobno.
// Bez stanu/handlerow -> Server Component, dziala tez wewnatrz komponentow klienckich.
export function TerminalWindow({
  title,
  actions,
  className = "",
  children,
}: {
  title: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`cyber-chamfer border border-border bg-card ${className}`}>
      <header className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#ffcc00]" />
        <span className="h-2.5 w-2.5 rounded-full bg-accent" />
        <span className="ml-2 truncate font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          {title}
        </span>
        {actions && <span className="ml-auto">{actions}</span>}
      </header>
      <div className="p-5">{children}</div>
    </div>
  );
}
