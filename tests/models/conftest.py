"""Shared fixtures for model tests.

Provides synthetic feature DataFrames mimicking build_game_features() output
for deterministic testing of baseline computation and model training.
"""

import pytest
import pandas as pd
import numpy as np


ROLLING_COLS = [
    "home_rolling_off_epa_per_play",
    "home_rolling_def_epa_per_play",
    "home_rolling_point_diff",
    "home_rolling_turnovers_committed",
    "home_rolling_turnovers_forced",
    "home_rolling_turnover_diff",
    "home_rolling_win",
    "away_rolling_off_epa_per_play",
    "away_rolling_def_epa_per_play",
    "away_rolling_point_diff",
    "away_rolling_turnovers_committed",
    "away_rolling_turnovers_forced",
    "away_rolling_turnover_diff",
    "away_rolling_win",
]


@pytest.fixture
def sample_feature_df():
    """Synthetic feature DataFrame mimicking build_game_features() output.

    20 rows across seasons 2022 and 2023 (10 each).
    Includes:
    - Mix of home wins (1), away wins (0), and one tie (NaN) per season
    - Known rolling_win values for deterministic better-record predictions
    - Some tied-record games to exercise the prior-season tiebreaker
    - Week 1 rows with NaN rolling features to test NaN handling
    """
    teams = ["KC", "BUF", "SF", "PHI", "DAL", "MIA", "BAL", "DET", "CIN", "JAX"]
    rows = []

    # Season 2022: 10 games
    for i in range(10):
        week = i + 1
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]

        # Week 1 has NaN rolling features
        if week == 1:
            rolling_vals = {col: np.nan for col in ROLLING_COLS}
        else:
            rolling_vals = {col: 0.5 for col in ROLLING_COLS}
            # Set specific rolling_win values for deterministic results
            rolling_vals["home_rolling_win"] = 0.6 + i * 0.02
            rolling_vals["away_rolling_win"] = 0.4 + i * 0.01

        # Game 5 (i=4) is a tie
        if i == 4:
            home_win = None
        elif i % 3 == 0:
            home_win = 0  # away wins
        else:
            home_win = 1  # home wins

        # Game 8 (i=7) has tied rolling_win to exercise tiebreaker
        if week > 1 and i == 7:
            rolling_vals["home_rolling_win"] = 0.5
            rolling_vals["away_rolling_win"] = 0.5

        row = {
            "game_id": f"2022_{week:02d}_{away}_{home}",
            "season": 2022,
            "week": week,
            "gameday": f"2022-09-{10 + i:02d}",
            "home_team": home,
            "away_team": away,
            "home_win": home_win,
            "home_rest": 7,
            "away_rest": 7,
            "div_game": 1 if i < 3 else 0,
        }
        row.update(rolling_vals)
        rows.append(row)

    # Season 2023: 10 games
    for i in range(10):
        week = i + 1
        home = teams[(i + 2) % len(teams)]
        away = teams[(i + 3) % len(teams)]

        if week == 1:
            rolling_vals = {col: np.nan for col in ROLLING_COLS}
        else:
            rolling_vals = {col: 0.5 for col in ROLLING_COLS}
            rolling_vals["home_rolling_win"] = 0.55 + i * 0.03
            rolling_vals["away_rolling_win"] = 0.45 + i * 0.02

        # Game 3 (i=2) is a tie
        if i == 2:
            home_win = None
        elif i % 2 == 0:
            home_win = 1
        else:
            home_win = 0

        # Game 6 (i=5) has tied rolling_win
        if week > 1 and i == 5:
            rolling_vals["home_rolling_win"] = 0.6
            rolling_vals["away_rolling_win"] = 0.6

        row = {
            "game_id": f"2023_{week:02d}_{away}_{home}",
            "season": 2023,
            "week": week,
            "gameday": f"2023-09-{10 + i:02d}",
            "home_team": home,
            "away_team": away,
            "home_win": home_win,
            "home_rest": 7,
            "away_rest": 7,
            "div_game": 0,
        }
        row.update(rolling_vals)
        rows.append(row)

    df = pd.DataFrame(rows)
    # Convert home_win to float so NaN works properly (int can't hold NaN)
    df["home_win"] = df["home_win"].astype(float)
    return df
