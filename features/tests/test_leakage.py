"""Leakage validation tests for the feature pipeline.

These tests MUST pass before any model training proceeds (CLAUDE.md).
They verify that no feature for game G uses data from game G or later.
"""
import pandas as pd
import numpy as np
import pytest
from features.build import (
    aggregate_game_stats,
    compute_rolling_features,
    build_game_features,
)
from features.definitions import ROLLING_FEATURES, FORBIDDEN_FEATURES


def _make_spike_data():
    """Create synthetic data where the LAST game has an extreme EPA spike (100.0).

    If any prior game's rolling features contain 100.0, leakage exists.
    Team TST plays 4 games: EPA of 0.2, 0.3, 0.1, then 100.0 (spike).
    """
    # Schedule: 4 games for team TST (home for all)
    schedule = pd.DataFrame({
        "game_id": [f"2023_0{w}_OPP{w}_TST" for w in range(1, 5)],
        "season": [2023] * 4,
        "game_type": ["REG"] * 4,
        "week": [1, 2, 3, 4],
        "gameday": ["2023-09-10", "2023-09-17", "2023-09-24", "2023-10-01"],
        "weekday": ["Sunday"] * 4,
        "gametime": ["13:00"] * 4,
        "away_team": ["AA1", "AA2", "AA3", "AA4"],
        "away_score": [10, 10, 10, 10],
        "home_team": ["TST"] * 4,
        "home_score": [20, 20, 20, 20],
        "location": ["Home"] * 4,
        "result": [10, 10, 10, 10],
        "total": [30, 30, 30, 30],
        "overtime": [0, 0, 0, 0],
        "away_rest": [7, 7, 7, 7],
        "home_rest": [7, 7, 7, 7],
        "div_game": [0, 0, 0, 0],
        "roof": ["outdoors"] * 4,
        "surface": ["grass"] * 4,
    })

    # PBP: controlled EPA values per game
    epa_values = [0.2, 0.3, 0.1, 100.0]  # Game 4 = SPIKE
    rows = []
    play_id = 1
    for g_idx in range(4):
        game_id = schedule.iloc[g_idx]["game_id"]
        week = g_idx + 1
        for team_role in ["home", "away"]:
            team = "TST" if team_role == "home" else f"AA{week}"
            opp = f"AA{week}" if team_role == "home" else "TST"
            epa = epa_values[g_idx] if team == "TST" else -0.1
            for i in range(5):
                rows.append({
                    "play_id": play_id,
                    "game_id": game_id,
                    "season": 2023,
                    "season_type": "REG",
                    "week": week,
                    "game_date": schedule.iloc[g_idx]["gameday"],
                    "home_team": "TST",
                    "away_team": f"AA{week}",
                    "posteam": team,
                    "posteam_type": team_role,
                    "defteam": opp,
                    "down": 1,
                    "ydstogo": 10,
                    "yardline_100": 50,
                    "quarter_seconds_remaining": 900,
                    "half_seconds_remaining": 1800,
                    "game_seconds_remaining": 3600,
                    "game_half": "Half1",
                    "play_type": "pass" if i < 3 else "run",
                    "yards_gained": 5,
                    "rush_attempt": 0 if i < 3 else 1,
                    "pass_attempt": 1 if i < 3 else 0,
                    "complete_pass": 1 if i < 2 else 0,
                    "incomplete_pass": 0,
                    "interception": 0,
                    "fumble_lost": 0,
                    "sack": 0,
                    "touchdown": 0,
                    "safety": 0,
                    "epa": epa,
                    "wp": 0.5,
                    "wpa": 0.01,
                    "score_differential": 0,
                    "posteam_score": 0,
                    "defteam_score": 0,
                    "total_home_score": 0,
                    "total_away_score": 0,
                    "location": "Home",
                })
                play_id += 1
    pbp = pd.DataFrame(rows)
    return pbp, schedule


class TestLeakagePrevention:
    """Tests that verify no future data leaks into current game features."""

    def test_shift1_excludes_current_game(self):
        """Verify rolling features for game G do NOT include game G's data.

        Strategy: Plant a spike (EPA=100.0) in game 4. If any rolling
        feature for games 1-3 reflects this value, leakage exists.
        """
        pbp, schedule = _make_spike_data()
        team_log = aggregate_game_stats(pbp, schedule)
        rolling = compute_rolling_features(team_log)

        # Get TST's rolling features for games BEFORE the spike (games 1-3)
        tst_rows = rolling[rolling["team"] == "TST"].sort_values("week")
        pre_spike = tst_rows[tst_rows["week"] < 4]

        for col in [c for c in rolling.columns if c.startswith("rolling_")]:
            values = pre_spike[col].dropna().values
            for val in values:
                assert abs(val) < 50.0, (
                    f"Leakage detected: {col} for TST pre-spike game "
                    f"contains value {val} (spike was 100.0)"
                )

    def test_spike_only_visible_after_game(self):
        """The spike from game 4 should ONLY appear in game 5+'s rolling (if it existed).

        Since game 4 is the last, its spike should appear in game 4's own
        stats but NOT in game 4's rolling features (which use only prior data).
        """
        pbp, schedule = _make_spike_data()
        team_log = aggregate_game_stats(pbp, schedule)
        rolling = compute_rolling_features(team_log)

        tst_game4 = rolling[(rolling["team"] == "TST") & (rolling["week"] == 4)]
        assert len(tst_game4) == 1

        # Game 4's rolling_off_epa should be mean of games 1-3: (0.2+0.3+0.1)/3 = 0.2
        rolling_epa = tst_game4["rolling_off_epa_per_play"].iloc[0]
        assert rolling_epa == pytest.approx(0.2, abs=0.01), (
            f"Game 4 rolling EPA should be ~0.2 (mean of prior 3 games), got {rolling_epa}"
        )

    def test_week1_rolling_features_are_nan(self, synthetic_pbp, synthetic_schedule):
        """Week 1 of each season should have NaN rolling features.

        Since shift(1) pushes the first observation out, and rolling resets
        at season boundaries, week 1 has no prior data.
        """
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)

        week1 = rolling[rolling["week"] == 1]
        rolling_cols = [c for c in rolling.columns if c.startswith("rolling_")]

        for col in rolling_cols:
            assert week1[col].isna().all(), (
                f"Week 1 should have NaN for {col}, got: {week1[col].values}"
            )

    def test_removing_future_game_does_not_change_past_features(
        self, synthetic_pbp, synthetic_schedule
    ):
        """Removing the last game should not change any prior game's features.

        Build features with all 4 games, then with first 3 games only.
        Features for games 1-3 must be identical in both runs.
        """
        # Full run (4 games)
        full_features = build_game_features(
            pbp=synthetic_pbp, schedule=synthetic_schedule
        )

        # Truncated run (remove game 4 from both PBP and schedule)
        game4_id = "2023_04_NYJ_KC"
        trunc_pbp = synthetic_pbp[synthetic_pbp["game_id"] != game4_id]
        trunc_sched = synthetic_schedule[synthetic_schedule["game_id"] != game4_id]
        trunc_features = build_game_features(pbp=trunc_pbp, schedule=trunc_sched)

        # Compare features for games 1-3
        common_games = trunc_features["game_id"].values
        full_common = full_features[full_features["game_id"].isin(common_games)].sort_values("game_id").reset_index(drop=True)
        trunc_common = trunc_features.sort_values("game_id").reset_index(drop=True)

        rolling_cols = [c for c in full_common.columns if "rolling" in c]
        for col in rolling_cols:
            for idx in range(len(full_common)):
                full_val = full_common[col].iloc[idx]
                trunc_val = trunc_common[col].iloc[idx]
                if pd.isna(full_val) and pd.isna(trunc_val):
                    continue  # Both NaN is fine
                assert full_val == pytest.approx(trunc_val, abs=1e-6), (
                    f"Feature {col} for game {full_common['game_id'].iloc[idx]} "
                    f"changed when future game removed: {full_val} vs {trunc_val}"
                )

    def test_no_forbidden_features_in_output(self, synthetic_pbp, synthetic_schedule):
        """Verify result, home_score, away_score are NOT in output columns."""
        features = build_game_features(
            pbp=synthetic_pbp, schedule=synthetic_schedule
        )
        for col in FORBIDDEN_FEATURES:
            assert col not in features.columns, (
                f"Forbidden feature '{col}' found in output columns: {list(features.columns)}"
            )

    def test_rolling_features_monotonic_information(self):
        """Each successive game's rolling features should incorporate one more data point.

        For a 4-game team: game 2 rolling = game 1 stats,
        game 3 rolling = mean(game 1, game 2),
        game 4 rolling = mean(game 1, game 2, game 3).
        """
        pbp, schedule = _make_spike_data()
        team_log = aggregate_game_stats(pbp, schedule)
        rolling = compute_rolling_features(team_log)

        tst = rolling[rolling["team"] == "TST"].sort_values("week")

        # Week 1: NaN (no prior data)
        assert pd.isna(tst.iloc[0]["rolling_off_epa_per_play"])

        # Week 2: rolling = game 1 only = 0.2
        assert tst.iloc[1]["rolling_off_epa_per_play"] == pytest.approx(0.2, abs=0.01)

        # Week 3: rolling = mean(game 1, game 2) = (0.2 + 0.3) / 2 = 0.25
        assert tst.iloc[2]["rolling_off_epa_per_play"] == pytest.approx(0.25, abs=0.01)

        # Week 4: rolling = mean(game 1, game 2, game 3) = (0.2 + 0.3 + 0.1) / 3 = 0.2
        assert tst.iloc[3]["rolling_off_epa_per_play"] == pytest.approx(0.2, abs=0.01)
