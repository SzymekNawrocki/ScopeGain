import { Nav } from "../components/Nav";
import { WatchlistWorkspace } from "../components/WatchlistWorkspace";

export default function WatchlistPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-7xl px-6 py-12">
        <h1 className="mb-8 font-display text-4xl font-black uppercase tracking-widest text-foreground">
          Obserwowane
        </h1>
        <WatchlistWorkspace />
      </main>
    </>
  );
}
