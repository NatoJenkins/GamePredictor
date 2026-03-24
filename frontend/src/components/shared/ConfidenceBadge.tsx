import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const tierStyles: Record<string, string> = {
  high: "bg-tier-high-bg text-tier-high",
  medium: "bg-tier-medium-bg text-tier-medium",
  low: "bg-tier-low-bg text-tier-low",
};

interface ConfidenceBadgeProps {
  tier: "high" | "medium" | "low";
}

export function ConfidenceBadge({ tier }: ConfidenceBadgeProps) {
  const label = tier.charAt(0).toUpperCase() + tier.slice(1);

  return (
    <Badge
      variant="outline"
      className={cn("border-0 text-xs", tierStyles[tier])}
    >
      {label}
    </Badge>
  );
}
