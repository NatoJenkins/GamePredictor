import { PickCard } from "@/components/picks/PickCard";
import type { PredictionResponse, SpreadPredictionResponse } from "@/lib/types";

interface PicksGridProps {
  predictions: PredictionResponse[];
  spreadByGameId?: Record<string, SpreadPredictionResponse>;
}

export function PicksGrid({ predictions, spreadByGameId }: PicksGridProps) {
  return (
    <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      {predictions.map((prediction) => (
        <div key={prediction.game_id} className="min-w-[280px]">
          <PickCard
            prediction={prediction}
            spread={spreadByGameId?.[prediction.game_id]}
          />
        </div>
      ))}
    </div>
  );
}
