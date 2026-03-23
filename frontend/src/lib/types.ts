export interface PredictionResponse {
  game_id: string;
  season: number;
  week: number;
  game_date: string | null;
  home_team: string;
  away_team: string;
  predicted_winner: string;
  confidence: number;
  confidence_tier: "high" | "medium" | "low";
  actual_winner: string | null;
  correct: boolean | null;
}

export interface HistorySummary {
  correct: number;
  total: number;
  accuracy: number | null;
}

export interface PredictionHistoryResponse {
  predictions: PredictionResponse[];
  summary: HistorySummary;
}

export interface WeekPredictionsResponse {
  season: number;
  week: number;
  status: "ok" | "offseason";
  predictions: PredictionResponse[];
}

export interface ModelInfoResponse {
  experiment_id: number;
  training_date: string;
  val_accuracy_2023: number;
  feature_count: number;
  hypothesis: string;
  baseline_always_home: number;
  baseline_better_record: number;
  spread_model: SpreadModelInfo | null;
}

export interface ShapFeature {
  feature: string;
  importance: number;
}

export interface ExperimentResponse {
  experiment_id: number;
  timestamp: string;
  params: Record<string, unknown>;
  features: string[];
  val_accuracy_2023: number;
  val_accuracy_2022: number;
  val_accuracy_2021: number;
  baseline_always_home: number;
  baseline_better_record: number;
  log_loss: number;
  brier_score: number;
  shap_top5: ShapFeature[];
  keep: boolean;
  hypothesis: string;
  prev_best_acc: number;
  model_path: string | null;
}

export interface SpreadPredictionResponse {
  game_id: string;
  season: number;
  week: number;
  game_date: string | null;
  home_team: string;
  away_team: string;
  predicted_spread: number;
  predicted_winner: string;
  actual_spread: number | null;
  actual_winner: string | null;
  correct: boolean | null;
}

export interface SpreadWeekResponse {
  season: number;
  week: number;
  status: string;
  predictions: SpreadPredictionResponse[];
}

export interface SpreadModelInfo {
  mae: number;
  rmse: number;
  derived_win_accuracy: number;
  training_date: string;
  experiment_id: number;
}

export interface SpreadHistoryResponse {
  season: number;
  predictions: SpreadPredictionResponse[];
}
