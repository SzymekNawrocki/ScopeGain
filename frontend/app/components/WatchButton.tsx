"use client";

import { useState } from "react";
import { addToWatchlist } from "../lib/api";

// "Obserwuj" on the company card. 409 (already on the list) counts as success.
export function WatchButton({ ticker }: { ticker: string }) {
  const [state, setState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function add() {
    setState("busy");
    try {
      await addToWatchlist(ticker);
      setState("done");
      setMessage("Dodano do obserwowanych.");
    } catch (e) {
      const text = e instanceof Error ? e.message : "Błąd";
      if (text.includes("już jest")) {
        setState("done");
        setMessage(text);
      } else {
        setState("error");
        setMessage(text);
      }
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={add}
        disabled={state === "busy" || state === "done"}
        className="cyber-chamfer-sm border border-accent px-3 py-1.5 font-mono text-sm uppercase tracking-wider text-accent transition-all hover:bg-accent/10 disabled:opacity-50"
      >
        {state === "busy" ? "Dodaję…" : state === "done" ? "Obserwujesz" : "Obserwuj"}
      </button>
      {message && (
        <span className={`font-mono text-xs ${state === "error" ? "text-destructive" : "text-muted-foreground"}`}>
          {message}
        </span>
      )}
    </div>
  );
}
