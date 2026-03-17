import { Card, CardContent } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge";
import { ResultIndicator } from "@/components/shared/ResultIndicator";
import type { PredictionResponse } from "@/lib/types";

const tierBorderColors: Record<string, string> = {
  high: "border-blue-500",
  medium: "border-amber-500",
  low: "border-zinc-500",
};

interface PickCardProps {
  prediction: PredictionResponse;
}

export function PickCard({ prediction }: PickCardProps) {
  const {
    away_team,
    home_team,
    predicted_winner,
    confidence,
    confidence_tier,
    actual_winner,
    correct,
  } = prediction;

  const nonPredicted =
    predicted_winner === home_team ? away_team : home_team;

  return (
    <Card
      className={`relative border-l-[3px] ${tierBorderColors[confidence_tier]} hover:-translate-y-px transition-transform duration-150`}
    >
      <CardContent className="flex flex-col gap-2 p-4">
        {actual_winner != null && (
          <div className="absolute top-3 right-3">
            <ResultIndicator correct={correct} />
          </div>
        )}

        <p className="text-sm">
          {away_team} <span className="text-muted-foreground">@</span>{" "}
          {home_team}
        </p>

        <div>
          <p className="text-xl font-semibold">{predicted_winner}</p>
          <p className="text-sm text-muted-foreground">{nonPredicted}</p>
        </div>

        <p className="text-[28px] font-semibold leading-tight">
          {(confidence * 100).toFixed(1)}%
        </p>

        <ConfidenceBadge tier={confidence_tier} />
      </CardContent>
    </Card>
  );
}
