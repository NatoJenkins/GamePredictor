import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InfoTooltip } from "@/components/shared/InfoTooltip";
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
            Pick-Em Model
            <InfoTooltip text="The Pick-Em model's win/loss prediction record for this season. It picks a straight-up winner for every game based on team stats, rest days, and recent performance." />
          </p>
          <p className="text-[28px] font-semibold leading-tight">
            {summary.accuracy !== null
              ? (summary.accuracy * 100).toFixed(1) + "%"
              : "N/A"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {summary.correct}/{summary.total}
          </p>
        </CardContent>
      </Card>

      {/* vs Always-Home Card */}
      <Card className="flex-1">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground uppercase tracking-wide mb-2">
            vs Always-Home
            <InfoTooltip text="Baseline that always picks the home team to win. Home-field advantage is real, so this is the simplest strategy to beat. The badge shows how much the model beats or trails this baseline." />
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
            vs Team w/ Better Record
            <InfoTooltip text="Baseline that always picks the team with the better record. This is a tougher benchmark — it uses the wisdom of the season so far. The badge shows how the model compares." />
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
