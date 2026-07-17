"use client";

import { useEffect, useState } from "react";
import { useWorkspace, WorkspaceTab } from "./WorkspaceProvider";
import { DiscoverWorkspace } from "./DiscoverWorkspace";
import { ThemesWorkspace } from "./ThemesWorkspace";
import { PortfolioWorkspace } from "./PortfolioWorkspace";

// Przelacza miedzy trybami. Kluczowa decyzja: tryb raz odwiedzony ZOSTAJE
// zamontowany i tylko chowa sie przez `hidden` - dzieki temu stan (ogladana
// spolka, otwarty temat, wybor portfela) nie kasuje sie przy przechodzeniu
// tam i z powrotem. Tryb nietkniety NIE montuje sie w tle, zeby nie strzelac
// po API zanim user tam wejdzie.
export function WorkspaceBody() {
  const { tab } = useWorkspace();
  const [visited, setVisited] = useState<Set<WorkspaceTab>>(() => new Set([tab]));

  useEffect(() => {
    setVisited((prev) => (prev.has(tab) ? prev : new Set(prev).add(tab)));
  }, [tab]);

  return (
    <>
      {visited.has("odkrywaj") && (
        <div className={tab === "odkrywaj" ? "" : "hidden"}>
          <DiscoverWorkspace />
        </div>
      )}
      {visited.has("tematy") && (
        <div className={tab === "tematy" ? "" : "hidden"}>
          <ThemesWorkspace />
        </div>
      )}
      {visited.has("portfel") && (
        <div className={tab === "portfel" ? "" : "hidden"}>
          <PortfolioWorkspace />
        </div>
      )}
    </>
  );
}
