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

function getSpreadErrorColor(error: number): string {
  if (error <= 3) return "text-status-success";
  if (error <= 7) return "text-status-warning";
  return "text-status-error";
}

function SpreadCell({ spread }: { spread: SpreadPredictionResponse }) {
  // Negate for sportsbook convention: negative = favorite, positive = underdog
  const predicted = `${spread.home_team} ${formatSpread(-spread.predicted_spread)}`;

  if (spread.actual_spread == null || spread.actual_winner == null) {
    return <span>{predicted}</span>;
  }

  const margin = Math.abs(spread.actual_spread);
  const error = Math.abs(spread.predicted_spread - spread.actual_spread);
  const actualText =
    margin === 0 ? "Tie" : `${spread.actual_winner} by ${Math.round(margin)}`;

  return (
    <div className="flex flex-col gap-0.5">
      <span>{predicted}</span>
      <span className={`text-xs ${getSpreadErrorColor(error)}`}>
        → {actualText}
      </span>
    </div>
  );
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
            {spreadByGameId && <TableHead className="w-[140px]">Spread</TableHead>}
            <TableHead className="w-20">Result</TableHead>
            <TableHead className="w-[100px]">Actual</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {predictions.map((p) => (
            <TableRow key={p.game_id} className="hover:bg-secondary/50">
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
                  {spreadByGameId[p.game_id] ? (
                    <SpreadCell spread={spreadByGameId[p.game_id]} />
                  ) : (
                    "-"
                  )}
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
