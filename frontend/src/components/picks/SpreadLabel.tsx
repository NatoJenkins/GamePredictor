interface SpreadLabelProps {
  predictedSpread?: number | null;
  actualSpread?: number | null;
}

function formatSpread(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}`;
}

function getSpreadErrorColor(error: number): string {
  if (error <= 3) return "text-green-400";
  if (error <= 7) return "text-amber-400";
  return "text-red-400";
}

export function SpreadLabel({ predictedSpread, actualSpread }: SpreadLabelProps) {
  if (predictedSpread == null) return null;

  const error =
    actualSpread != null ? Math.abs(predictedSpread - actualSpread) : null;

  // Negate for sportsbook convention: negative = favorite, positive = underdog
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-sm text-muted-foreground">
        {formatSpread(-predictedSpread)} spread
      </p>
      {actualSpread != null && error != null && (
        <p className="text-xs text-muted-foreground">
          Actual {formatSpread(-actualSpread)}{" "}
          <span className={`font-semibold ${getSpreadErrorColor(error)}`}>
            (off by {error.toFixed(1)})
          </span>
        </p>
      )}
    </div>
  );
}
