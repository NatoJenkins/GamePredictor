"""Feature build pipeline: aggregate -> roll -> pivot -> store.

WARNING: Do NOT modify during autoresearch experiment loop (CLAUDE.md).
Only models/train.py may be modified during experiments.
"""
import pandas as pd
import numpy as np
from features.definitions import (
    ROLLING_FEATURES,
    SITUATIONAL_FEATURES,
    TARGET,
    FORBIDDEN_FEATURES,
    EPA_PLAY_TYPES,
)


def aggregate_game_stats(pbp: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    """Stage 1: Compute per-team, per-game statistics from PBP + schedule.

    Returns a team game log with one row per (game_id, team) containing:
    - off_epa_per_play: mean EPA on plays where team is posteam (pass/run only)
    - def_epa_per_play: mean EPA on plays where team is defteam (pass/run only)
    - point_diff: points scored - points allowed
    - turnovers_committed: interceptions thrown + fumbles lost
    - turnovers_forced: turnovers committed by opponent in same game
    - turnover_diff: turnovers_forced - turnovers_committed
    - win: 1.0 if won, 0.0 if lost, 0.5 if tie
    """
    # --- EPA aggregation (pass/run plays only) ---
    real_plays = pbp[pbp["play_type"].isin(EPA_PLAY_TYPES)]

    off_epa = (
        real_plays.groupby(["game_id", "posteam"])["epa"]
        .mean()
        .reset_index()
        .rename(columns={"posteam": "team", "epa": "off_epa_per_play"})
    )

    def_epa = (
        real_plays.groupby(["game_id", "defteam"])["epa"]
        .mean()
        .reset_index()
        .rename(columns={"defteam": "team", "epa": "def_epa_per_play"})
    )

    # --- Turnovers (all plays with a posteam, not just pass/run) ---
    plays_with_team = pbp[pbp["posteam"].notna()]
    turnovers_by_team = (
        plays_with_team.groupby(["game_id", "posteam"])
        .agg(turnovers_committed=("interception", "sum"),
             fumbles_lost_count=("fumble_lost", "sum"))
        .reset_index()
    )
    turnovers_by_team["turnovers_committed"] = (
        turnovers_by_team["turnovers_committed"] + turnovers_by_team["fumbles_lost_count"]
    )
    turnovers_by_team = turnovers_by_team.drop(columns=["fumbles_lost_count"])
    turnovers_by_team = turnovers_by_team.rename(columns={"posteam": "team"})

    # --- Build team game log from schedule (home + away perspectives) ---
    reg_schedule = schedule[schedule["game_type"] == "REG"].copy()
    reg_schedule["gameday"] = pd.to_datetime(reg_schedule["gameday"])

    # Home perspective
    home = reg_schedule[["game_id", "season", "week", "gameday",
                         "home_team", "away_team", "home_score", "away_score", "result"]].copy()
    home["team"] = home["home_team"]
    home["opponent"] = home["away_team"]
    home["points_for"] = home["home_score"]
    home["points_against"] = home["away_score"]
    home["point_diff"] = home["result"].astype(float)
    home["win"] = home["result"].apply(lambda x: 1.0 if x > 0 else (0.5 if x == 0 else 0.0))

    # Away perspective
    away = reg_schedule[["game_id", "season", "week", "gameday",
                         "home_team", "away_team", "home_score", "away_score", "result"]].copy()
    away["team"] = away["away_team"]
    away["opponent"] = away["home_team"]
    away["points_for"] = away["away_score"]
    away["points_against"] = away["home_score"]
    away["point_diff"] = -away["result"].astype(float)
    away["win"] = away["result"].apply(lambda x: 0.0 if x > 0 else (0.5 if x == 0 else 1.0))

    keep_cols = ["game_id", "season", "week", "gameday", "team", "opponent", "point_diff", "win"]
    team_log = pd.concat([home[keep_cols], away[keep_cols]], ignore_index=True)

    # --- Merge EPA and turnovers onto team log ---
    team_log = team_log.merge(off_epa, on=["game_id", "team"], how="left")
    team_log = team_log.merge(def_epa, on=["game_id", "team"], how="left")
    team_log = team_log.merge(turnovers_by_team, on=["game_id", "team"], how="left")

    # Turnovers forced = opponent's turnovers committed in same game
    opp_turnovers = turnovers_by_team.rename(
        columns={"team": "opponent", "turnovers_committed": "turnovers_forced"}
    )
    team_log = team_log.merge(
        opp_turnovers[["game_id", "opponent", "turnovers_forced"]],
        on=["game_id", "opponent"],
        how="left",
    )

    # Fill missing turnovers with 0 (games with no turnovers)
    team_log["turnovers_committed"] = team_log["turnovers_committed"].fillna(0)
    team_log["turnovers_forced"] = team_log["turnovers_forced"].fillna(0)
    team_log["turnover_diff"] = team_log["turnovers_forced"] - team_log["turnovers_committed"]

    # Sort for rolling computation
    team_log = team_log.sort_values(["team", "season", "gameday", "week"]).reset_index(drop=True)

    return team_log


def compute_rolling_features(team_log: pd.DataFrame) -> pd.DataFrame:
    """Stage 2: Compute rolling features with shift(1) per team per season.

    CRITICAL: All rolling features use .shift(1) -- no exceptions (CLAUDE.md).
    Rolling resets at season boundaries (groupby team AND season).
    Week 1 of each season will have NaN -- this is correct.
    """
    result = team_log.copy()

    rolling_cols = [
        "off_epa_per_play",
        "def_epa_per_play",
        "point_diff",
        "turnovers_committed",
        "turnovers_forced",
        "turnover_diff",
        "win",
    ]

    for col in rolling_cols:
        result[f"rolling_{col}"] = (
            result.groupby(["team", "season"])[col]
            .transform(lambda x: x.shift(1).expanding().mean())
        )

    return result


def build_home_perspective(
    schedule: pd.DataFrame,
    rolling_features: pd.DataFrame,
) -> pd.DataFrame:
    """Stage 3: Pivot per-team rolling features into home-perspective rows.

    Each row = one regular-season game with:
    - home_rolling_* columns from the home team's rolling stats
    - away_rolling_* columns from the away team's rolling stats
    - Situational features from schedule
    - Target: home_win (1=home win, 0=away win, None=tie)
    """
    reg_schedule = schedule[schedule["game_type"] == "REG"].copy()
    reg_schedule["gameday"] = pd.to_datetime(reg_schedule["gameday"])

    rolling_cols = [c for c in rolling_features.columns if c.startswith("rolling_")]

    # Home team features
    home_rolling = rolling_features[["game_id", "team"] + rolling_cols].copy()
    home_rename = {c: f"home_{c}" for c in rolling_cols}
    home_rename["team"] = "home_team"
    home_rolling = home_rolling.rename(columns=home_rename)

    # Away team features
    away_rolling = rolling_features[["game_id", "team"] + rolling_cols].copy()
    away_rename = {c: f"away_{c}" for c in rolling_cols}
    away_rename["team"] = "away_team"
    away_rolling = away_rolling.rename(columns=away_rename)

    # Build game features
    game_features = reg_schedule[["game_id", "season", "week", "gameday",
                                   "home_team", "away_team", "result",
                                   "home_rest", "away_rest", "div_game"]].copy()

    # Target variable
    game_features["home_win"] = game_features["result"].apply(
        lambda x: 1 if x > 0 else (0 if x < 0 else None)
    )

    # Merge rolling features
    game_features = game_features.merge(home_rolling, on=["game_id", "home_team"], how="left")
    game_features = game_features.merge(away_rolling, on=["game_id", "away_team"], how="left")

    # Drop result (FORBIDDEN_FEATURES -- must not be in final output)
    game_features = game_features.drop(columns=["result"])

    return game_features


def build_game_features(
    seasons: list[int] | None = None,
    pbp: pd.DataFrame | None = None,
    schedule: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Main entry point: build complete feature matrix.

    Args:
        seasons: List of seasons to process. Defaults to 2005-2024.
        pbp: Pre-loaded PBP data (for testing). If None, loads from cache.
        schedule: Pre-loaded schedule data (for testing). If None, loads from cache.

    Returns:
        DataFrame with one row per regular-season game (home perspective)
        containing rolling and situational features.
    """
    if pbp is None or schedule is None:
        from data.loaders import load_pbp_cached, load_schedules_cached
        from data.transforms import normalize_teams_in_df, filter_preseason
        from data.sources import TEAM_COLUMNS_PBP, TEAM_COLUMNS_SCHEDULE

        if seasons is None:
            seasons = list(range(2005, 2025))

        pbp_frames = []
        sched_frames = []
        for season in seasons:
            p = load_pbp_cached(season)
            p = filter_preseason(p, "season_type")
            p = normalize_teams_in_df(p, TEAM_COLUMNS_PBP)
            pbp_frames.append(p)

            s = load_schedules_cached(season)
            s = s[s["game_type"] != "PRE"].reset_index(drop=True)
            s = normalize_teams_in_df(s, TEAM_COLUMNS_SCHEDULE)
            sched_frames.append(s)

        pbp = pd.concat(pbp_frames, ignore_index=True)
        schedule = pd.concat(sched_frames, ignore_index=True)

    # Stage 1: Game-level aggregation
    team_log = aggregate_game_stats(pbp, schedule)

    # Stage 2: Rolling features
    rolling = compute_rolling_features(team_log)

    # Stage 3: Home perspective pivot
    game_features = build_home_perspective(schedule, rolling)

    # Validate: no forbidden features in output
    for col in FORBIDDEN_FEATURES:
        assert col not in game_features.columns, f"Forbidden feature '{col}' found in output"

    return game_features


def store_game_features(df: pd.DataFrame) -> int:
    """Store feature matrix in PostgreSQL game_features table.

    Returns number of rows stored.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from data.db import get_engine, get_table

    engine = get_engine()
    table = get_table("game_features", engine)

    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            else:
                record[col] = val
        records.append(record)

    # Upsert in chunks
    chunk_size = 1000
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = pg_insert(table).values(chunk)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in table.columns
            if c.name != "game_id"
        }
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_=update_cols,
        )
        with engine.begin() as conn:
            conn.execute(upsert_stmt)

    return len(records)
