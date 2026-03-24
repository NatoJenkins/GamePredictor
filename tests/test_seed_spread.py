"""Unit tests for spread prediction seeding script.

Tests cover:
1. Regression inference (model.predict, NOT predict_proba)
2. Actual spread computation (home_score - away_score)
3. Idempotent upsert (ON CONFLICT DO UPDATE)
"""

from unittest.mock import MagicMock, patch, call

import numpy as np
import pandas as pd
import pytest


def _build_mock_features_df(feature_names):
    """Build a mock features DataFrame with 2 completed games."""
    data = {
        "game_id": ["2023_01_ARI_WAS", "2023_01_ATL_CAR"],
        "season": [2023, 2023],
        "week": [1, 1],
        "home_team": ["WAS", "CAR"],
        "away_team": ["ARI", "ATL"],
        "home_win": [1.0, 0.0],
        "home_rolling_win_pct": [0.5, 0.4],
    }
    # Add feature columns matching model expectation
    for feat in feature_names:
        if feat not in data:
            data[feat] = [0.5, 0.6]
    return pd.DataFrame(data)


def _build_mock_schedule_df():
    """Build a mock schedule DataFrame with game scores."""
    return pd.DataFrame({
        "game_id": ["2023_01_ARI_WAS", "2023_01_ATL_CAR"],
        "gameday": ["2023-09-10", "2023-09-10"],
        "home_score": [24, 17],
        "away_score": [17, 24],
    })


def _setup_mocks():
    """Create common mock objects for seed_spread tests."""
    feature_names = [
        "home_rolling_win_pct", "away_rolling_win_pct",
        "home_rest", "away_rest", "div_game",
    ]

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([3.5, -7.2])
    mock_model.get_booster.return_value.feature_names = feature_names

    mock_experiment = {"experiment_id": 1}

    features_df = _build_mock_features_df(feature_names)
    schedule_df = _build_mock_schedule_df()

    return mock_model, mock_experiment, features_df, schedule_df, feature_names


@patch("scripts.seed_spread.get_table")
@patch("scripts.seed_spread.get_engine")
@patch("scripts.seed_spread.build_game_features")
@patch("scripts.seed_spread.get_best_spread_experiment")
@patch("scripts.seed_spread.load_best_spread_model")
def test_seed_spread_predictions(
    mock_load_model,
    mock_get_experiment,
    mock_build_features,
    mock_get_engine,
    mock_get_table,
):
    """Verify model.predict() is called (regression), NOT predict_proba.

    Also verifies predicted_winner convention:
    - spread 3.5 -> home team wins (positive = home advantage)
    - spread -7.2 -> away team wins (negative = away advantage)
    """
    mock_model, mock_experiment, features_df, schedule_df, _ = _setup_mocks()

    mock_load_model.return_value = mock_model
    mock_get_experiment.return_value = mock_experiment
    mock_build_features.return_value = features_df

    # Mock engine and schedule query
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    # Mock pd.read_sql to return schedule data
    with patch("scripts.seed_spread.pd.read_sql", return_value=schedule_df):
        # Mock the upsert chain
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        with patch("scripts.seed_spread.pg_insert") as mock_pg_insert:
            mock_stmt = MagicMock()
            mock_pg_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt
            mock_stmt.excluded = MagicMock()

            from scripts.seed_spread import seed_spread_predictions
            result = seed_spread_predictions(season=2023)

    # Verify model.predict() was called (regression)
    mock_model.predict.assert_called_once()
    # Verify predict_proba was NOT called
    assert not mock_model.predict_proba.called

    # Verify predicted_winner convention from the records passed to upsert
    # We need to check the values passed to the insert statement
    insert_call_args = mock_pg_insert.call_args
    values_call_args = mock_stmt.values.call_args

    records = values_call_args[0][0]

    # Game 1: spread 3.5 -> home (WAS) wins
    assert records[0]["predicted_winner"] == "WAS"
    assert records[0]["predicted_spread"] == pytest.approx(3.5)

    # Game 2: spread -7.2 -> away (ATL) wins
    assert records[1]["predicted_winner"] == "ATL"
    assert records[1]["predicted_spread"] == pytest.approx(-7.2)

    # Should return count of records
    assert result == 2


@patch("scripts.seed_spread.get_table")
@patch("scripts.seed_spread.get_engine")
@patch("scripts.seed_spread.build_game_features")
@patch("scripts.seed_spread.get_best_spread_experiment")
@patch("scripts.seed_spread.load_best_spread_model")
def test_seed_spread_backfills_actuals(
    mock_load_model,
    mock_get_experiment,
    mock_build_features,
    mock_get_engine,
    mock_get_table,
):
    """Verify actual columns are computed correctly.

    Game 1: home_score=24, away_score=17
      -> actual_spread = 24 - 17 = 7.0 (home minus away)
      -> actual_winner = WAS (home team, positive spread)
      -> With predicted_spread=3.5, predicted_winner=WAS -> correct=True

    Game 2: home_score=17, away_score=24
      -> actual_spread = 17 - 24 = -7.0 (home minus away)
      -> actual_winner = ATL (away team, negative spread)
      -> With predicted_spread=-7.2, predicted_winner=ATL -> correct=True
    """
    mock_model, mock_experiment, features_df, schedule_df, _ = _setup_mocks()

    mock_load_model.return_value = mock_model
    mock_get_experiment.return_value = mock_experiment
    mock_build_features.return_value = features_df

    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    with patch("scripts.seed_spread.pd.read_sql", return_value=schedule_df):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        with patch("scripts.seed_spread.pg_insert") as mock_pg_insert:
            mock_stmt = MagicMock()
            mock_pg_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt
            mock_stmt.excluded = MagicMock()

            from scripts.seed_spread import seed_spread_predictions
            seed_spread_predictions(season=2023)

    records = mock_stmt.values.call_args[0][0]

    # Game 1: home_score=24, away_score=17
    assert records[0]["actual_spread"] == pytest.approx(7.0)
    assert records[0]["actual_winner"] == "WAS"  # home team (positive spread)
    assert records[0]["correct"] is True  # predicted WAS, actual WAS

    # Game 2: home_score=17, away_score=24
    assert records[1]["actual_spread"] == pytest.approx(-7.0)
    assert records[1]["actual_winner"] == "ATL"  # away team (negative spread)
    assert records[1]["correct"] is True  # predicted ATL, actual ATL


@patch("scripts.seed_spread.get_table")
@patch("scripts.seed_spread.get_engine")
@patch("scripts.seed_spread.build_game_features")
@patch("scripts.seed_spread.get_best_spread_experiment")
@patch("scripts.seed_spread.load_best_spread_model")
def test_seed_spread_idempotent(
    mock_load_model,
    mock_get_experiment,
    mock_build_features,
    mock_get_engine,
    mock_get_table,
):
    """Verify upsert uses ON CONFLICT DO UPDATE with index_elements=['game_id'].

    This ensures re-running the seed script does not create duplicate records.
    """
    mock_model, mock_experiment, features_df, schedule_df, _ = _setup_mocks()

    mock_load_model.return_value = mock_model
    mock_get_experiment.return_value = mock_experiment
    mock_build_features.return_value = features_df

    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    with patch("scripts.seed_spread.pd.read_sql", return_value=schedule_df):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        with patch("scripts.seed_spread.pg_insert") as mock_pg_insert:
            mock_stmt = MagicMock()
            mock_pg_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt
            mock_stmt.excluded = MagicMock()

            from scripts.seed_spread import seed_spread_predictions

            # Call twice to verify idempotency
            seed_spread_predictions(season=2023)
            seed_spread_predictions(season=2023)

    # Verify on_conflict_do_update was called with correct index_elements
    conflict_calls = mock_stmt.on_conflict_do_update.call_args_list
    assert len(conflict_calls) >= 2  # Called at least once per invocation

    for conflict_call in conflict_calls:
        assert conflict_call[1]["index_elements"] == ["game_id"]

    # Verify pg_insert was called with the spread_predictions table
    for pg_call in mock_pg_insert.call_args_list:
        assert pg_call[0][0] == mock_table  # table object passed to pg_insert
