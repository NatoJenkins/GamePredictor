import type { ExperimentResponse } from "@/lib/types";

interface ExperimentDetailProps {
  experiment: ExperimentResponse;
}

export function ExperimentDetail({ experiment }: ExperimentDetailProps) {
  const maxImportance =
    experiment.shap_top5.length > 0
      ? Math.max(...experiment.shap_top5.map((s) => s.importance))
      : 1;

  return (
    <div className="space-y-4 p-4">
      {/* Hypothesis */}
      <div>
        <h4 className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
          Hypothesis
        </h4>
        <p className="text-sm">{experiment.hypothesis}</p>
      </div>

      {/* Params */}
      <div>
        <h4 className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
          Parameters
        </h4>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1">
          {Object.entries(experiment.params).map(([key, value]) => (
            <div key={key} className="flex gap-2">
              <span className="text-xs text-muted-foreground">{key}:</span>
              <span className="font-mono text-xs">{String(value)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div>
        <h4 className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
          Features
        </h4>
        <p className="text-xs text-muted-foreground">
          {experiment.features.join(", ")}
        </p>
      </div>

      {/* SHAP Top 5 */}
      {experiment.shap_top5.length > 0 && (
        <div>
          <h4 className="text-xs text-muted-foreground uppercase tracking-wide mb-2">
            SHAP Top 5
          </h4>
          <div className="space-y-1">
            {experiment.shap_top5.map((item) => (
              <div key={item.feature} className="flex items-center gap-2">
                <span className="text-xs w-40 truncate">{item.feature}</span>
                <div className="flex-1 h-4 bg-secondary rounded overflow-hidden">
                  <div
                    className="h-4 bg-primary rounded"
                    style={{
                      width: `${(item.importance / maxImportance) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground w-16 text-right font-mono">
                  {item.importance.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
