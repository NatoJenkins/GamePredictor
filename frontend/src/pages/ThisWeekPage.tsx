import { useEffect } from "react";
import { Link } from "react-router";
import { useCurrentPredictions } from "@/hooks/useCurrentPredictions";
import { PicksGrid } from "@/components/picks/PicksGrid";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

export function ThisWeekPage() {
  const { data, isLoading, isError, refetch } = useCurrentPredictions();

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
    return (
      <ErrorState
        heading="Connection Failed"
        body="Could not reach the prediction API. Make sure the server is running on localhost:8000."
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
      <PicksGrid predictions={data.predictions} />
    </div>
  );
}
