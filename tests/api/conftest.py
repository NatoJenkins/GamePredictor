"""Shared test fixtures for API tests."""

import json
import os

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


# Sample experiment entries matching real experiments.jsonl schema
SAMPLE_EXPERIMENTS = [
    {
        "experiment_id": 1,
        "timestamp": "2026-03-17T01:16:43.500695+00:00",
        "params": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.3},
        "features": [
            "home_rest",
            "away_rest",
            "div_game",
            "home_rolling_point_diff",
        ],
        "val_accuracy_2023": 0.6016,
        "val_accuracy_2022": 1.0,
        "val_accuracy_2021": 0.9882,
        "baseline_always_home": 0.5551,
        "baseline_better_record": 0.5820,
        "log_loss": 0.7521,
        "brier_score": 0.2605,
        "shap_top5": [
            {"feature": "home_rolling_point_diff", "importance": 0.3856}
        ],
        "keep": True,
        "hypothesis": "Baseline experiment",
        "prev_best_acc": 0.0,
        "model_path": "models/artifacts/model_exp001.json",
    },
    {
        "experiment_id": 2,
        "timestamp": "2026-03-17T01:17:49.466408+00:00",
        "params": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.3},
        "features": ["home_rest", "away_rest"],
        "val_accuracy_2023": 0.5352,
        "val_accuracy_2022": 0.9764,
        "val_accuracy_2021": 0.9804,
        "baseline_always_home": 0.5551,
        "baseline_better_record": 0.5820,
        "log_loss": 0.7890,
        "brier_score": 0.2811,
        "shap_top5": [{"feature": "home_rest", "importance": 0.4365}],
        "keep": False,
        "hypothesis": "Ablation test",
        "prev_best_acc": 0.6016,
        "model_path": None,
    },
]

# Sample prediction rows (as would come from DB)
SAMPLE_PREDICTIONS = pd.DataFrame(
    [
        {
            "game_id": "2024_01_KC_BAL",
            "season": 2024,
            "week": 1,
            "game_date": "2024-09-05",
            "home_team": "BAL",
            "away_team": "KC",
            "predicted_winner": "BAL",
            "confidence": 0.62,
            "confidence_tier": "medium",
            "actual_winner": "KC",
            "correct": False,
        },
        {
            "game_id": "2024_01_GB_PHI",
            "season": 2024,
            "week": 1,
            "game_date": "2024-09-06",
            "home_team": "PHI",
            "away_team": "GB",
            "predicted_winner": "PHI",
            "confidence": 0.68,
            "confidence_tier": "high",
            "actual_winner": "PHI",
            "correct": True,
        },
    ]
)


SAMPLE_SPREAD_EXPERIMENT = {
    "experiment_id": 1,
    "timestamp": "2026-03-23T04:54:37.744622+00:00",
    "model_type": "spread_regression",
    "params": {"n_estimators": 300},
    "features": ["home_rest", "away_rest", "div_game"],
    "mae_2023": 10.6826,
    "rmse_2023": 13.8711,
    "derived_win_accuracy_2023": 0.6016,
    "keep": True,
    "hypothesis": "Baseline spread",
    "prev_best_mae": None,
    "model_path": "models/artifacts/best_spread_model.json",
}

SAMPLE_SPREAD_PREDICTIONS = pd.DataFrame(
    [
        {
            "game_id": "2024_01_KC_BAL",
            "season": 2024,
            "week": 1,
            "game_date": "2024-09-05",
            "home_team": "BAL",
            "away_team": "KC",
            "predicted_spread": 3.5,
            "predicted_winner": "BAL",
            "actual_spread": None,
            "actual_winner": None,
            "correct": None,
        },
        {
            "game_id": "2024_01_GB_PHI",
            "season": 2024,
            "week": 1,
            "game_date": "2024-09-06",
            "home_team": "PHI",
            "away_team": "GB",
            "predicted_spread": -2.1,
            "predicted_winner": "GB",
            "actual_spread": None,
            "actual_winner": None,
            "correct": None,
        },
    ]
)


@pytest.fixture
def experiments_file(tmp_path):
    """Create a temporary experiments.jsonl file."""
    path = tmp_path / "experiments.jsonl"
    with open(path, "w") as f:
        for exp in SAMPLE_EXPERIMENTS:
            f.write(json.dumps(exp) + "\n")
    return str(path)


def _mock_read_sql(query, engine, params=None):
    """Mock pd.read_sql to return sample data without requiring PostgreSQL."""
    query_lower = query.lower().strip()
    if "max(season)" in query_lower:
        return pd.DataFrame({"max_season": [2024]})
    elif "from spread_predictions" in query_lower:
        df = SAMPLE_SPREAD_PREDICTIONS.copy()
        if params:
            if "season" in params:
                df = df[df["season"] == params["season"]]
            if "week" in params:
                df = df[df["week"] == params["week"]]
        return df
    elif "from predictions" in query_lower:
        # Filter sample predictions by params
        df = SAMPLE_PREDICTIONS.copy()
        if params:
            if "season" in params:
                df = df[df["season"] == params["season"]]
            if "week" in params:
                df = df[df["week"] == params["week"]]
            if "team" in params:
                team = params["team"]
                df = df[
                    (df["home_team"] == team) | (df["away_team"] == team)
                ]
        return df
    return pd.DataFrame()


@pytest.fixture
def mock_model():
    """Create a mock XGBClassifier."""
    model = MagicMock()
    model.get_booster.return_value.feature_names = [
        "home_rest",
        "away_rest",
        "div_game",
        "home_rolling_point_diff",
    ]
    return model


@pytest.fixture
def mock_spread_model():
    """Create a mock XGBRegressor."""
    model = MagicMock()
    model.get_booster.return_value.feature_names = [
        "home_rest",
        "away_rest",
        "div_game",
        "home_rolling_point_diff",
    ]
    return model


@pytest.fixture
def mock_settings(experiments_file):
    """Create mock settings pointing to temp experiments file."""
    ms = MagicMock()
    ms.RELOAD_TOKEN = "test-token"
    ms.MODEL_PATH = "models/artifacts/best_model.json"
    ms.EXPERIMENTS_PATH = experiments_file
    ms.CONFIDENCE_HIGH = 0.65
    ms.CONFIDENCE_MEDIUM = 0.55
    ms.SPREAD_MODEL_PATH = "models/artifacts/best_spread_model.json"
    ms.SPREAD_EXPERIMENTS_PATH = experiments_file
    ms.CORS_ORIGINS = ["http://localhost:3000"]
    return ms


@pytest.fixture
def client(mock_model, mock_spread_model, mock_settings):
    """FastAPI TestClient with mocked dependencies (no DB/model needed).

    Patches lifespan dependencies so TestClient runs without real DB/model,
    then also patches route-level dependencies for request handling.
    """
    mock_engine = MagicMock()

    with (
        # Patch lifespan dependencies (called when TestClient starts)
        patch("api.main.get_engine", return_value=mock_engine),
        patch("api.main.load_best_model", return_value=mock_model),
        patch("api.main.get_best_experiment", return_value=SAMPLE_EXPERIMENTS[0]),
        patch("api.main.load_best_spread_model", return_value=mock_spread_model),
        patch("api.main.get_best_spread_experiment", return_value=SAMPLE_SPREAD_EXPERIMENT),
        patch("api.main.settings", mock_settings),
        # Patch route-level dependencies
        patch("api.routes.predictions.pd.read_sql", side_effect=_mock_read_sql),
        patch("api.routes.predictions.detect_current_week", return_value=(2024, 5)),
        patch("api.routes.spreads.pd.read_sql", side_effect=_mock_read_sql),
        patch("api.routes.model.load_best_model", return_value=mock_model),
        patch("api.routes.model.get_best_experiment", return_value=SAMPLE_EXPERIMENTS[0]),
        patch("api.routes.model.detect_current_week", return_value=(2024, 5)),
        patch("api.routes.model.generate_predictions", return_value=[{"game_id": "test"}]),
        patch("api.routes.model.load_best_spread_model", return_value=mock_spread_model),
        patch("api.routes.model.get_best_spread_experiment", return_value=SAMPLE_SPREAD_EXPERIMENT),
        patch("api.routes.model.generate_spread_predictions", return_value=[{"game_id": "spread_test"}]),
        patch("api.routes.model.settings", mock_settings),
        patch("api.routes.experiments.settings", mock_settings),
    ):
        from api.main import app

        with TestClient(app, raise_server_exceptions=False) as tc:
            yield tc


@pytest.fixture
def offseason_client(mock_model, mock_spread_model, mock_settings):
    """Client where detect_current_week returns None (offseason)."""
    mock_engine = MagicMock()

    with (
        # Patch lifespan dependencies
        patch("api.main.get_engine", return_value=mock_engine),
        patch("api.main.load_best_model", return_value=mock_model),
        patch("api.main.get_best_experiment", return_value=SAMPLE_EXPERIMENTS[0]),
        patch("api.main.load_best_spread_model", return_value=mock_spread_model),
        patch("api.main.get_best_spread_experiment", return_value=SAMPLE_SPREAD_EXPERIMENT),
        patch("api.main.settings", mock_settings),
        # Patch route-level dependencies
        patch("api.routes.predictions.pd.read_sql", side_effect=_mock_read_sql),
        patch("api.routes.predictions.detect_current_week", return_value=None),
        patch("api.routes.spreads.pd.read_sql", side_effect=_mock_read_sql),
        patch("api.routes.model.settings", mock_settings),
        patch("api.routes.experiments.settings", mock_settings),
    ):
        from api.main import app

        with TestClient(app, raise_server_exceptions=False) as tc:
            yield tc


@pytest.fixture
def no_spread_client(mock_model, mock_settings):
    """Client where spread model is not available (graceful degradation)."""
    mock_engine = MagicMock()

    with (
        patch("api.main.get_engine", return_value=mock_engine),
        patch("api.main.load_best_model", return_value=mock_model),
        patch("api.main.get_best_experiment", return_value=SAMPLE_EXPERIMENTS[0]),
        patch("api.main.load_best_spread_model", side_effect=FileNotFoundError("not found")),
        patch("api.main.get_best_spread_experiment", side_effect=FileNotFoundError("not found")),
        patch("api.main.settings", mock_settings),
        patch("api.routes.predictions.pd.read_sql", side_effect=_mock_read_sql),
        patch("api.routes.predictions.detect_current_week", return_value=(2024, 5)),
        patch("api.routes.model.load_best_model", return_value=mock_model),
        patch("api.routes.model.get_best_experiment", return_value=SAMPLE_EXPERIMENTS[0]),
        patch("api.routes.model.detect_current_week", return_value=(2024, 5)),
        patch("api.routes.model.generate_predictions", return_value=[{"game_id": "test"}]),
        patch("api.routes.model.load_best_spread_model", side_effect=FileNotFoundError("not found")),
        patch("api.routes.model.get_best_spread_experiment", side_effect=FileNotFoundError("not found")),
        patch("api.routes.model.settings", mock_settings),
        patch("api.routes.experiments.settings", mock_settings),
    ):
        from api.main import app

        with TestClient(app, raise_server_exceptions=False) as tc:
            yield tc
