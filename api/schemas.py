"""Pydantic response models for all API endpoints."""

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    """Single game prediction."""

    game_id: str
    season: int
    week: int
    game_date: str | None = None
    home_team: str
    away_team: str
    predicted_winner: str
    confidence: float
    confidence_tier: str
    actual_winner: str | None = None
    correct: bool | None = None


class SpreadPredictionResponse(BaseModel):
    """Single game spread prediction."""

    game_id: str
    season: int
    week: int
    game_date: str | None = None
    home_team: str
    away_team: str
    predicted_spread: float
    predicted_winner: str
    actual_spread: float | None = None
    actual_winner: str | None = None
    correct: bool | None = None


class HistorySummary(BaseModel):
    """Summary statistics for prediction history."""

    correct: int
    total: int
    accuracy: float | None = None


class PredictionHistoryResponse(BaseModel):
    """Response for GET /predictions/history."""

    predictions: list[PredictionResponse]
    summary: HistorySummary
    available_seasons: list[int] = []


class WeekPredictionsResponse(BaseModel):
    """Response for GET /predictions/week/{week} and /predictions/current."""

    season: int
    week: int
    status: str = "ok"  # "ok" or "offseason"
    predictions: list[PredictionResponse]


class SpreadWeekResponse(BaseModel):
    """Response for GET /api/predictions/spreads/week/{season}/{week}."""

    season: int
    week: int
    status: str = "ok"
    predictions: list[SpreadPredictionResponse]


class SpreadHistoryResponse(BaseModel):
    """Response for GET /api/predictions/spreads/history."""

    season: int
    predictions: list[SpreadPredictionResponse]


class SpreadModelInfo(BaseModel):
    """Spread model metadata nested in ModelInfoResponse."""

    mae: float
    rmse: float
    derived_win_accuracy: float
    training_date: str
    experiment_id: int


class ModelInfoResponse(BaseModel):
    """Response for GET /model/info."""

    experiment_id: int
    training_date: str
    val_accuracy_2023: float
    feature_count: int
    hypothesis: str
    baseline_always_home: float
    baseline_better_record: float
    spread_model: SpreadModelInfo | None = None


class ShapFeature(BaseModel):
    """Single SHAP feature importance entry."""

    feature: str
    importance: float


class ExperimentResponse(BaseModel):
    """Single experiment from experiments.jsonl."""

    experiment_id: int
    timestamp: str
    params: dict
    features: list[str]
    val_accuracy_2023: float
    val_accuracy_2022: float
    val_accuracy_2021: float
    baseline_always_home: float
    baseline_better_record: float
    log_loss: float
    brier_score: float
    shap_top5: list[ShapFeature]
    keep: bool
    hypothesis: str
    prev_best_acc: float
    model_path: str | None = None


class ReloadResponse(BaseModel):
    """Response for POST /model/reload."""

    status: str
    experiment_id: int
    val_accuracy_2023: float
    predictions_generated: int
    spread_experiment_id: int | None = None
    spread_mae: float | None = None
    spread_predictions_generated: int = 0


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: str
