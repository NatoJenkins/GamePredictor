"""Seed spread_predictions table with historical season data.

Loads the best spread model, builds features for a season, runs regression
inference on all completed games, and stores spread predictions with actual
outcomes so the dashboard accuracy metrics have data on first deploy.

Usage:
    python -m scripts.seed_spread [--seasons 2023 2024] [--dry-run]

This is a deployment utility. It does NOT modify any model artifacts or
spread_experiments.jsonl -- it only writes to the spread_predictions table.
"""

import argparse
import sys

import numpy as np
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data.db import get_engine, get_table
from features.build import build_game_features
from models.predict import load_best_spread_model, get_best_spread_experiment


def seed_spread_predictions(season: int, dry_run: bool = False) -> int:
    """Generate and store spread predictions for all completed games in a season.

    Unlike generate_spread_predictions() in models/predict.py (which targets
    unplayed games), this function targets completed games where actual outcomes
    are known, so the dashboard can display spread accuracy stats.

    Args:
        season: Season year to generate spread predictions for.
        dry_run: If True, prints predictions without writing to database.

    Returns:
        Number of predictions generated.
    """
    print(f"Seeding spread predictions for {season} season...")

    # Step 1: Load spread model and experiment info
    model = load_best_spread_model()
    experiment_info = get_best_spread_experiment()
    if experiment_info is None:
        print("ERROR: No kept experiments found in spread_experiments.jsonl")
        sys.exit(1)

    model_id = experiment_info["experiment_id"]
    feature_names = model.get_booster().feature_names
    print(f"Loaded spread model from experiment {model_id}")
    print(f"Model expects {len(feature_names)} features")

    # Step 2: Build features for the target season
    print(f"Building features for {season} season (this may take a minute)...")
    features_df = build_game_features(seasons=[season])

    # Step 3: Filter to completed games with rolling features
    rolling_cols = [c for c in features_df.columns if c.startswith("home_rolling_")]
    completed = features_df.dropna(subset=rolling_cols).copy()

    # Also need actual outcomes -- filter to games with home_win (not ties/None)
    completed = completed.dropna(subset=["home_win"]).copy()

    print(f"Found {len(completed)} completed games with features")

    if completed.empty:
        print("No completed games found. Nothing to seed.")
        return 0

    # Step 4: Build feature matrix and run REGRESSION inference (NOT predict_proba)
    X = completed[feature_names]
    predicted_spreads = model.predict(X)  # Regression: continuous spread values

    # Step 5: Get schedule data for game dates and actual scores
    engine = get_engine()

    schedule_query = """
        SELECT game_id, gameday, home_score, away_score
        FROM schedules
        WHERE season = %(season)s AND game_type = 'REG'
    """
    schedule_info = pd.read_sql(schedule_query, engine, params={"season": season})
    schedule_map = {
        row["game_id"]: row for _, row in schedule_info.iterrows()
    }

    # Step 6: Build prediction records with BOTH predicted and actual columns
    records = []
    correct_count = 0

    for i, (_, game) in enumerate(completed.iterrows()):
        predicted_spread = float(predicted_spreads[i])
        home_team = str(game["home_team"])
        away_team = str(game["away_team"])

        # Home-team convention: spread >= 0 means home wins
        predicted_winner = home_team if predicted_spread >= 0 else away_team

        # Get schedule info for actual scores
        sched = schedule_map.get(game["game_id"])
        game_date = None
        actual_spread = None
        actual_winner = None

        if sched is not None:
            if pd.notna(sched["gameday"]):
                game_date = str(sched["gameday"])

            if pd.notna(sched["home_score"]) and pd.notna(sched["away_score"]):
                # actual_spread = home_score - away_score (matching prediction convention)
                actual_spread = float(sched["home_score"] - sched["away_score"])
                # For actual_spread == 0 (ties), set actual_winner to home_team
                actual_winner = home_team if actual_spread >= 0 else away_team

        correct = (predicted_winner == actual_winner) if actual_winner is not None else None

        record = {
            "game_id": str(game["game_id"]),
            "season": int(game["season"]),
            "week": int(game["week"]),
            "game_date": game_date,
            "home_team": home_team,
            "away_team": away_team,
            "predicted_spread": predicted_spread,
            "predicted_winner": predicted_winner,
            "model_id": model_id,
            "actual_spread": actual_spread,
            "actual_winner": actual_winner,
            "correct": correct,
        }
        records.append(record)
        if correct:
            correct_count += 1

    total = len(records)
    accuracy = correct_count / total if total > 0 else 0.0
    print(f"\nSpread predictions generated: {total}")
    print(f"Correct: {correct_count}/{total} ({accuracy * 100:.1f}%)")

    if dry_run:
        print("\n[DRY RUN] No data written to database.")
        print("\nSample predictions:")
        for r in records[:5]:
            status = "CORRECT" if r["correct"] else "WRONG"
            print(
                f"  Week {r['week']:2d}: {r['away_team']} @ {r['home_team']} "
                f"-> spread {r['predicted_spread']:+.1f} ({r['predicted_winner']}) [{status}]"
            )
        return total

    # Step 7: Upsert into spread_predictions table
    print("\nWriting to spread_predictions table...")
    spread_table = get_table("spread_predictions", engine)

    # Upsert in chunks
    chunk_size = 100
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = pg_insert(spread_table).values(chunk)
        update_columns = {
            col: stmt.excluded[col]
            for col in [
                "season", "week", "game_date", "home_team", "away_team",
                "predicted_spread", "predicted_winner", "model_id",
                "actual_spread", "actual_winner", "correct",
            ]
        }
        upsert = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_=update_columns,
        )
        with engine.begin() as conn:
            conn.execute(upsert)

    print(f"Successfully seeded {total} spread predictions for {season} season.")
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Seed spread_predictions table with completed season data for dashboard."
    )
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=[2023, 2024],
        help="Season years to seed spread predictions for (default: 2023 2024)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print predictions without writing to database",
    )
    args = parser.parse_args()

    total = 0
    for season in args.seasons:
        total += seed_spread_predictions(season=season, dry_run=args.dry_run)
    print(f"\nTotal: seeded {total} spread predictions across {len(args.seasons)} season(s)")


if __name__ == "__main__":
    main()
