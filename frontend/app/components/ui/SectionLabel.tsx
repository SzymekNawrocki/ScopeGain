// Wspolny naglowek sekcji w stylu terminala (znacznik $ + komenda).
// Czysto prezentacyjny - bez stanu/interakcji, wiec zyje jako Server Component
// i nie trafia do bundla JS wysylanego do przegladarki.
export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-4 font-mono text-sm uppercase tracking-[0.3em] text-accent-tertiary">
      {children}
    </p>
  );
}
