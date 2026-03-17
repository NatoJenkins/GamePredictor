"""Training pipeline with temporal split, dual logging, TreeSHAP, and multi-season evaluation.

This is the ONLY file modified during the autoresearch experiment loop (CLAUDE.md).
Every experiment logs to both experiments.jsonl (append-only) and MLflow (local tracking).

Functions:
    setup_mlflow: Configure local file-based MLflow tracking.
    load_and_split: Temporal split with tie/NaN exclusion.
    train_and_evaluate: Train XGBoost + evaluate on 2021/2022/2023 + TreeSHAP top-5.
    log_experiment: Dual logging to experiments.jsonl and MLflow.
    save_model: Save model artifact by experiment ID.
    save_best_model: Overwrite best model checkpoint.
    should_keep: Compound keep/revert decision logic.
"""

import json
import os
from datetime import datetime, timezone

import mlflow
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from xgboost import XGBClassifier

from features.definitions import FORBIDDEN_FEATURES, TARGET

# Metadata columns that are NOT model features
META_COLS = ["game_id", "season", "week", "gameday", "home_team", "away_team"]


def setup_mlflow():
    """Configure MLflow for local file-based tracking.

    Uses ./mlruns directory (auto-created). No server needed.
    Run `mlflow ui` ad-hoc to visualize at http://127.0.0.1:5000.
    """
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("nfl-game-predictor")


def load_and_split(df: pd.DataFrame) -> tuple:
    """Split feature matrix by season with tie and NaN exclusion.

    Temporal split (CLAUDE.md: hardcoded, never shuffle):
        - train: 2005-2022 (ALL seasons, including 2021 and 2022)
        - val_2023: 2023 (held-out validation -- used for keep/revert decisions)
        - val_2022: 2022 subset of training data (in-sample evaluation)
        - val_2021: 2021 subset of training data (in-sample evaluation)

    IMPORTANT: val_2022 and val_2021 are IN-SAMPLE subsets. They remain in the
    training set (the model trains on ALL of 2005-2022). These subsets are
    evaluated AFTER training to detect overfitting: if in-sample accuracy drops
    while out-of-sample 2023 accuracy improves, something is wrong. Only 2023
    is true held-out validation.

    Holdout 2024 is NEVER touched.

    Args:
        df: Feature DataFrame from build_game_features().

    Returns:
        Tuple of (train, val_2023, val_2022, val_2021, feature_cols).
    """
    # Feature columns = everything except meta columns and target
    feature_cols = [c for c in df.columns if c not in META_COLS + [TARGET]]

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

    # Drop ties (home_win is NaN for ties)
    train = train.dropna(subset=[TARGET])
    val_2023 = val_2023.dropna(subset=[TARGET])
    val_2022 = val_2022.dropna(subset=[TARGET])
    val_2021 = val_2021.dropna(subset=[TARGET])

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


def train_and_evaluate(
    X_train,
    y_train,
    X_val_2023,
    y_val_2023,
    X_val_2022,
    y_val_2022,
    X_val_2021,
    y_val_2021,
    params: dict,
) -> tuple[dict, XGBClassifier]:
    """Train XGBoost and evaluate on all validation/evaluation sets.

    Args:
        X_train, y_train: Training features and labels (2005-2022).
        X_val_2023, y_val_2023: Held-out 2023 validation set.
        X_val_2022, y_val_2022: In-sample 2022 evaluation set.
        X_val_2021, y_val_2021: In-sample 2021 evaluation set.
        params: XGBoost hyperparameters (passed to XGBClassifier).

    Returns:
        Tuple of (results_dict, model) where results_dict has keys:
            val_accuracy_2023, val_accuracy_2022, val_accuracy_2021,
            log_loss, brier_score, shap_top5.
    """
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        use_label_encoder=False,
        **params,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val_2023, y_val_2023)],
        verbose=False,
    )

    # 2023 predictions and probabilities (held-out validation)
    pred_2023 = model.predict(X_val_2023)
    prob_2023 = model.predict_proba(X_val_2023)[:, 1]

    # 2022 and 2021 predictions (in-sample evaluation)
    pred_2022 = model.predict(X_val_2022)
    pred_2021 = model.predict(X_val_2021)

    results = {
        "val_accuracy_2023": accuracy_score(y_val_2023, pred_2023),
        "val_accuracy_2022": accuracy_score(y_val_2022, pred_2022),
        "val_accuracy_2021": accuracy_score(y_val_2021, pred_2021),
        "log_loss": log_loss(y_val_2023, prob_2023),
        "brier_score": brier_score_loss(y_val_2023, prob_2023),
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


def log_experiment(
    experiment_id: int,
    params: dict,
    features_used: list[str],
    val_acc_2023: float,
    val_acc_2022: float,
    val_acc_2021: float,
    baseline_home: float,
    baseline_record: float,
    log_loss_val: float,
    brier_score_val: float,
    shap_top5: list[tuple[str, float]],
    keep: bool,
    hypothesis: str,
    prev_best_acc: float,
    model_path: str | None,
    jsonl_path: str = "models/experiments.jsonl",
):
    """Log experiment to both experiments.jsonl and MLflow.

    Args:
        experiment_id: Sequential experiment number.
        params: XGBoost hyperparameters used.
        features_used: List of feature column names.
        val_acc_2023: Held-out 2023 validation accuracy.
        val_acc_2022: In-sample 2022 evaluation accuracy.
        val_acc_2021: In-sample 2021 evaluation accuracy.
        baseline_home: Always-home baseline accuracy.
        baseline_record: Better-record baseline accuracy.
        log_loss_val: Log loss on 2023 validation set.
        brier_score_val: Brier score on 2023 validation set.
        shap_top5: List of (feature_name, importance) tuples.
        keep: Whether experiment was kept (True) or reverted (False).
        hypothesis: What was being tested.
        prev_best_acc: Previous best 2023 accuracy before this experiment.
        model_path: Path to saved model artifact (None if reverted).
        jsonl_path: Path to JSONL log file (default: models/experiments.jsonl).
            Tests pass tmp_path to avoid writing to real project files.
    """
    entry = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "params": params,
        "features": features_used,
        "val_accuracy_2023": val_acc_2023,
        "val_accuracy_2022": val_acc_2022,
        "val_accuracy_2021": val_acc_2021,
        "baseline_always_home": baseline_home,
        "baseline_better_record": baseline_record,
        "log_loss": log_loss_val,
        "brier_score": brier_score_val,
        "shap_top5": [
            {"feature": f, "importance": round(v, 4)} for f, v in shap_top5
        ],
        "keep": keep,
        "hypothesis": hypothesis,
        "prev_best_acc": prev_best_acc,
        "model_path": model_path,
    }

    # Append to JSONL (append-only, CLAUDE.md rule)
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Log to MLflow
    with mlflow.start_run(run_name=f"exp-{experiment_id:03d}"):
        mlflow.log_params(params)
        mlflow.log_metrics(
            {
                "val_accuracy_2023": val_acc_2023,
                "val_accuracy_2022": val_acc_2022,
                "val_accuracy_2021": val_acc_2021,
                "log_loss": log_loss_val,
                "brier_score": brier_score_val,
                "baseline_always_home": baseline_home,
                "baseline_better_record": baseline_record,
            }
        )
        mlflow.set_tag("keep", str(keep))
        mlflow.set_tag("hypothesis", hypothesis)
        if model_path:
            mlflow.log_artifact(model_path)


def save_model(
    model: XGBClassifier,
    experiment_id: int,
    artifacts_dir: str = "models/artifacts",
) -> str:
    """Save model using XGBoost native JSON format.

    Args:
        model: Trained XGBClassifier.
        experiment_id: Experiment number for filename.
        artifacts_dir: Directory for model artifacts.

    Returns:
        Path to saved model file.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(artifacts_dir, f"model_exp{experiment_id:03d}.json")
    model.save_model(path)
    return path


def save_best_model(
    model: XGBClassifier,
    artifacts_dir: str = "models/artifacts",
) -> str:
    """Overwrite the best model checkpoint.

    Args:
        model: Trained XGBClassifier (current best).
        artifacts_dir: Directory for model artifacts.

    Returns:
        Path to saved best model file.
    """
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(artifacts_dir, "best_model.json")
    model.save_model(path)
    return path


def should_keep(
    new_acc: float,
    prev_best_acc: float,
    new_log_loss: float,
    prev_best_log_loss: float,
) -> bool:
    """Compound keep/revert decision rule from CONTEXT.md.

    Keep if:
        (a) accuracy improves by >= 0.5 percentage points (>= 0.005), OR
        (b) accuracy improves by any amount AND log_loss also improves

    Otherwise revert. This prevents random-walking through noise on the
    272-game 2023 validation set.

    Args:
        new_acc: New experiment's 2023 validation accuracy.
        prev_best_acc: Previous best 2023 validation accuracy.
        new_log_loss: New experiment's 2023 validation log loss.
        prev_best_log_loss: Previous best 2023 validation log loss.

    Returns:
        True if experiment should be kept, False to revert.
    """
    acc_improvement = new_acc - prev_best_acc

    # Rule (a): Large accuracy improvement
    if acc_improvement >= 0.005:
        return True

    # Rule (b): Any accuracy improvement + log_loss improvement
    if acc_improvement > 0 and new_log_loss < prev_best_log_loss:
        return True

    return False
