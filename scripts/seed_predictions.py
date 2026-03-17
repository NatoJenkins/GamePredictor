"""Seed predictions table with 2023 validation season data for dashboard development.

Loads the best model, builds features for the 2023 season, runs inference on
all completed games, and stores predictions with actual outcomes so the
Accuracy and History dashboard pages have data to display.

Usage:
    python -m scripts.seed_predictions [--season 2023] [--dry-run]

This is a development utility. It does NOT modify any model artifacts or
experiments.jsonl -- it only writes to the predictions table.
"""

import argparse
import sys

import numpy as np
import pandas as pd

from api.config import get_confidence_tier
from data.db import get_engine, get_table
from features.build import build_game_features
from models.predict import load_best_model, get_best_experiment


def seed_predictions(season: int = 2023, dry_run: bool = False) -> int:
    """Generate and store predictions for all completed games in a season.

    Unlike generate_predictions() in models/predict.py (which targets unplayed
    games), this function targets completed games where actual outcomes are
    known, so the dashboard can display accuracy stats.

    Args:
        season: Season year to generate predictions for. Defaults to 2023
            (the validation season).
        dry_run: If True, prints predictions without writing to database.

    Returns:
        Number of predictions generated.
    """
    print(f"Seeding predictions for {season} season...")

    # Step 1: Load model and experiment info
    model = load_best_model()
    experiment_info = get_best_experiment()
    if experiment_info is None:
        print("ERROR: No kept experiments found in experiments.jsonl")
        sys.exit(1)

    model_id = experiment_info["experiment_id"]
    feature_names = model.get_booster().feature_names
    print(f"Loaded model from experiment {model_id}")
    print(f"Model expects {len(feature_names)} features")

    # Step 2: Build features for the target season
    # We need rolling features from completed games, so include the full season
    print(f"Building features for {season} season (this may take a minute)...")
    features_df = build_game_features(seasons=[season])

    # Step 3: Filter to completed games only (have rolling features)
    rolling_cols = [c for c in features_df.columns if c.startswith("home_rolling_")]
    completed = features_df.dropna(subset=rolling_cols).copy()

    # Also need actual outcomes -- filter to games with home_win (not ties/None)
    completed = completed.dropna(subset=["home_win"]).copy()

    print(f"Found {len(completed)} completed games with features")

    if completed.empty:
        print("No completed games found. Nothing to seed.")
        return 0

    # Step 4: Build feature matrix and run inference
    X = completed[feature_names]
    proba = model.predict_proba(X)[:, 1]  # P(home_win)

    # Step 5: Build prediction records with actual outcomes
    engine = get_engine()

    # Get schedule data for game dates
    schedule_query = """
        SELECT game_id, gameday, home_score, away_score
        FROM schedules
        WHERE season = %(season)s AND game_type = 'REG'
    """
    schedule_info = pd.read_sql(schedule_query, engine, params={"season": season})
    schedule_map = {
        row["game_id"]: row for _, row in schedule_info.iterrows()
    }

    records = []
    correct_count = 0

    for i, (_, game) in enumerate(completed.iterrows()):
        home_prob = float(proba[i])

        if home_prob >= 0.5:
            predicted_winner = game["home_team"]
            confidence = home_prob
        else:
            predicted_winner = game["away_team"]
            confidence = 1.0 - home_prob

        # Determine actual winner from home_win target
        home_win = game["home_win"]
        if home_win == 1:
            actual_winner = game["home_team"]
        else:
            actual_winner = game["away_team"]

        is_correct = predicted_winner == actual_winner

        # Get game date from schedule
        sched = schedule_map.get(game["game_id"])
        game_date = None
        if sched is not None and pd.notna(sched["gameday"]):
            game_date = str(sched["gameday"])

        record = {
            "game_id": str(game["game_id"]),
            "season": int(game["season"]),
            "week": int(game["week"]),
            "game_date": game_date,
            "home_team": str(game["home_team"]),
            "away_team": str(game["away_team"]),
            "predicted_winner": str(predicted_winner),
            "confidence": float(confidence),
            "confidence_tier": get_confidence_tier(confidence),
            "model_id": model_id,
            "actual_winner": str(actual_winner),
            "correct": is_correct,
        }
        records.append(record)
        if is_correct:
            correct_count += 1

    total = len(records)
    accuracy = correct_count / total if total > 0 else 0.0
    print(f"\nPredictions generated: {total}")
    print(f"Correct: {correct_count}/{total} ({accuracy * 100:.1f}%)")

    if dry_run:
        print("\n[DRY RUN] No data written to database.")
        print("\nSample predictions:")
        for r in records[:5]:
            status = "CORRECT" if r["correct"] else "WRONG"
            print(
                f"  Week {r['week']:2d}: {r['away_team']} @ {r['home_team']} "
                f"-> {r['predicted_winner']} ({r['confidence']*100:.1f}%) [{status}]"
            )
        return total

    # Step 6: Upsert into predictions table
    print("\nWriting to predictions table...")
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    predictions_table = get_table("predictions", engine)

    # Upsert in chunks
    chunk_size = 100
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = pg_insert(predictions_table).values(chunk)
        update_columns = {
            col: stmt.excluded[col]
            for col in [
                "season", "week", "game_date", "home_team", "away_team",
                "predicted_winner", "confidence", "confidence_tier",
                "model_id", "actual_winner", "correct",
            ]
        }
        upsert = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_=update_columns,
        )
        with engine.begin() as conn:
            conn.execute(upsert)

    print(f"Successfully seeded {total} predictions for {season} season.")
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Seed predictions table with completed season data for dashboard development."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2023,
        help="Season year to seed predictions for (default: 2023)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print predictions without writing to database",
    )
    args = parser.parse_args()

    seed_predictions(season=args.season, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
