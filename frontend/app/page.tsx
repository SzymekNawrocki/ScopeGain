import { Nav } from "./components/Nav";
import { CompanyWorkspace } from "./components/CompanyWorkspace";

// Server Component: powloka strony (naglowek) nie ma stanu. Interaktywny jest
// tylko CompanyWorkspace (wyszukiwarka + profil spolki).
export default function Dashboard() {
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
        <CompanyWorkspace />
      </main>
    </>
  );
}
