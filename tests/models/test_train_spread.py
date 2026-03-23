"""Unit tests for spread regression training pipeline (models/train_spread.py).

Tests cover:
- Temporal split correctness and boundary enforcement (TRAIN-01)
- Metric evaluation: MAE, RMSE, derived win accuracy on 2023 + overfitting monitoring (TRAIN-02)
- Naive spread baselines (always +2.5 and always 0) (TRAIN-03)
- JSONL logging with full metadata and spread-specific schema (TRAIN-04)
- Model save/load for both experiment and best model artifacts (TRAIN-05)
"""

import json
import os

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error

from tests.models.conftest import ROLLING_COLS
from models.train_spread import (
    DEFAULT_SPREAD_PARAMS,
    META_COLS,
    compute_spread_baselines,
    load_and_split_spread,
    log_spread_experiment,
    save_best_spread_model,
    save_spread_model,
    train_and_evaluate_spread,
)


def _make_spread_df(
    seasons: list[int],
    rows_per_season: int = 10,
    include_nan_week1: bool = True,
) -> tuple[pd.DataFrame, pd.Series]:
    """Build a synthetic multi-season feature DataFrame for spread split tests.

    Args:
        seasons: List of seasons to include.
        rows_per_season: Games per season (default 10).
        include_nan_week1: If True, week 1 of each season has NaN rolling features.

    Returns:
        Tuple of (DataFrame mimicking build_game_features() output, target Series).
    """
    np.random.seed(42)
    teams = ["KC", "BUF", "SF", "PHI", "DAL", "MIA", "BAL", "DET", "CIN", "JAX"]
    rows = []
    targets = []

    for season in seasons:
        n = rows_per_season
        spread_values = np.random.normal(2.5, 14.0, n)

        for i in range(n):
            week = i + 1
            home = teams[i % len(teams)]
            away = teams[(i + 1) % len(teams)]

            # Rolling features: NaN for week 1, known values otherwise
            if include_nan_week1 and week == 1:
                rolling_vals = {col: np.nan for col in ROLLING_COLS}
            else:
                rolling_vals = {col: 0.5 + (i * 0.01) for col in ROLLING_COLS}

            # Binary home_win for classifier compatibility
            home_win = float(1 if spread_values[i] > 0 else 0)

            row = {
                "game_id": f"{season}_{week:02d}_{away}_{home}",
                "season": season,
                "week": week,
                "gameday": f"{season}-09-{10 + i:02d}",
                "home_team": home,
                "away_team": away,
                "home_win": home_win,
                "home_rest": 7,
                "away_rest": 7,
                "div_game": 0,
            }
            row.update(rolling_vals)
            rows.append(row)
            targets.append(spread_values[i])

    df = pd.DataFrame(rows)
    target_series = pd.Series(targets, name="spread_target")
    return df, target_series


class TestSpreadSplit:
    """Tests for load_and_split_spread temporal boundary enforcement (TRAIN-01)."""

    def test_temporal_split_boundaries(self):
        """load_and_split_spread assigns 2021+2022 to train and 2023 to val_2023."""
        df, target = _make_spread_df(
            seasons=[2021, 2022, 2023],
            rows_per_season=10,
            include_nan_week1=True,
        )
        train, val_2023, val_2022, val_2021, feature_cols = load_and_split_spread(
            df, target
        )

        # Train should contain 2021 and 2022
        assert set(train["season"].unique()) == {2021, 2022}

        # val_2023 should contain only 2023
        assert set(val_2023["season"].unique()) == {2023}

        # val_2022 and val_2021 are subsets of training data
        assert set(val_2022["season"].unique()) == {2022}
        assert set(val_2021["season"].unique()) == {2021}

    def test_feature_cols_count(self):
        """Feature columns should be exactly 17 (14 rolling + 3 situational)."""
        df, target = _make_spread_df(
            seasons=[2021, 2022, 2023],
            rows_per_season=10,
            include_nan_week1=False,
        )
        _, _, _, _, feature_cols = load_and_split_spread(df, target)

        assert len(feature_cols) == 17, (
            f"Expected 17 feature columns (14 rolling + 3 situational), got {len(feature_cols)}: {feature_cols}"
        )

    def test_forbidden_features_excluded(self):
        """Forbidden features (result, home_score, away_score) are not in feature_cols."""
        from features.definitions import FORBIDDEN_FEATURES

        df, target = _make_spread_df(
            seasons=[2022, 2023],
            rows_per_season=5,
            include_nan_week1=False,
        )
        _, _, _, _, feature_cols = load_and_split_spread(df, target)

        for forbidden in FORBIDDEN_FEATURES:
            assert forbidden not in feature_cols, (
                f"Forbidden feature '{forbidden}' found in feature_cols"
            )

    def test_nan_week1_dropped(self):
        """Week-1 rows with NaN rolling features are dropped from all splits."""
        df, target = _make_spread_df(
            seasons=[2021, 2022, 2023],
            rows_per_season=10,
            include_nan_week1=True,
        )
        train, val_2023, val_2022, val_2021, feature_cols = load_and_split_spread(
            df, target
        )

        # After split, no NaN in feature columns for any split
        for split_name, split_df in [
            ("train", train),
            ("val_2023", val_2023),
            ("val_2022", val_2022),
            ("val_2021", val_2021),
        ]:
            for col in feature_cols:
                assert split_df[col].isna().sum() == 0, (
                    f"NaN found in {split_name}[{col}]"
                )


class TestSpreadEval:
    """Tests for train_and_evaluate_spread function (TRAIN-02)."""

    @pytest.fixture
    def spread_training_data(self):
        """Prepare small synthetic training/evaluation data for spread tests."""
        np.random.seed(42)
        n_train = 20
        n_val = 5
        n_features = 17

        feature_names = [f"feat_{i}" for i in range(n_features)]

        def make_set(n):
            X = pd.DataFrame(
                np.random.randn(n, n_features),
                columns=feature_names,
            )
            y = pd.Series(np.random.normal(2.5, 14.0, size=n))
            return X, y

        X_train, y_train = make_set(n_train)
        X_val_2023, y_val_2023 = make_set(n_val)
        X_val_2022, y_val_2022 = make_set(n_val)
        X_val_2021, y_val_2021 = make_set(n_val)

        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val_2023": X_val_2023,
            "y_val_2023": y_val_2023,
            "X_val_2022": X_val_2022,
            "y_val_2022": y_val_2022,
            "X_val_2021": X_val_2021,
            "y_val_2021": y_val_2021,
        }

    def test_returns_all_metrics(self, spread_training_data):
        """train_and_evaluate_spread returns dict with all 9 metric keys plus shap_top5."""
        params = {**DEFAULT_SPREAD_PARAMS, "n_estimators": 10, "early_stopping_rounds": 5}
        results, model = train_and_evaluate_spread(
            **spread_training_data,
            params=params,
        )

        expected_keys = {
            "mae_2023", "rmse_2023", "derived_win_accuracy_2023",
            "mae_2022", "rmse_2022", "derived_win_accuracy_2022",
            "mae_2021", "rmse_2021", "derived_win_accuracy_2021",
            "shap_top5",
        }
        assert expected_keys.issubset(set(results.keys())), (
            f"Missing keys: {expected_keys - set(results.keys())}"
        )

    def test_metric_ranges(self, spread_training_data):
        """All MAE/RMSE values are >= 0; derived_win_accuracy is between 0 and 1."""
        params = {**DEFAULT_SPREAD_PARAMS, "n_estimators": 10, "early_stopping_rounds": 5}
        results, _ = train_and_evaluate_spread(
            **spread_training_data,
            params=params,
        )

        for season in ["2023", "2022", "2021"]:
            assert results[f"mae_{season}"] >= 0, f"mae_{season} should be >= 0"
            assert results[f"rmse_{season}"] >= 0, f"rmse_{season} should be >= 0"
            assert 0 <= results[f"derived_win_accuracy_{season}"] <= 1, (
                f"derived_win_accuracy_{season} should be between 0 and 1"
            )

    def test_shap_top5_format(self, spread_training_data):
        """shap_top5 has 5 entries, each is (str, float) tuple."""
        params = {**DEFAULT_SPREAD_PARAMS, "n_estimators": 10, "early_stopping_rounds": 5}
        results, _ = train_and_evaluate_spread(
            **spread_training_data,
            params=params,
        )

        shap_top5 = results["shap_top5"]
        assert isinstance(shap_top5, list)
        assert len(shap_top5) == 5

        for item in shap_top5:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)  # feature name
            assert isinstance(item[1], float)  # importance value
            assert item[1] >= 0  # mean absolute SHAP is non-negative

    def test_objective_override_no_error(self, spread_training_data):
        """Passing objective='reg:pseudohubererror' in params does NOT raise TypeError."""
        params = {
            **DEFAULT_SPREAD_PARAMS,
            "n_estimators": 10,
            "early_stopping_rounds": 5,
            "objective": "reg:pseudohubererror",
        }
        # Should not raise TypeError
        results, model = train_and_evaluate_spread(
            **spread_training_data,
            params=params,
        )
        assert "mae_2023" in results


class TestSpreadBaselines:
    """Tests for compute_spread_baselines function (TRAIN-03)."""

    def test_baseline_keys(self):
        """Result has 'always_home_25' and 'always_zero' keys with sub-keys."""
        y_true = np.array([7.0, -3.0, 14.0, 0.0, -10.0])
        baselines = compute_spread_baselines(y_true)

        assert "always_home_25" in baselines
        assert "always_zero" in baselines

        for key in ["always_home_25", "always_zero"]:
            assert "mae" in baselines[key]
            assert "rmse" in baselines[key]
            assert "derived_win_accuracy" in baselines[key]

    def test_baseline_values(self):
        """Baseline MAE values match manual computation."""
        y_true = np.array([7.0, -3.0, 14.0, 0.0, -10.0])
        baselines = compute_spread_baselines(y_true)

        # Manually compute expected MAE for always +2.5
        pred_25 = np.full(5, 2.5)
        expected_mae_25 = mean_absolute_error(y_true, pred_25)

        # Manually compute expected MAE for always 0
        pred_zero = np.zeros(5)
        expected_mae_zero = mean_absolute_error(y_true, pred_zero)

        assert abs(baselines["always_home_25"]["mae"] - expected_mae_25) < 1e-6, (
            f"always_home_25 MAE {baselines['always_home_25']['mae']} != expected {expected_mae_25}"
        )
        assert abs(baselines["always_zero"]["mae"] - expected_mae_zero) < 1e-6, (
            f"always_zero MAE {baselines['always_zero']['mae']} != expected {expected_mae_zero}"
        )


class TestSpreadLogging:
    """Tests for log_spread_experiment JSONL logging (TRAIN-04)."""

    SAMPLE_PARAMS = {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1}
    SAMPLE_FEATURES = [f"feat_{i}" for i in range(17)]
    SAMPLE_RESULTS = {
        "mae_2023": 10.68,
        "rmse_2023": 13.87,
        "derived_win_accuracy_2023": 0.6016,
        "mae_2022": 8.71,
        "rmse_2022": 11.20,
        "derived_win_accuracy_2022": 0.6969,
        "mae_2021": 10.61,
        "rmse_2021": 13.36,
        "derived_win_accuracy_2021": 0.6745,
        "shap_top5": [
            ("feat_0", 1.7392),
            ("feat_1", 1.1188),
            ("feat_2", 0.9038),
            ("feat_3", 0.3756),
            ("feat_4", 0.3672),
        ],
    }
    SAMPLE_BASELINES = {
        "always_home_25": {"mae": 11.02, "rmse": 14.27, "derived_win_accuracy": 0.5664},
        "always_zero": {"mae": 11.26, "rmse": 14.59, "derived_win_accuracy": 0.4336},
    }

    def test_jsonl_append(self, tmp_path):
        """log_spread_experiment creates/appends to JSONL file."""
        jsonl_path = str(tmp_path / "spread_experiments.jsonl")

        log_spread_experiment(
            experiment_id=1,
            params=self.SAMPLE_PARAMS,
            features_used=self.SAMPLE_FEATURES,
            results=self.SAMPLE_RESULTS,
            baselines=self.SAMPLE_BASELINES,
            keep=True,
            hypothesis="Baseline test",
            prev_best_mae=None,
            model_path=None,
            jsonl_path=jsonl_path,
        )

        assert os.path.exists(jsonl_path)
        with open(jsonl_path) as f:
            lines = f.readlines()
        assert len(lines) == 1

        # Append a second entry
        log_spread_experiment(
            experiment_id=2,
            params=self.SAMPLE_PARAMS,
            features_used=self.SAMPLE_FEATURES,
            results=self.SAMPLE_RESULTS,
            baselines=self.SAMPLE_BASELINES,
            keep=False,
            hypothesis="Second test",
            prev_best_mae=10.68,
            model_path=None,
            jsonl_path=jsonl_path,
        )

        with open(jsonl_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_jsonl_schema_fields(self, tmp_path):
        """Logged JSONL entry contains all required keys and model_type is 'spread_regression'."""
        jsonl_path = str(tmp_path / "spread_experiments.jsonl")

        log_spread_experiment(
            experiment_id=1,
            params=self.SAMPLE_PARAMS,
            features_used=self.SAMPLE_FEATURES,
            results=self.SAMPLE_RESULTS,
            baselines=self.SAMPLE_BASELINES,
            keep=True,
            hypothesis="Schema test",
            prev_best_mae=None,
            model_path="models/artifacts/spread_model_exp001.json",
            jsonl_path=jsonl_path,
        )

        with open(jsonl_path) as f:
            entry = json.loads(f.readline())

        required_keys = {
            "experiment_id",
            "timestamp",
            "model_type",
            "params",
            "features",
            "mae_2023",
            "rmse_2023",
            "derived_win_accuracy_2023",
            "mae_2022",
            "rmse_2022",
            "derived_win_accuracy_2022",
            "mae_2021",
            "rmse_2021",
            "derived_win_accuracy_2021",
            "baselines",
            "shap_top5",
            "keep",
            "hypothesis",
            "prev_best_mae",
            "model_path",
        }

        assert required_keys.issubset(set(entry.keys())), (
            f"Missing keys: {required_keys - set(entry.keys())}"
        )
        assert entry["model_type"] == "spread_regression"
        assert entry["experiment_id"] == 1
        assert entry["keep"] is True
        assert len(entry["shap_top5"]) == 5


class TestSpreadModelSave:
    """Tests for save_spread_model and save_best_spread_model (TRAIN-05)."""

    @pytest.fixture
    def small_model(self):
        """Train a minimal XGBRegressor for save/load tests."""
        from xgboost import XGBRegressor

        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(20, 5), columns=[f"f{i}" for i in range(5)])
        y = pd.Series(np.random.normal(2.5, 14.0, 20))

        model = XGBRegressor(
            n_estimators=5,
            max_depth=2,
            objective="reg:squarederror",
        )
        model.fit(X, y)
        return model

    def test_save_experiment_model(self, small_model, tmp_path):
        """save_spread_model creates file at artifacts/spread_model_exp{NNN}.json."""
        artifacts_dir = str(tmp_path / "artifacts")
        path = save_spread_model(small_model, experiment_id=1, artifacts_dir=artifacts_dir)

        assert os.path.exists(path)
        assert path.endswith("spread_model_exp001.json")

    def test_save_best_model(self, small_model, tmp_path):
        """save_best_spread_model creates best_spread_model.json that loads back."""
        from xgboost import XGBRegressor

        artifacts_dir = str(tmp_path / "artifacts")
        path = save_best_spread_model(small_model, artifacts_dir=artifacts_dir)

        assert os.path.exists(path)
        assert path.endswith("best_spread_model.json")

        # Load it back and verify it works
        loaded = XGBRegressor()
        loaded.load_model(path)

        # Verify loaded model can predict
        X_test = pd.DataFrame(
            np.random.randn(3, 5), columns=[f"f{i}" for i in range(5)]
        )
        preds = loaded.predict(X_test)
        assert len(preds) == 3
