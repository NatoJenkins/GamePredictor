"""Point spread regression training pipeline.

Trains an XGBoost regression model to predict the home team's point spread
(margin of victory). This model lives ALONGSIDE the existing classifier —
do NOT modify train.py, the classifier model, or existing predictions.

The regression target is schedules.result — the home team's point differential.
Example: home wins 24-17 → result = +7. Home loses 10-20 → result = -10.

Functions:
    load_and_split_spread: Temporal split with target JOIN from schedules.
    train_and_evaluate_spread: Train XGBRegressor + evaluate on multiple seasons.
    compute_spread_baselines: Naive baselines for regression comparison.
    log_spread_experiment: Logging to spread_experiments.jsonl.
    save_spread_model: Save model artifact by experiment ID.
    save_best_spread_model: Overwrite best spread model checkpoint.
"""

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from xgboost import XGBRegressor

from features.definitions import FORBIDDEN_FEATURES

# Metadata columns that are NOT model features
META_COLS = ["game_id", "season", "week", "gameday", "home_team", "away_team"]

# Spread target — joined from schedules, NOT a feature column
SPREAD_TARGET = "result"


def load_and_split_spread(df: pd.DataFrame, target_series: pd.Series) -> tuple:
    """Split feature matrix by season for spread regression.

    Temporal split (same as classifier, CLAUDE.md: hardcoded, never shuffle):
        - train: 2005-2022 (ALL seasons)
        - val_2023: 2023 (held-out validation — primary metric)
        - val_2022: 2022 subset of training data (in-sample evaluation)
        - val_2021: 2021 subset of training data (in-sample evaluation)

    Holdout 2024 is NEVER touched.

    Args:
        df: Feature DataFrame from build_game_features().
        target_series: Series of point spread values (schedules.result),
            indexed to match df.

    Returns:
        Tuple of (train, val_2023, val_2022, val_2021, feature_cols).
        Each split DataFrame includes a 'spread_target' column.
    """
    # Attach the spread target
    df = df.copy()
    df["spread_target"] = target_series.values

    # Feature columns = everything except meta columns, classifier target, and spread target
    feature_cols = [
        c for c in df.columns
        if c not in META_COLS + ["home_win", "spread_target"]
    ]

    # Assert no forbidden features leaked in
    for col in feature_cols:
        assert col not in FORBIDDEN_FEATURES, (
            f"Forbidden feature '{col}' found in feature columns. "
            f"CLAUDE.md: Never use result, home_score, or away_score as model features."
        )

    # Temporal split (hardcoded boundaries)
    train = df[df["season"].between(2005, 2022)].copy()
    val_2023 = df[df["season"] == 2023].copy()
    val_2022 = df[df["season"] == 2022].copy()
    val_2021 = df[df["season"] == 2021].copy()

    # Drop rows without a spread target (ties are fine for regression — spread=0)
    # But NaN means the game hasn't been played yet
    train = train.dropna(subset=["spread_target"])
    val_2023 = val_2023.dropna(subset=["spread_target"])
    val_2022 = val_2022.dropna(subset=["spread_target"])
    val_2021 = val_2021.dropna(subset=["spread_target"])

    # Drop week-1 NaN rolling feature rows
    train = train.dropna(subset=feature_cols)
    val_2023 = val_2023.dropna(subset=feature_cols)
    val_2022 = val_2022.dropna(subset=feature_cols)
    val_2021 = val_2021.dropna(subset=feature_cols)

    print(
        f"Train: {len(train)}, "
        f"Val 2023 (held-out): {len(val_2023)}, "
        f"Eval 2022 (in-sample): {len(val_2022)}, "
        f"Eval 2021 (in-sample): {len(val_2021)}"
    )

    return (train, val_2023, val_2022, val_2021, feature_cols)


def _derived_win_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Convert predicted spreads to win/loss picks and compute accuracy.

    Positive spread = home win, negative = away win.
    Ties (spread == 0) are excluded from accuracy calculation.

    Args:
        y_true: Actual point differentials.
        y_pred: Predicted point differentials.

    Returns:
        Win/loss accuracy as a float between 0.0 and 1.0.
    """
    # Exclude actual ties from accuracy calculation
    mask = y_true != 0
    y_true_filtered = y_true[mask]
    y_pred_filtered = y_pred[mask]

    if len(y_true_filtered) == 0:
        return 0.0

    actual_home_win = y_true_filtered > 0
    predicted_home_win = y_pred_filtered > 0

    return float((actual_home_win == predicted_home_win).mean())


def compute_spread_baselines(y_true_2023: np.ndarray) -> dict:
    """Compute naive spread baselines on 2023 validation set.

    Baselines:
    1. Always predict home +2.5 (approximate historical home field advantage)
    2. Always predict 0 (no advantage)

    Args:
        y_true_2023: Actual point differentials for 2023 validation set.

    Returns:
        Dict with baseline MAE, RMSE, and derived win accuracy for each.
    """
    n = len(y_true_2023)

    # Baseline 1: Always predict home +2.5
    pred_home_25 = np.full(n, 2.5)
    mae_home_25 = mean_absolute_error(y_true_2023, pred_home_25)
    rmse_home_25 = root_mean_squared_error(y_true_2023, pred_home_25)
    win_acc_home_25 = _derived_win_accuracy(y_true_2023, pred_home_25)

    # Baseline 2: Always predict 0
    pred_zero = np.zeros(n)
    mae_zero = mean_absolute_error(y_true_2023, pred_zero)
    rmse_zero = root_mean_squared_error(y_true_2023, pred_zero)
    win_acc_zero = _derived_win_accuracy(y_true_2023, pred_zero)

    return {
        "always_home_25": {
            "mae": float(mae_home_25),
            "rmse": float(rmse_home_25),
            "derived_win_accuracy": float(win_acc_home_25),
        },
        "always_zero": {
            "mae": float(mae_zero),
            "rmse": float(rmse_zero),
            "derived_win_accuracy": float(win_acc_zero),
        },
    }


def train_and_evaluate_spread(
    X_train,
    y_train,
    X_val_2023,
    y_val_2023,
    X_val_2022,
    y_val_2022,
    X_val_2021,
    y_val_2021,
    params: dict,
) -> tuple[dict, XGBRegressor]:
    """Train XGBoost regressor and evaluate on all validation/evaluation sets.

    Args:
        X_train, y_train: Training features and targets (2005-2022).
        X_val_2023, y_val_2023: Held-out 2023 validation set.
        X_val_2022, y_val_2022: In-sample 2022 evaluation set.
        X_val_2021, y_val_2021: In-sample 2021 evaluation set.
        params: XGBoost hyperparameters (passed to XGBRegressor).

    Returns:
        Tuple of (results_dict, model).
    """
    objective = params.pop("objective", "reg:squarederror")
    model = XGBRegressor(
        objective=objective,
        eval_metric="mae",
        **params,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val_2023, y_val_2023)],
        verbose=False,
    )

    # Predictions on all sets
    pred_2023 = model.predict(X_val_2023)
    pred_2022 = model.predict(X_val_2022)
    pred_2021 = model.predict(X_val_2021)

    results = {
        # Primary metrics on 2023 (held-out)
        "mae_2023": float(mean_absolute_error(y_val_2023, pred_2023)),
        "rmse_2023": float(root_mean_squared_error(y_val_2023, pred_2023)),
        "derived_win_accuracy_2023": _derived_win_accuracy(
            y_val_2023.values, pred_2023
        ),
        # In-sample metrics (overfitting monitoring)
        "mae_2022": float(mean_absolute_error(y_val_2022, pred_2022)),
        "rmse_2022": float(root_mean_squared_error(y_val_2022, pred_2022)),
        "derived_win_accuracy_2022": _derived_win_accuracy(
            y_val_2022.values, pred_2022
        ),
        "mae_2021": float(mean_absolute_error(y_val_2021, pred_2021)),
        "rmse_2021": float(root_mean_squared_error(y_val_2021, pred_2021)),
        "derived_win_accuracy_2021": _derived_win_accuracy(
            y_val_2021.values, pred_2021
        ),
    }

    # TreeSHAP feature importance (top 5 by mean absolute SHAP value)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_val_2023)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    feature_names = X_val_2023.columns.tolist()
    top5_idx = np.argsort(mean_abs_shap)[-5:][::-1]
    results["shap_top5"] = [
        (feature_names[i], float(mean_abs_shap[i])) for i in top5_idx
    ]

    return (results, model)


def log_spread_experiment(
    experiment_id: int,
    params: dict,
    features_used: list[str],
    results: dict,
    baselines: dict,
    keep: bool,
    hypothesis: str,
    prev_best_mae: float | None,
    model_path: str | None,
    jsonl_path: str = "models/spread_experiments.jsonl",
):
    """Log spread experiment to spread_experiments.jsonl (append-only).

    Args:
        experiment_id: Sequential experiment number.
        params: XGBoost hyperparameters used.
        features_used: List of feature column names.
        results: Dict of evaluation metrics from train_and_evaluate_spread.
        baselines: Dict of baseline metrics from compute_spread_baselines.
        keep: Whether experiment was kept.
        hypothesis: What was being tested.
        prev_best_mae: Previous best 2023 MAE (None for first experiment).
        model_path: Path to saved model artifact (None if reverted).
        jsonl_path: Path to JSONL log file.
    """
    entry = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_type": "spread_regression",
        "params": params,
        "features": features_used,
        # Primary metrics (2023 held-out)
        "mae_2023": results["mae_2023"],
        "rmse_2023": results["rmse_2023"],
        "derived_win_accuracy_2023": results["derived_win_accuracy_2023"],
        # In-sample metrics (overfitting monitoring)
        "mae_2022": results["mae_2022"],
        "rmse_2022": results["rmse_2022"],
        "derived_win_accuracy_2022": results["derived_win_accuracy_2022"],
        "mae_2021": results["mae_2021"],
        "rmse_2021": results["rmse_2021"],
        "derived_win_accuracy_2021": results["derived_win_accuracy_2021"],
        # Baselines
        "baselines": baselines,
        # SHAP
        "shap_top5": [
            {"feature": f, "importance": round(v, 4)}
            for f, v in results["shap_top5"]
        ],
        # Decision
        "keep": keep,
        "hypothesis": hypothesis,
        "prev_best_mae": prev_best_mae,
        "model_path": model_path,
    }

    # Append to JSONL (append-only, CLAUDE.md rule)
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def save_spread_model(
    model: XGBRegressor,
    experiment_id: int,
    artifacts_dir: str = "models/artifacts",
) -> str:
    """Save spread model using XGBoost native JSON format.

    Args:
        model: Trained XGBRegressor.
        experiment_id: Experiment number for filename.
        artifacts_dir: Directory for model artifacts.

    Returns:
        Path to saved model file.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(
        artifacts_dir, f"spread_model_exp{experiment_id:03d}.json"
    )
    model.save_model(path)
    return path


def save_best_spread_model(
    model: XGBRegressor,
    artifacts_dir: str = "models/artifacts",
) -> str:
    """Overwrite the best spread model checkpoint.

    Args:
        model: Trained XGBRegressor (current best).
        artifacts_dir: Directory for model artifacts.

    Returns:
        Path to saved best spread model file.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(artifacts_dir, "best_spread_model.json")
    model.save_model(path)
    return path


# ---------------------------------------------------------------------------
# Experiment runner entry point
# ---------------------------------------------------------------------------

# Default XGBoost regression parameters (Spread Experiment 1 baseline)
DEFAULT_SPREAD_PARAMS = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "reg_alpha": 0,
    "reg_lambda": 1,
    "min_child_weight": 1,
    "gamma": 0,
    "early_stopping_rounds": 20,
}

# Current experiment configuration
EXPERIMENT_ID = 1
EXPERIMENT_PARAMS = {**DEFAULT_SPREAD_PARAMS}
EXPERIMENT_HYPOTHESIS = (
    "Baseline spread regression with all 17 features, "
    "XGBRegressor(reg:squarederror), lr=0.1, n_estimators=300, "
    "early_stopping_rounds=20 (mirrors classifier Exp 5 hyperparams)"
)
DROP_FEATURES: list[str] = []


def run_spread_experiment():
    """Orchestrate a single spread regression experiment.

    Reads configuration from module-level variables:
        EXPERIMENT_ID, EXPERIMENT_PARAMS, EXPERIMENT_HYPOTHESIS, DROP_FEATURES

    Returns:
        Tuple of (results_dict, model, keep_decision) for caller inspection.
    """
    from features.build import build_game_features

    # Load and build features
    print(f"\n{'='*60}")
    print(f"SPREAD EXPERIMENT {EXPERIMENT_ID}: {EXPERIMENT_HYPOTHESIS}")
    print(f"{'='*60}\n")

    df = build_game_features()

    # JOIN with schedules to get the spread target (result column)
    # result = home_score - away_score (already exists in schedule data)
    # Load from parquet cache — no DB connection needed for training.
    print("Loading schedules from cache for spread target...")
    from data.loaders import load_schedules_cached
    from data.transforms import normalize_teams_in_df
    from data.sources import TEAM_COLUMNS_SCHEDULE

    sched_frames = []
    for season in range(2005, 2025):
        s = load_schedules_cached(season)
        s = s[s["game_type"] != "PRE"].reset_index(drop=True)
        s = normalize_teams_in_df(s, TEAM_COLUMNS_SCHEDULE)
        sched_frames.append(s)
    schedules = pd.concat(sched_frames, ignore_index=True)
    schedules = schedules[schedules["game_type"] == "REG"]

    # Merge on game_id to attach the spread target
    df = df.merge(schedules[["game_id", "result"]], on="game_id", how="left")

    # The result column is now in df — extract it as the target before splitting
    # (load_and_split_spread expects a separate target_series)
    target_series = df["result"].copy()
    df = df.drop(columns=["result"])  # Remove to avoid it being a feature

    train, val_2023, val_2022, val_2021, feature_cols = load_and_split_spread(
        df, target_series
    )

    # Apply feature drops if specified
    active_features = [c for c in feature_cols if c not in DROP_FEATURES]
    if DROP_FEATURES:
        print(f"Dropped features: {DROP_FEATURES}")
        print(
            f"Active features: {len(active_features)} (was {len(feature_cols)})"
        )

    # Prepare X/y splits
    X_train = train[active_features]
    y_train = train["spread_target"]
    X_val_2023 = val_2023[active_features]
    y_val_2023 = val_2023["spread_target"]
    X_val_2022 = val_2022[active_features]
    y_val_2022 = val_2022["spread_target"]
    X_val_2021 = val_2021[active_features]
    y_val_2021 = val_2021["spread_target"]

    # Train and evaluate
    results, model = train_and_evaluate_spread(
        X_train,
        y_train,
        X_val_2023,
        y_val_2023,
        X_val_2022,
        y_val_2022,
        X_val_2021,
        y_val_2021,
        EXPERIMENT_PARAMS,
    )

    # Compute baselines
    baselines = compute_spread_baselines(y_val_2023.values)

    # Load previous best MAE from spread_experiments.jsonl
    prev_best_mae = None
    jsonl_path = "models/spread_experiments.jsonl"
    if os.path.exists(jsonl_path):
        with open(jsonl_path) as f:
            for line in f:
                entry = json.loads(line)
                if entry["keep"]:
                    entry_mae = entry["mae_2023"]
                    if prev_best_mae is None or entry_mae < prev_best_mae:
                        prev_best_mae = entry_mae

    # Keep/revert decision for regression:
    # For experiment 1, always keep (establishing baseline)
    # For subsequent: keep if MAE improves by >= 0.1 points
    keep = False
    if EXPERIMENT_ID == 1:
        keep = True
    elif prev_best_mae is not None:
        mae_improvement = prev_best_mae - results["mae_2023"]
        if mae_improvement >= 0.1:
            keep = True

    # Save model if keeping
    model_path = None
    if keep:
        model_path = save_spread_model(model, EXPERIMENT_ID)
        save_best_spread_model(model)

    # Log experiment (always, regardless of keep/revert)
    log_spread_experiment(
        experiment_id=EXPERIMENT_ID,
        params=EXPERIMENT_PARAMS,
        features_used=active_features,
        results=results,
        baselines=baselines,
        keep=keep,
        hypothesis=EXPERIMENT_HYPOTHESIS,
        prev_best_mae=prev_best_mae,
        model_path=model_path,
        jsonl_path=jsonl_path,
    )

    # Print results
    print(f"\n{'='*60}")
    print(f"RESULTS - Spread Experiment {EXPERIMENT_ID}")
    print(f"{'='*60}")
    print(f"  2023 MAE:          {results['mae_2023']:.3f}")
    print(f"  2023 RMSE:         {results['rmse_2023']:.3f}")
    print(f"  2023 Win Accuracy: {results['derived_win_accuracy_2023']:.4f}")
    print(f"  2022 MAE:          {results['mae_2022']:.3f}")
    print(f"  2022 RMSE:         {results['rmse_2022']:.3f}")
    print(f"  2022 Win Accuracy: {results['derived_win_accuracy_2022']:.4f}")
    print(f"  2021 MAE:          {results['mae_2021']:.3f}")
    print(f"  2021 RMSE:         {results['rmse_2021']:.3f}")
    print(f"  2021 Win Accuracy: {results['derived_win_accuracy_2021']:.4f}")
    print(f"\n  --- Baselines (2023) ---")
    b25 = baselines["always_home_25"]
    b0 = baselines["always_zero"]
    print(f"  Always +2.5: MAE={b25['mae']:.3f}, Win Acc={b25['derived_win_accuracy']:.4f}")
    print(f"  Always 0:    MAE={b0['mae']:.3f}, Win Acc={b0['derived_win_accuracy']:.4f}")
    print(f"\n  --- Comparison ---")
    print(f"  Classifier Exp 5 Win Accuracy (2023): 62.89%")
    print(f"  Spread Model Win Accuracy (2023):     {results['derived_win_accuracy_2023']*100:.2f}%")
    print(f"\n  SHAP top-5:    {results['shap_top5']}")
    print(f"  Prev best MAE: {prev_best_mae}")
    print(f"  Decision:      {'KEEP' if keep else 'REVERT'}")
    if model_path:
        print(f"  Model saved:   {model_path}")
    print(f"{'='*60}\n")

    return results, model, keep


if __name__ == "__main__":
    run_spread_experiment()
