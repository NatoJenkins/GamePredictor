import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { HistorySummary } from "@/lib/types";

interface SummaryCardsProps {
  summary: HistorySummary;
  baselineAlwaysHome: number;
  baselineBetterRecord: number;
}

function ComparisonBadge({
  modelAccuracy,
  baseline,
}: {
  modelAccuracy: number | null;
  baseline: number;
}) {
  const diff = (modelAccuracy ?? 0) - baseline;

  if (diff > 0) {
    return (
      <Badge className="bg-green-500/20 text-green-400 border-0">
        Beating +{(diff * 100).toFixed(1)}%
      </Badge>
    );
  }

  return (
    <Badge className="bg-red-500/20 text-red-400 border-0">
      Behind {(diff * 100).toFixed(1)}%
    </Badge>
  );
}

export function SummaryCards({
  summary,
  baselineAlwaysHome,
  baselineBetterRecord,
}: SummaryCardsProps) {
  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Model Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            Model
          </p>
          <p className="text-[28px] font-semibold leading-tight">
            {summary.correct}/{summary.total}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {summary.accuracy !== null
              ? (summary.accuracy * 100).toFixed(1) + "%"
              : "N/A"}
          </p>
        </CardContent>
      </Card>

      {/* vs Always-Home Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            vs Always-Home
          </p>
          <p className="text-[28px] font-semibold leading-tight">
            {(baselineAlwaysHome * 100).toFixed(1)}%
          </p>
          <div className="mt-2">
            <ComparisonBadge
              modelAccuracy={summary.accuracy}
              baseline={baselineAlwaysHome}
            />
          </div>
        </CardContent>
      </Card>

      {/* vs Better-Record Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            vs Better-Record
          </p>
          <p className="text-[28px] font-semibold leading-tight">
            {(baselineBetterRecord * 100).toFixed(1)}%
          </p>
          <div className="mt-2">
            <ComparisonBadge
              modelAccuracy={summary.accuracy}
              baseline={baselineBetterRecord}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
