import { useEffect, useMemo } from "react";
import { usePredictionHistory } from "@/hooks/usePredictionHistory";
import { useModelInfo } from "@/hooks/useModelInfo";
import { SummaryCards } from "@/components/accuracy/SummaryCards";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
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
  const historyQuery = usePredictionHistory();
  const modelQuery = useModelInfo();

  useEffect(() => {
    document.title = "Season Accuracy - NFL Predictor";
  }, []);

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
    return (
      <ErrorState
        heading="Connection Failed"
        body="Could not reach the prediction API. Make sure the server is running on localhost:8000."
        onRetry={() => {
          historyQuery.refetch();
          modelQuery.refetch();
        }}
      />
    );
  }

  if (!historyQuery.data || !modelQuery.data) return null;

  return (
    <div>
      <h1 className="text-xl font-semibold mb-8">Season Accuracy</h1>

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
                  className="hover:bg-zinc-800/50"
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
    </div>
  );
}
