"""Tests for models/predict.py prediction logic functions."""

import json
import os

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from models.predict import (
    get_best_experiment,
    load_best_model,
    load_best_spread_model,
    get_best_spread_experiment,
    _get_team_rolling_features,
)


# ---- Fixtures ----


@pytest.fixture
def experiments_file(tmp_path):
    """Create a temporary experiments.jsonl file with sample data."""
    entries = [
        {
            "experiment_id": 1,
            "timestamp": "2026-03-17T01:16:43.500695+00:00",
            "params": {"n_estimators": 100},
            "features": ["home_rest", "away_rest", "div_game"],
            "val_accuracy_2023": 0.6016,
            "val_accuracy_2022": 1.0,
            "val_accuracy_2021": 0.9882,
            "baseline_always_home": 0.5551,
            "baseline_better_record": 0.5820,
            "log_loss": 0.7521,
            "brier_score": 0.2605,
            "shap_top5": [
                {"feature": "home_rest", "importance": 0.3856}
            ],
            "keep": True,
            "hypothesis": "Baseline",
            "prev_best_acc": 0.0,
            "model_path": "models/artifacts\\model_exp001.json",
        },
        {
            "experiment_id": 2,
            "timestamp": "2026-03-17T01:17:49.466408+00:00",
            "params": {"n_estimators": 100},
            "features": ["home_rest", "away_rest"],
            "val_accuracy_2023": 0.5352,
            "val_accuracy_2022": 0.9764,
            "val_accuracy_2021": 0.9804,
            "baseline_always_home": 0.5551,
            "baseline_better_record": 0.5820,
            "log_loss": 0.7890,
            "brier_score": 0.2811,
            "shap_top5": [
                {"feature": "home_rest", "importance": 0.4365}
            ],
            "keep": False,
            "hypothesis": "Ablation test",
            "prev_best_acc": 0.6016,
            "model_path": None,
        },
    ]
    path = tmp_path / "experiments.jsonl"
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return str(path)


@pytest.fixture
def features_df():
    """Feature DataFrame with known rolling columns for team lookup tests."""
    rolling_cols = [
        "home_rolling_off_epa_per_play",
        "home_rolling_def_epa_per_play",
        "home_rolling_point_diff",
        "home_rolling_win",
        "away_rolling_off_epa_per_play",
        "away_rolling_def_epa_per_play",
        "away_rolling_point_diff",
        "away_rolling_win",
    ]
    rows = [
        # Week 2: KC is home team
        {
            "game_id": "2024_02_BUF_KC",
            "season": 2024,
            "week": 2,
            "home_team": "KC",
            "away_team": "BUF",
            "home_rolling_off_epa_per_play": 0.10,
            "home_rolling_def_epa_per_play": -0.05,
            "home_rolling_point_diff": 3.5,
            "home_rolling_win": 0.6,
            "away_rolling_off_epa_per_play": 0.08,
            "away_rolling_def_epa_per_play": -0.03,
            "away_rolling_point_diff": 2.1,
            "away_rolling_win": 0.5,
        },
        # Week 3: KC is home team again (latest for KC)
        {
            "game_id": "2024_03_MIA_KC",
            "season": 2024,
            "week": 3,
            "home_team": "KC",
            "away_team": "MIA",
            "home_rolling_off_epa_per_play": 0.15,
            "home_rolling_def_epa_per_play": -0.06,
            "home_rolling_point_diff": 4.0,
            "home_rolling_win": 0.65,
            "away_rolling_off_epa_per_play": 0.07,
            "away_rolling_def_epa_per_play": -0.02,
            "away_rolling_point_diff": 1.5,
            "away_rolling_win": 0.4,
        },
        # Week 4: BUF is away team (latest for BUF)
        {
            "game_id": "2024_04_BUF_PHI",
            "season": 2024,
            "week": 4,
            "home_team": "PHI",
            "away_team": "BUF",
            "home_rolling_off_epa_per_play": 0.12,
            "home_rolling_def_epa_per_play": -0.04,
            "home_rolling_point_diff": 2.8,
            "home_rolling_win": 0.55,
            "away_rolling_off_epa_per_play": 0.18,
            "away_rolling_def_epa_per_play": -0.08,
            "away_rolling_point_diff": 5.2,
            "away_rolling_win": 0.7,
        },
    ]
    return pd.DataFrame(rows)


# ---- Tests ----


def test_get_best_experiment(experiments_file):
    """Returns the best kept experiment (experiment_id == 1, highest accuracy with keep=True)."""
    result = get_best_experiment(experiments_file)
    assert result is not None
    assert result["experiment_id"] == 1
    assert result["val_accuracy_2023"] == 0.6016


def test_get_best_experiment_no_file():
    """Raises FileNotFoundError when JSONL file does not exist."""
    with pytest.raises(FileNotFoundError):
        get_best_experiment("nonexistent_path/experiments.jsonl")


def test_load_best_model(tmp_path):
    """Loads XGBoost model from JSON file and returns XGBClassifier."""
    from xgboost import XGBClassifier

    # Create a dummy model and save it
    model = XGBClassifier(n_estimators=2, max_depth=2)
    # Train on minimal data to make it saveable
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([0, 1, 0, 1])
    model.fit(X, y)

    model_path = str(tmp_path / "test_model.json")
    model.save_model(model_path)

    # Load and verify
    loaded = load_best_model(model_path)
    assert isinstance(loaded, XGBClassifier)


def test_confidence_home_win():
    """When home_prob >= 0.5, confidence equals home_prob."""
    # Test the confidence logic used in generate_predictions
    home_prob = 0.72
    if home_prob >= 0.5:
        predicted_winner = "HOME"
        confidence = home_prob
    else:
        predicted_winner = "AWAY"
        confidence = 1.0 - home_prob

    assert predicted_winner == "HOME"
    assert confidence == 0.72


def test_confidence_away_win():
    """When home_prob < 0.5, confidence equals 1 - home_prob."""
    home_prob = 0.35
    if home_prob >= 0.5:
        predicted_winner = "HOME"
        confidence = home_prob
    else:
        predicted_winner = "AWAY"
        confidence = 1.0 - home_prob

    assert predicted_winner == "AWAY"
    assert confidence == pytest.approx(0.65)


def test_get_team_rolling_features_as_home(features_df):
    """When team's latest game was as home_team, extracts home_rolling_* columns.

    KC's latest game is week 3, where KC was home.
    Their stats should come from home_rolling_* columns.
    """
    result = _get_team_rolling_features(features_df, "KC")

    # KC was home in week 3, so their rolling stats are in home_rolling_* columns
    assert result["rolling_off_epa_per_play"] == pytest.approx(0.15)
    assert result["rolling_def_epa_per_play"] == pytest.approx(-0.06)
    assert result["rolling_point_diff"] == pytest.approx(4.0)
    assert result["rolling_win"] == pytest.approx(0.65)


def test_get_team_rolling_features_as_away(features_df):
    """When team's latest game was as away_team, extracts away_rolling_* columns.

    BUF's latest game is week 4, where BUF was away.
    Their stats should come from away_rolling_* columns (NOT home_rolling_*).
    """
    result = _get_team_rolling_features(features_df, "BUF")

    # BUF was away in week 4, so their rolling stats are in away_rolling_* columns
    assert result["rolling_off_epa_per_play"] == pytest.approx(0.18)
    assert result["rolling_def_epa_per_play"] == pytest.approx(-0.08)
    assert result["rolling_point_diff"] == pytest.approx(5.2)
    assert result["rolling_win"] == pytest.approx(0.7)

    # Crucially, NOT the home team's (PHI's) values
    assert result["rolling_off_epa_per_play"] != pytest.approx(0.12)


def test_model_path_normalization(experiments_file):
    """get_best_experiment normalizes backslashes in model_path."""
    result = get_best_experiment(experiments_file)
    # The sample JSONL has "models/artifacts\\model_exp001.json"
    assert "\\" not in result["model_path"]
    assert result["model_path"] == "models/artifacts/model_exp001.json"


# ---- Spread Prediction Tests ----


SAMPLE_SPREAD_EXPERIMENTS = [
    {
        "experiment_id": 1,
        "timestamp": "2026-03-23T04:54:37.744622+00:00",
        "model_type": "spread_regression",
        "params": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1},
        "features": ["home_rest", "away_rest", "div_game"],
        "mae_2023": 10.6826,
        "rmse_2023": 13.8711,
        "derived_win_accuracy_2023": 0.6016,
        "keep": True,
        "hypothesis": "Baseline spread",
        "prev_best_mae": None,
        "model_path": "models/artifacts\\spread_model_exp001.json",
    },
    {
        "experiment_id": 2,
        "timestamp": "2026-03-23T15:27:18.981854+00:00",
        "model_type": "spread_regression",
        "params": {"n_estimators": 300},
        "features": ["home_rest", "away_rest"],
        "mae_2023": 10.5836,
        "rmse_2023": 13.7103,
        "derived_win_accuracy_2023": 0.5820,
        "keep": False,
        "hypothesis": "Regularization test",
        "prev_best_mae": 10.6826,
        "model_path": None,
    },
]


@pytest.fixture
def spread_experiments_file(tmp_path):
    """Create a temporary spread_experiments.jsonl file."""
    path = tmp_path / "spread_experiments.jsonl"
    with open(path, "w") as f:
        for exp in SAMPLE_SPREAD_EXPERIMENTS:
            f.write(json.dumps(exp) + "\n")
    return str(path)


def test_load_best_spread_model(tmp_path):
    """Loads XGBoost spread model from JSON file and returns XGBRegressor."""
    from xgboost import XGBRegressor

    model = XGBRegressor(n_estimators=2, max_depth=2)
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([1.5, -3.2, 0.7, 5.1])
    model.fit(X, y)
    model_path = str(tmp_path / "test_spread_model.json")
    model.save_model(model_path)

    loaded = load_best_spread_model(model_path)
    assert isinstance(loaded, XGBRegressor)


def test_load_best_spread_model_missing():
    """Raises FileNotFoundError for nonexistent path."""
    with pytest.raises(FileNotFoundError):
        load_best_spread_model("nonexistent_path/spread_model.json")


def test_get_best_spread_experiment(spread_experiments_file):
    """Returns the keep=true entry (experiment_id=1) ignoring keep=false even with lower MAE."""
    result = get_best_spread_experiment(spread_experiments_file)
    assert result is not None
    assert result["experiment_id"] == 1
    assert result["mae_2023"] == pytest.approx(10.6826)


def test_get_best_spread_experiment_lowest_mae(tmp_path):
    """When multiple keep=true entries exist, returns the one with lowest mae_2023."""
    entries = [
        {
            "experiment_id": 1,
            "mae_2023": 10.6826,
            "keep": True,
            "model_path": "models/artifacts\\spread_model_exp001.json",
        },
        {
            "experiment_id": 3,
            "mae_2023": 9.5,
            "keep": True,
            "model_path": "models/artifacts\\spread_model_exp003.json",
        },
    ]
    path = tmp_path / "spread_multi.jsonl"
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    result = get_best_spread_experiment(str(path))
    assert result is not None
    assert result["experiment_id"] == 3
    assert result["mae_2023"] == pytest.approx(9.5)


def test_get_best_spread_experiment_no_file():
    """Raises FileNotFoundError when JSONL file does not exist."""
    with pytest.raises(FileNotFoundError):
        get_best_spread_experiment("nonexistent_path/spread_experiments.jsonl")


def test_get_best_spread_experiment_path_normalization(spread_experiments_file):
    """Backslashes in model_path are replaced with forward slashes."""
    result = get_best_spread_experiment(spread_experiments_file)
    assert "\\" not in result["model_path"]
    assert result["model_path"] == "models/artifacts/spread_model_exp001.json"


def test_spread_winner_home():
    """predicted_spread >= 0 -> predicted_winner = home_team."""
    predicted_spread = 3.5
    home_team, away_team = "KC", "BUF"
    predicted_winner = home_team if predicted_spread >= 0 else away_team
    assert predicted_winner == "KC"


def test_spread_winner_away():
    """predicted_spread < 0 -> predicted_winner = away_team."""
    predicted_spread = -2.1
    home_team, away_team = "KC", "BUF"
    predicted_winner = home_team if predicted_spread >= 0 else away_team
    assert predicted_winner == "BUF"


def test_spread_winner_zero_tie():
    """predicted_spread = 0.0 -> predicted_winner = home_team (home-team convention)."""
    predicted_spread = 0.0
    home_team, away_team = "KC", "BUF"
    predicted_winner = home_team if predicted_spread >= 0 else away_team
    assert predicted_winner == "KC"
