"""Unit tests for baseline computation functions.

Each test uses small, hand-crafted DataFrames for precise control
over expected values. The conftest fixture is for integration-style
tests in later plans.
"""

import pandas as pd
import numpy as np
import pytest

from models.baselines import (
    always_home_baseline,
    better_record_baseline,
    compute_baselines,
    _build_prior_season_records,
)


def _make_minimal_df(
    home_wins: list,
    home_rolling_wins: list | None = None,
    away_rolling_wins: list | None = None,
    season: int = 2023,
    home_teams: list | None = None,
    away_teams: list | None = None,
) -> pd.DataFrame:
    """Helper to build a minimal feature DataFrame for testing."""
    n = len(home_wins)
    df = pd.DataFrame({
        "game_id": [f"{season}_{i+1:02d}_AWAY_HOME" for i in range(n)],
        "season": [season] * n,
        "week": list(range(2, n + 2)),  # Start at week 2 to avoid NaN issues
        "gameday": [f"{season}-09-{10+i:02d}" for i in range(n)],
        "home_team": home_teams or ["KC"] * n,
        "away_team": away_teams or ["BUF"] * n,
        "home_win": [float(x) if x is not None else np.nan for x in home_wins],
        "home_rest": [7] * n,
        "away_rest": [7] * n,
        "div_game": [0] * n,
        "home_rolling_off_epa_per_play": [0.1] * n,
        "home_rolling_def_epa_per_play": [-0.1] * n,
        "home_rolling_point_diff": [3.0] * n,
        "home_rolling_turnovers_committed": [1.0] * n,
        "home_rolling_turnovers_forced": [1.5] * n,
        "home_rolling_turnover_diff": [0.5] * n,
        "home_rolling_win": home_rolling_wins or [0.6] * n,
        "away_rolling_off_epa_per_play": [0.05] * n,
        "away_rolling_def_epa_per_play": [-0.05] * n,
        "away_rolling_point_diff": [1.0] * n,
        "away_rolling_turnovers_committed": [1.2] * n,
        "away_rolling_turnovers_forced": [1.0] * n,
        "away_rolling_turnover_diff": [-0.2] * n,
        "away_rolling_win": away_rolling_wins or [0.4] * n,
    })
    return df


class TestAlwaysHomeBaseline:
    """Tests for always_home_baseline function."""

    def test_always_home_baseline_known_values(self):
        """Given 10 games where 6 are home wins, baseline returns 0.6."""
        home_wins = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
        df = _make_minimal_df(home_wins)
        result = always_home_baseline(df)
        assert result == pytest.approx(0.6)

    def test_always_home_baseline_excludes_ties(self):
        """Given 10 games where 1 has home_win=NaN (tie), baseline computes on 9 games only."""
        # 5 home wins, 4 away wins, 1 tie -> 5/9 = 0.5556
        home_wins = [1, 1, 1, 1, 1, 0, 0, 0, 0, None]
        df = _make_minimal_df(home_wins)
        result = always_home_baseline(df)
        assert result == pytest.approx(5 / 9)


class TestBetterRecordBaseline:
    """Tests for better_record_baseline function."""

    def test_better_record_home_higher(self):
        """When home_rolling_win > away_rolling_win, predicts home win."""
        # 5 games, all home has higher rolling_win, home actually wins all
        df = _make_minimal_df(
            home_wins=[1, 1, 1, 1, 1],
            home_rolling_wins=[0.7, 0.7, 0.7, 0.7, 0.7],
            away_rolling_wins=[0.3, 0.3, 0.3, 0.3, 0.3],
        )
        result = better_record_baseline(df, 2023)
        assert result == pytest.approx(1.0)  # all correct

    def test_better_record_away_higher(self):
        """When away_rolling_win > home_rolling_win, predicts away win."""
        # 4 games, away has higher rolling_win, away actually wins all
        df = _make_minimal_df(
            home_wins=[0, 0, 0, 0],
            home_rolling_wins=[0.3, 0.3, 0.3, 0.3],
            away_rolling_wins=[0.7, 0.7, 0.7, 0.7],
        )
        result = better_record_baseline(df, 2023)
        assert result == pytest.approx(1.0)  # all correct (predicted away, away won)

    def test_better_record_tied_uses_prior_season(self):
        """When records are tied, uses prior-season record as tiebreaker.

        Constructs a 2-season DataFrame:
        - Season 2022: KC has final rolling_win=0.75, BUF has 0.50
        - Season 2023: one tied-record game (both 0.5), home_team=KC, away_team=BUF
          KC has better prior record -> predict KC (home) wins
        """
        # Season 2022 data to establish prior records
        prior_rows = {
            "game_id": ["2022_17_BUF_KC", "2022_17_DET_BUF"],
            "season": [2022, 2022],
            "week": [17, 17],
            "gameday": ["2022-12-31", "2022-12-31"],
            "home_team": ["KC", "BUF"],
            "away_team": ["BUF", "DET"],
            "home_win": [1.0, 1.0],
            "home_rest": [7, 7],
            "away_rest": [7, 7],
            "div_game": [0, 0],
            "home_rolling_off_epa_per_play": [0.2, 0.1],
            "home_rolling_def_epa_per_play": [-0.1, -0.05],
            "home_rolling_point_diff": [5.0, 2.0],
            "home_rolling_turnovers_committed": [0.8, 1.2],
            "home_rolling_turnovers_forced": [1.5, 1.0],
            "home_rolling_turnover_diff": [0.7, -0.2],
            "home_rolling_win": [0.75, 0.50],  # KC=0.75, BUF=0.50
            "away_rolling_off_epa_per_play": [0.1, 0.05],
            "away_rolling_def_epa_per_play": [-0.05, -0.02],
            "away_rolling_point_diff": [2.0, 1.0],
            "away_rolling_turnovers_committed": [1.2, 1.5],
            "away_rolling_turnovers_forced": [1.0, 0.8],
            "away_rolling_turnover_diff": [-0.2, -0.7],
            "away_rolling_win": [0.50, 0.40],  # BUF=0.50 as away
        }
        prior_df = pd.DataFrame(prior_rows)

        # Season 2023: tied-record game
        tied_game = _make_minimal_df(
            home_wins=[1],  # KC wins (correct prediction expected)
            home_rolling_wins=[0.5],
            away_rolling_wins=[0.5],
            season=2023,
            home_teams=["KC"],
            away_teams=["BUF"],
        )

        df = pd.concat([prior_df, tied_game], ignore_index=True)

        # KC had prior 0.75 > BUF prior 0.50, so tiebreaker predicts KC (home) wins
        # KC actually won -> accuracy = 1.0
        result = better_record_baseline(df, 2023)
        assert result == pytest.approx(1.0)

    def test_better_record_tied_home_fallback_no_prior(self):
        """When records are tied and no prior season exists, falls back to home team."""
        # Only season 2005 (first in dataset) -- no prior season data
        df = _make_minimal_df(
            home_wins=[1],  # home wins
            home_rolling_wins=[0.5],
            away_rolling_wins=[0.5],
            season=2005,
        )
        result = better_record_baseline(df, 2005)
        # Falls back to predicting home team -> correct prediction -> 1.0
        assert result == pytest.approx(1.0)

    def test_better_record_excludes_nan_records(self):
        """Rows with NaN rolling_win are excluded from evaluation."""
        df = _make_minimal_df(
            home_wins=[1, 1, 0],
            home_rolling_wins=[np.nan, 0.6, 0.6],
            away_rolling_wins=[np.nan, 0.4, 0.4],
        )
        # First game excluded (NaN rolling_win)
        # Remaining 2 games: home > away -> predict home. Game 2: correct, Game 3: wrong
        # Accuracy = 1/2 = 0.5
        result = better_record_baseline(df, 2023)
        assert result == pytest.approx(0.5)


class TestBuildPriorSeasonRecords:
    """Tests for _build_prior_season_records helper."""

    def test_build_prior_season_records(self):
        """Returns correct (team, season+1) -> rolling_win mapping from multi-season data."""
        # Season 2022: KC's last-week rolling_win is 0.75
        df = pd.DataFrame({
            "game_id": ["2022_17_BUF_KC", "2022_18_SF_KC"],
            "season": [2022, 2022],
            "week": [17, 18],
            "gameday": ["2022-12-25", "2022-12-31"],
            "home_team": ["KC", "KC"],
            "away_team": ["BUF", "SF"],
            "home_win": [1.0, 1.0],
            "home_rest": [7, 7],
            "away_rest": [7, 7],
            "div_game": [0, 0],
            "home_rolling_off_epa_per_play": [0.2, 0.2],
            "home_rolling_def_epa_per_play": [-0.1, -0.1],
            "home_rolling_point_diff": [5.0, 5.0],
            "home_rolling_turnovers_committed": [0.8, 0.8],
            "home_rolling_turnovers_forced": [1.5, 1.5],
            "home_rolling_turnover_diff": [0.7, 0.7],
            "home_rolling_win": [0.70, 0.75],  # Week 18 is latest -> 0.75
            "away_rolling_off_epa_per_play": [0.1, 0.05],
            "away_rolling_def_epa_per_play": [-0.05, -0.02],
            "away_rolling_point_diff": [2.0, 1.0],
            "away_rolling_turnovers_committed": [1.2, 1.5],
            "away_rolling_turnovers_forced": [1.0, 0.8],
            "away_rolling_turnover_diff": [-0.2, -0.7],
            "away_rolling_win": [0.50, 0.40],  # BUF week 17: 0.50, SF week 18: 0.40
        })

        records = _build_prior_season_records(df)

        # KC's last week (18) has home_rolling_win=0.75 -> stored as (KC, 2023)
        assert ("KC", 2023) in records
        assert records[("KC", 2023)] == pytest.approx(0.75)

        # BUF appears as away in week 17 with rolling_win=0.50
        # SF appears as away in week 18 with rolling_win=0.40
        # But SF week 18 is later so SF's record should be 0.40
        assert ("BUF", 2023) in records
        assert records[("BUF", 2023)] == pytest.approx(0.50)
        assert ("SF", 2023) in records
        assert records[("SF", 2023)] == pytest.approx(0.40)


class TestComputeBaselines:
    """Tests for compute_baselines function."""

    def test_compute_baselines_returns_dict(self):
        """compute_baselines returns dict with correct keys."""
        df = _make_minimal_df(
            home_wins=[1, 0, 1, 1, 0],
            home_rolling_wins=[0.6, 0.6, 0.6, 0.6, 0.6],
            away_rolling_wins=[0.4, 0.4, 0.4, 0.4, 0.4],
        )
        result = compute_baselines(df, 2023)

        assert isinstance(result, dict)
        expected_keys = {
            "season",
            "always_home_accuracy",
            "better_record_accuracy",
            "always_home_game_count",
            "better_record_game_count",
        }
        assert set(result.keys()) == expected_keys
        assert result["season"] == 2023

    def test_compute_baselines_filters_season(self):
        """compute_baselines only evaluates games from the specified season."""
        # 3 games in 2022 (2 home wins), 3 games in 2023 (1 home win)
        df_2022 = _make_minimal_df(
            home_wins=[1, 1, 0],
            season=2022,
        )
        df_2023 = _make_minimal_df(
            home_wins=[1, 0, 0],
            season=2023,
        )
        df = pd.concat([df_2022, df_2023], ignore_index=True)

        result = compute_baselines(df, 2023)

        # always_home on 2023: 1/3 home wins
        assert result["always_home_accuracy"] == pytest.approx(1 / 3)
        assert result["always_home_game_count"] == 3
        assert result["better_record_game_count"] == 3
