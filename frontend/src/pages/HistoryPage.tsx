import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router";
import { usePredictionHistory } from "@/hooks/usePredictionHistory";
import { useSpreadHistory } from "@/hooks/useSpreadHistory";
import { HistoryFilters } from "@/components/history/HistoryFilters";
import { HistoryLegend } from "@/components/history/HistoryLegend";
import { HistoryTable } from "@/components/history/HistoryTable";
import { ErrorState } from "@/components/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import type { SpreadPredictionResponse } from "@/lib/types";

export function HistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const season = searchParams.get("season")
    ? Number(searchParams.get("season"))
    : undefined;
  const team = searchParams.get("team") ?? undefined;

  const { data, isLoading, isError, error, refetch } = usePredictionHistory(
    season,
    team
  );

  const spreadHistoryQuery = useSpreadHistory(season);

  const spreadByGameId = useMemo(() => {
    if (!spreadHistoryQuery.data?.predictions) return undefined;
    const map: Record<string, SpreadPredictionResponse> = {};
    for (const sp of spreadHistoryQuery.data.predictions) {
      map[sp.game_id] = sp;
    }
    return map;
  }, [spreadHistoryQuery.data]);

  useEffect(() => {
    document.title = "History - NFL Predictor";
  }, []);

  const availableSeasons = useMemo(() => {
    if (!data) return [];
    return data.available_seasons;
  }, [data]);

  const availableTeams = useMemo(() => {
    if (!data) return [];
    return [
      ...new Set(
        data.predictions.flatMap((p) => [p.home_team, p.away_team])
      ),
    ].sort();
  }, [data]);

  const handleSeasonChange = (newSeason: number | undefined) => {
    const params = new URLSearchParams(searchParams);
    if (newSeason !== undefined) {
      params.set("season", String(newSeason));
    } else {
      params.delete("season");
    }
    setSearchParams(params);
  };

  const handleTeamChange = (newTeam: string | undefined) => {
    const params = new URLSearchParams(searchParams);
    if (newTeam !== undefined) {
      params.set("team", newTeam);
    } else {
      params.delete("team");
    }
    setSearchParams(params);
  };

  if (isLoading) {
    return (
      <div>
        <Skeleton className="h-7 w-48 mb-4" />
        <div className="flex gap-4 mb-6">
          <Skeleton className="h-10 w-36" />
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    const notReady = error instanceof ApiError && error.isNotReady;
    return (
      <ErrorState
        heading={notReady ? "No Model Trained Yet" : "Connection Failed"}
        body={
          notReady
            ? "Train a model and call POST /api/model/reload to see prediction history."
            : "Could not reach the prediction API. Make sure the server is running."
        }
        onRetry={() => refetch()}
      />
    );
  }

  if (data && data.predictions.length === 0) {
    return (
      <div>
        <h1 className="text-xl font-semibold mb-8">Prediction History</h1>
        <ErrorState
          heading="No Predictions Yet"
          body="Predictions will appear here after the model processes game data."
        />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-1">Prediction History</h1>
      <div className="flex gap-4 mb-6 text-sm text-muted-foreground">
        <span>
          {data.summary.correct}/{data.summary.total} correct
        </span>
        {data.summary.accuracy !== null && (
          <span>({(data.summary.accuracy * 100).toFixed(1)}%)</span>
        )}
      </div>

      <HistoryFilters
        season={season}
        team={team}
        onSeasonChange={handleSeasonChange}
        onTeamChange={handleTeamChange}
        availableSeasons={availableSeasons}
        availableTeams={availableTeams}
      />

      <HistoryLegend />

      <HistoryTable predictions={data.predictions} spreadByGameId={spreadByGameId} />
    </div>
  );
}
