import { useEffect, useMemo } from "react";
import { Link } from "react-router";
import { useCurrentPredictions } from "@/hooks/useCurrentPredictions";
import { useSpreadPredictions } from "@/hooks/useSpreadPredictions";
import { PicksGrid } from "@/components/picks/PicksGrid";
import { ErrorState } from "@/components/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import type { SpreadPredictionResponse } from "@/lib/types";

export function ThisWeekPage() {
  const { data, isLoading, isError, error, refetch } = useCurrentPredictions();

  const spreadQuery = useSpreadPredictions(data?.season, data?.week);

  const spreadByGameId = useMemo(() => {
    if (!spreadQuery.data?.predictions) return undefined;
    const map: Record<string, SpreadPredictionResponse> = {};
    for (const sp of spreadQuery.data.predictions) {
      map[sp.game_id] = sp;
    }
    return map;
  }, [spreadQuery.data]);

  useEffect(() => {
    if (data) {
      document.title = `Week ${data.week} Picks - NFL Predictor`;
    }
  }, [data]);

  if (isLoading) {
    return (
      <div>
        <Skeleton className="h-7 w-48 mb-8" />
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-48 rounded-lg min-w-[280px]" />
          <Skeleton className="h-48 rounded-lg min-w-[280px]" />
          <Skeleton className="h-48 rounded-lg min-w-[280px]" />
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
            ? "Train a model and call POST /api/model/reload to generate predictions."
            : "Could not reach the prediction API. Make sure the server is running."
        }
        onRetry={() => refetch()}
      />
    );
  }

  if (data?.status === "offseason") {
    return (
      <div>
        <ErrorState
          heading="Offseason"
          body="No upcoming games to predict. Check back when the regular season starts."
        />
        <div className="mt-4 text-center">
          <Link
            to="/history"
            className="text-sm text-blue-400 hover:underline"
          >
            View Prediction History
          </Link>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-1">Week {data.week} Picks</h1>
      <p className="text-sm text-muted-foreground mb-8">
        {data.season} Season
      </p>
      <PicksGrid predictions={data.predictions} spreadByGameId={spreadByGameId} />
    </div>
  );
}
