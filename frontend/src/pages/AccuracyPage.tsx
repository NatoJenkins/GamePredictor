import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router";
import { usePredictionHistory } from "@/hooks/usePredictionHistory";
import { useModelInfo } from "@/hooks/useModelInfo";
import { useSpreadHistory } from "@/hooks/useSpreadHistory";
import { SummaryCards } from "@/components/accuracy/SummaryCards";
import {
  SpreadSummaryCards,
  computeAgreement,
} from "@/components/accuracy/SpreadSummaryCards";
import { ErrorState } from "@/components/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface WeekBreakdown {
  week: number;
  correct: number;
  total: number;
  accuracy: number;
}

export function AccuracyPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const season = searchParams.get("season")
    ? Number(searchParams.get("season"))
    : undefined;

  const historyQuery = usePredictionHistory(season);
  const modelQuery = useModelInfo();
  const hasSpreadModel = modelQuery.data?.spread_model != null;
  const spreadHistoryQuery = useSpreadHistory(season, hasSpreadModel);

  useEffect(() => {
    document.title = "Season Accuracy - NFL Predictor";
  }, []);

  const availableSeasons = useMemo(() => {
    if (!historyQuery.data) return [];
    return historyQuery.data.available_seasons;
  }, [historyQuery.data]);

  const displaySeason = useMemo(() => {
    if (season) return season;
    if (availableSeasons.length > 0) return availableSeasons[0];
    return null;
  }, [season, availableSeasons]);

  const handleSeasonChange = (value: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (!value || value === "latest") {
      params.delete("season");
    } else {
      params.set("season", value);
    }
    setSearchParams(params);
  };

  const weekBreakdown = useMemo<WeekBreakdown[]>(() => {
    if (!historyQuery.data) return [];

    const byWeek = new Map<number, { correct: number; total: number }>();

    for (const p of historyQuery.data.predictions) {
      if (p.correct === null) continue;
      const entry = byWeek.get(p.week) ?? { correct: 0, total: 0 };
      entry.total++;
      if (p.correct) entry.correct++;
      byWeek.set(p.week, entry);
    }

    return Array.from(byWeek.entries())
      .sort(([a], [b]) => a - b)
      .map(([week, stats]) => ({
        week,
        correct: stats.correct,
        total: stats.total,
        accuracy: stats.total > 0 ? stats.correct / stats.total : 0,
      }));
  }, [historyQuery.data]);

  const agreement = useMemo(() => {
    if (!historyQuery.data?.predictions || !spreadHistoryQuery.data?.predictions)
      return null;
    return computeAgreement(
      historyQuery.data.predictions,
      spreadHistoryQuery.data.predictions,
    );
  }, [historyQuery.data, spreadHistoryQuery.data]);

  // Compute season-filtered spread stats instead of using lifetime model info
  const seasonSpreadStats = useMemo(() => {
    if (!spreadHistoryQuery.data?.predictions) return null;
    const completed = spreadHistoryQuery.data.predictions.filter(
      (p) => p.actual_spread != null && p.correct != null,
    );
    if (completed.length === 0) return null;

    const totalError = completed.reduce(
      (sum, p) => sum + Math.abs(p.predicted_spread - p.actual_spread!),
      0,
    );
    const correctCount = completed.filter((p) => p.correct).length;

    return {
      mae: totalError / completed.length,
      derived_win_accuracy: correctCount / completed.length,
    };
  }, [spreadHistoryQuery.data]);

  if (historyQuery.isLoading || modelQuery.isLoading) {
    return (
      <div>
        <Skeleton className="h-7 w-48 mb-8" />
        <div className="flex flex-col md:flex-row gap-6 mb-8">
          <Skeleton className="h-32 flex-1 rounded-lg" />
          <Skeleton className="h-32 flex-1 rounded-lg" />
          <Skeleton className="h-32 flex-1 rounded-lg" />
        </div>
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (historyQuery.isError || modelQuery.isError) {
    const err = modelQuery.error ?? historyQuery.error;
    const notReady = err instanceof ApiError && err.isNotReady;
    return (
      <ErrorState
        heading={notReady ? "No Model Trained Yet" : "Connection Failed"}
        body={
          notReady
            ? "Train a model and call POST /api/model/reload to see accuracy stats here."
            : "Could not reach the prediction API. Make sure the server is running."
        }
        onRetry={() => {
          historyQuery.refetch();
          modelQuery.refetch();
        }}
      />
    );
  }

  if (!historyQuery.data || !modelQuery.data) return null;

  // Empty state: API succeeded but no predictions exist yet
  if (historyQuery.data.predictions.length === 0) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-8">Season Accuracy</h1>
        <ErrorState
          heading="No Predictions Yet"
          body="No predictions have been generated yet. Run predict_week.py to generate predictions, then check back here to see accuracy stats."
        />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-8">
        <h1 className="text-xl font-semibold">
          {displaySeason} Season Accuracy
        </h1>
        {availableSeasons.length > 1 && (
          <Select
            value={season !== undefined ? String(season) : "latest"}
            onValueChange={handleSeasonChange}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="latest">Latest</SelectItem>
              {availableSeasons.map((s) => (
                <SelectItem key={s} value={String(s)}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      <SummaryCards
        summary={historyQuery.data.summary}
        baselineAlwaysHome={modelQuery.data.baseline_always_home}
        baselineBetterRecord={modelQuery.data.baseline_better_record}
      />

      {weekBreakdown.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            Week-by-Week Breakdown
          </h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">Week</TableHead>
                <TableHead className="w-[100px]">Record</TableHead>
                <TableHead className="w-[100px]">Accuracy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {weekBreakdown.map((week) => (
                <TableRow
                  key={week.week}
                  className="hover:bg-secondary/50"
                >
                  <TableCell>{week.week}</TableCell>
                  <TableCell>
                    {week.correct}/{week.total}
                  </TableCell>
                  <TableCell>
                    {(week.accuracy * 100).toFixed(1)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Spread Model Section -- hidden when spread model not loaded */}
      {modelQuery.data.spread_model && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            Spread Model
          </h2>
          {spreadHistoryQuery.isLoading ? (
            <div className="flex flex-col md:flex-row gap-6">
              <Skeleton className="h-32 flex-1 rounded-lg" />
              <Skeleton className="h-32 flex-1 rounded-lg" />
              <Skeleton className="h-32 flex-1 rounded-lg" />
            </div>
          ) : (
            <SpreadSummaryCards
              seasonStats={seasonSpreadStats}
              lifetimeStats={modelQuery.data.spread_model}
              displaySeason={displaySeason}
              classifierAccuracy={historyQuery.data.summary.accuracy}
              agreement={
                agreement ?? {
                  bothCorrect: 0,
                  bothWrong: 0,
                  onlyClassifier: 0,
                  onlySpread: 0,
                }
              }
            />
          )}
        </div>
      )}
    </div>
  );
}
