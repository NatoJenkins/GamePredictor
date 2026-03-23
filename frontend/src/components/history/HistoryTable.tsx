import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge";
import { ResultIndicator } from "@/components/shared/ResultIndicator";
import type { PredictionResponse, SpreadPredictionResponse } from "@/lib/types";

interface HistoryTableProps {
  predictions: PredictionResponse[];
  spreadByGameId?: Record<string, SpreadPredictionResponse>;
}

function formatSpread(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}`;
}

function formatDate(gameDate: string | null): string {
  if (!gameDate) return "-";
  const date = new Date(gameDate);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function HistoryTable({ predictions, spreadByGameId }: HistoryTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[60px]">Week</TableHead>
            <TableHead className="w-[100px]">Date</TableHead>
            <TableHead>Matchup</TableHead>
            <TableHead className="w-[100px]">Pick</TableHead>
            <TableHead className="w-[100px]">Confidence</TableHead>
            {spreadByGameId && <TableHead className="w-[80px]">Spread</TableHead>}
            <TableHead className="w-20">Result</TableHead>
            <TableHead className="w-[100px]">Actual</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {predictions.map((p) => (
            <TableRow key={p.game_id} className="hover:bg-zinc-800/50">
              <TableCell>{p.week}</TableCell>
              <TableCell>{formatDate(p.game_date)}</TableCell>
              <TableCell className="text-sm">
                {p.away_team} <span className="text-muted-foreground">@</span>{" "}
                {p.home_team}
              </TableCell>
              <TableCell className="font-semibold">
                {p.predicted_winner}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span>{(p.confidence * 100).toFixed(1)}%</span>
                  <ConfidenceBadge tier={p.confidence_tier} />
                </div>
              </TableCell>
              {spreadByGameId && (
                <TableCell className="text-sm text-muted-foreground">
                  {spreadByGameId[p.game_id]
                    ? formatSpread(spreadByGameId[p.game_id].predicted_spread)
                    : "-"}
                </TableCell>
              )}
              <TableCell>
                <ResultIndicator correct={p.correct} />
              </TableCell>
              <TableCell>
                {p.actual_winner ? (
                  p.actual_winner
                ) : (
                  <span className="text-muted-foreground text-sm">
                    Pending
                  </span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
