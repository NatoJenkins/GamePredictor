"""Baseline computation. Never modify during autoresearch experiments (only train.py is modified).

Provides two trivial baselines for comparison against trained models:
- always_home_baseline: predict the home team always wins
- better_record_baseline: predict the team with the better season record wins

Both baselines exclude tied games from evaluation. Every experiment logs
these baseline accuracies alongside model accuracy for context.
"""

import pandas as pd
import numpy as np

from features.definitions import TARGET


def _build_prior_season_records(df: pd.DataFrame) -> dict[tuple[str, int], float]:
    """Build a lookup mapping (team, season) -> team's final rolling_win from the PRIOR season.

    For each team in each season S, finds the last week's rolling_win value,
    then stores it as (team, S+1) so it can be looked up during season S+1.

    CAVEAT: rolling_win uses shift(1) + expanding mean, so the value at the
    last week of a season represents the win rate going INTO that final game,
    not including it. This means the prior-season tiebreaker is stale by one
    game (e.g., a 16-game record instead of 17). This is a known minor
    inaccuracy that does not materially affect baseline accuracy.

    Args:
        df: Full multi-season feature DataFrame from build_game_features().

    Returns:
        Dict mapping (team_abbr, season) -> prior-season final rolling_win.
        The season in the key is the season where this record would be USED
        (i.e., season + 1 relative to when the record was earned).
    """
    records: dict[tuple[str, int], float] = {}

    # Home perspective: for each (season, home_team), find max-week row's rolling_win
    home_groups = df.dropna(subset=["home_rolling_win"]).groupby(["season", "home_team"])
    for (season, team), group in home_groups:
        max_week_idx = group["week"].idxmax()
        rolling_win = group.loc[max_week_idx, "home_rolling_win"]
        if not np.isnan(rolling_win):
            records[(team, season + 1)] = rolling_win

    # Away perspective: for each (season, away_team), find max-week row's rolling_win
    away_groups = df.dropna(subset=["away_rolling_win"]).groupby(["season", "away_team"])
    for (season, team), group in away_groups:
        max_week_idx = group["week"].idxmax()
        rolling_win = group.loc[max_week_idx, "away_rolling_win"]
        if not np.isnan(rolling_win):
            # Only set if not already set from home perspective (should be consistent)
            if (team, season + 1) not in records:
                records[(team, season + 1)] = rolling_win

    return records


def always_home_baseline(df: pd.DataFrame) -> float:
    """Compute accuracy of always predicting the home team wins.

    Excludes tied games (home_win is NaN) from evaluation.

    Args:
        df: Feature DataFrame for the season(s) to evaluate.

    Returns:
        Accuracy as a float between 0.0 and 1.0.
    """
    valid = df[df[TARGET].notna()]
    return valid[TARGET].mean()


def better_record_baseline(df: pd.DataFrame, season: int) -> float:
    """Compute accuracy of predicting the team with the better season record wins.

    Accepts the FULL multi-season DataFrame so it can look up prior-season
    records for tiebreaking. Evaluates only games from the specified season.

    Tiebreaker logic (per CONTEXT.md decision):
    - If home_rolling_win > away_rolling_win -> predict home win
    - If away_rolling_win > home_rolling_win -> predict away win
    - If tied: use prior-season record as tiebreaker
    - If no prior-season data: fall back to predicting home team wins

    Excludes:
    - Tied games (home_win is NaN)
    - Games with NaN rolling_win (Week 1 of each season)

    Args:
        df: Full multi-season feature DataFrame.
        season: Target season to evaluate.

    Returns:
        Accuracy as a float between 0.0 and 1.0.
    """
    # Step 1: Build prior-season lookup
    prior_records = _build_prior_season_records(df)

    # Step 2: Filter to target season
    season_df = df[df["season"] == season].copy()

    # Step 3: Exclude ties
    season_df = season_df[season_df[TARGET].notna()]

    # Step 4: Exclude rows with NaN rolling_win (need records to compare)
    season_df = season_df[
        season_df["home_rolling_win"].notna() & season_df["away_rolling_win"].notna()
    ]

    if len(season_df) == 0:
        return 0.0

    # Step 5: Generate predictions
    predictions = []
    for _, row in season_df.iterrows():
        home_win_rate = row["home_rolling_win"]
        away_win_rate = row["away_rolling_win"]

        if home_win_rate > away_win_rate:
            predictions.append(1)  # predict home win
        elif away_win_rate > home_win_rate:
            predictions.append(0)  # predict away win
        else:
            # Tied records -- use prior-season tiebreaker
            prior_home = prior_records.get((row["home_team"], season))
            prior_away = prior_records.get((row["away_team"], season))

            if prior_home is not None and prior_away is not None:
                # Both have prior records: predict the one with higher prior win rate
                if prior_home >= prior_away:
                    predictions.append(1)
                else:
                    predictions.append(0)
            elif prior_home is not None:
                # Only home has prior record
                predictions.append(1)
            elif prior_away is not None:
                # Only away has prior record
                predictions.append(0)
            else:
                # No prior data -- fall back to home team
                predictions.append(1)

    # Step 6: Compute accuracy
    actuals = season_df[TARGET].values
    predictions_arr = np.array(predictions)
    accuracy = (predictions_arr == actuals).mean()

    return float(accuracy)


def compute_baselines(df: pd.DataFrame, season: int) -> dict:
    """Compute both baselines for a given season.

    Args:
        df: Full multi-season feature DataFrame.
        season: Target season to evaluate.

    Returns:
        Dict with keys:
        - season: the evaluation season
        - always_home_accuracy: accuracy of always-home baseline
        - better_record_accuracy: accuracy of better-record baseline
        - always_home_game_count: number of non-tie games evaluated by always_home
        - better_record_game_count: number of non-tie, non-NaN-rolling games
          evaluated by better_record
    """
    season_df = df[df["season"] == season]

    # Always-home: evaluates all non-tie games
    ah_df = season_df[season_df[TARGET].notna()]
    ah_accuracy = always_home_baseline(season_df)

    # Better-record: evaluates non-tie games with non-NaN rolling_win
    br_df = season_df[
        season_df[TARGET].notna()
        & season_df["home_rolling_win"].notna()
        & season_df["away_rolling_win"].notna()
    ]
    br_accuracy = better_record_baseline(df, season)

    return {
        "season": season,
        "always_home_accuracy": ah_accuracy,
        "better_record_accuracy": br_accuracy,
        "always_home_game_count": len(ah_df),
        "better_record_game_count": len(br_df),
    }
