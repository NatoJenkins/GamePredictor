import { useState } from "react";

export function HistoryLegend() {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
      >
        <span className="text-base leading-none">&#9432;</span>
        {open ? "Hide legend" : "How to read this table"}
      </button>

      {open && (
        <div className="mt-3 p-4 rounded-lg border border-zinc-800 bg-zinc-900/50 text-sm text-muted-foreground space-y-3">
          <div>
            <span className="font-semibold text-foreground">Pick</span> —
            The model's predicted winner for the game.
          </div>
          <div>
            <span className="font-semibold text-foreground">Confidence</span> —
            How confident the model is in its pick.{" "}
            <span className="text-amber-400">Medium</span> and{" "}
            <span className="text-green-400">High</span> indicate stronger conviction.
          </div>
          <div>
            <span className="font-semibold text-foreground">Spread</span> —
            The model's predicted point spread for the home team, using standard
            sportsbook convention.{" "}
            <span className="text-foreground">MIA -2.3</span> means Miami is
            favored by 2.3 points (giving 2.3).{" "}
            <span className="text-foreground">MIA +2.0</span> means Miami is a
            2-point underdog (getting 2). After the game, the actual result is
            shown below (e.g., "BUF by 9").
          </div>
          <div className="pl-4 space-y-1">
            <div>
              The color shows how accurate the spread prediction was:
            </div>
            <div>
              <span className="text-green-400 font-semibold">Green</span> — Within
              3 points of the actual margin (field goal or less).
            </div>
            <div>
              <span className="text-amber-400 font-semibold">Amber</span> — Off by
              3 to 7 points.
            </div>
            <div>
              <span className="text-red-400 font-semibold">Red</span> — Off by more
              than 7 points (touchdown+).
            </div>
          </div>
          <div>
            <span className="font-semibold text-foreground">Result</span> —
            Whether the model's <em>winner pick</em> was correct (
            <span className="text-green-400">&#10004;</span>) or wrong (
            <span className="text-red-400">&#10008;</span>).
          </div>
          <div>
            <span className="font-semibold text-foreground">Actual</span> — The
            team that actually won the game.
          </div>
        </div>
      )}
    </div>
  );
}
