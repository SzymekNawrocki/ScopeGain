import { Nav } from "./components/Nav";
import { CompanyWorkspace } from "./components/CompanyWorkspace";

// Server Component shell. ?t=TICKER opens a company directly (links from the
// watchlist, or from other tools).
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ t?: string }>;
}) {
  const { t } = await searchParams;
  const ticker = (t ?? "AAPL").toUpperCase();
  return (
    <>
      <Nav />
      <main id="top" className="mx-auto max-w-7xl px-6 py-12">
        <header className="mb-12">
          <h1 className="font-display text-6xl font-black uppercase tracking-widest text-foreground sm:text-7xl">
            ScopeGain
          </h1>
          <p className="mt-4 max-w-2xl font-mono text-base leading-relaxed text-muted-foreground">
            Wpisz spółkę — ScopeGain powie, czy warto, na podstawie faktów i statystyk,
            a nie opinii. I zawsze pokaże, czego nie wie.
            <span className="cursor-blink" />
          </p>
        </header>
        <CompanyWorkspace key={ticker} initialTicker={ticker} />
      </main>
    </>
  );
}
