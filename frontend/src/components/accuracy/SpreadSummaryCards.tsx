import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InfoTooltip } from "@/components/shared/InfoTooltip";
import type {
  SpreadModelInfo,
  PredictionResponse,
  SpreadPredictionResponse,
} from "@/lib/types";

interface AgreementData {
  bothCorrect: number;
  bothWrong: number;
  onlyClassifier: number;
  onlySpread: number;
}

export function computeAgreement(
  classifierPredictions: PredictionResponse[],
  spreadPredictions: SpreadPredictionResponse[],
): AgreementData {
  const spreadByGame = new Map(
    spreadPredictions.map((sp) => [sp.game_id, sp]),
  );

  const result: AgreementData = {
    bothCorrect: 0,
    bothWrong: 0,
    onlyClassifier: 0,
    onlySpread: 0,
  };

  for (const cp of classifierPredictions) {
    if (cp.correct == null) continue;
    const sp = spreadByGame.get(cp.game_id);
    if (!sp || sp.correct == null) continue;

    if (cp.correct && sp.correct) result.bothCorrect++;
    else if (!cp.correct && !sp.correct) result.bothWrong++;
    else if (cp.correct && !sp.correct) result.onlyClassifier++;
    else result.onlySpread++;
  }

  return result;
}

function SpreadComparisonBadge({
  spreadAccuracy,
  classifierAccuracy,
}: {
  spreadAccuracy: number;
  classifierAccuracy: number | null;
}) {
  const diff = spreadAccuracy - (classifierAccuracy ?? 0);

  if (diff > 0) {
    return (
      <Badge className="bg-status-success/15 text-status-success border-0">
        Beating +{(diff * 100).toFixed(1)}%
      </Badge>
    );
  }

  return (
    <Badge className="bg-status-error/15 text-status-error border-0">
      Behind {(diff * 100).toFixed(1)}%
    </Badge>
  );
}

interface SpreadSummaryCardsProps {
  seasonStats: { mae: number; derived_win_accuracy: number } | null;
  lifetimeStats: Pick<SpreadModelInfo, "mae" | "derived_win_accuracy">;
  displaySeason: number | null;
  classifierAccuracy: number | null;
  agreement: AgreementData;
}

export function SpreadSummaryCards({
  seasonStats,
  lifetimeStats,
  displaySeason,
  classifierAccuracy,
  agreement,
}: SpreadSummaryCardsProps) {
  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Spread MAE Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            Spread MAE
            <InfoTooltip text="Mean Absolute Error — the average number of points the spread prediction was off by. Lower is better. For context, an NFL field goal is 3 points." />
          </p>
          {seasonStats && (
            <div className="mb-2">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">
                {displaySeason} Season
              </p>
              <p className="text-[28px] font-semibold leading-tight">
                {seasonStats.mae.toFixed(2)}
              </p>
            </div>
          )}
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">
              Lifetime
            </p>
            <p className={`${seasonStats ? "text-lg" : "text-[28px]"} font-semibold leading-tight`}>
              {lifetimeStats.mae.toFixed(2)}
            </p>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            avg. spread prediction error
          </p>
        </CardContent>
      </Card>

      {/* Spread Winner Accuracy Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            Spread Winner Accuracy
            <InfoTooltip text="How often the spread model correctly predicted which team would win, based on the predicted point margin. The badge compares this to the Pick-Em model above." />
          </p>
          {seasonStats && (
            <div className="mb-2">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">
                {displaySeason} Season
              </p>
              <p className="text-[28px] font-semibold leading-tight">
                {(seasonStats.derived_win_accuracy * 100).toFixed(1)}%
              </p>
              <div className="mt-1">
                <SpreadComparisonBadge
                  spreadAccuracy={seasonStats.derived_win_accuracy}
                  classifierAccuracy={classifierAccuracy}
                />
              </div>
            </div>
          )}
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">
              Lifetime
            </p>
            <p className={`${seasonStats ? "text-lg" : "text-[28px]"} font-semibold leading-tight`}>
              {(lifetimeStats.derived_win_accuracy * 100).toFixed(1)}%
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Agreement Breakdown Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            Pick-Em vs Spread
            <InfoTooltip text="Head-to-head comparison of the two models on the same games. 'Both correct' means both picked the winner right. 'Only Pick-Em' means the Pick-Em model was right but the spread model was wrong, and vice versa." />
          </p>
          <div className="flex flex-col gap-1 mt-1">
            <p className="text-sm">
              Both correct:{" "}
              <span className="font-semibold">{agreement.bothCorrect}</span>
            </p>
            <p className="text-sm">
              Both wrong:{" "}
              <span className="font-semibold">{agreement.bothWrong}</span>
            </p>
            <p className="text-sm">
              Only Pick-Em:{" "}
              <span className="font-semibold">{agreement.onlyClassifier}</span>
            </p>
            <p className="text-sm">
              Only spread:{" "}
              <span className="font-semibold">{agreement.onlySpread}</span>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
