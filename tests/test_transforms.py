"""Tests for data/transforms.py transformation functions."""
import pandas as pd
import pytest
from data.sources import normalize_team_abbrev, TEAM_COLUMNS_PBP


def test_normalize_team_abbrev_maps_all_four():
    assert normalize_team_abbrev("OAK") == "LV"
    assert normalize_team_abbrev("SD") == "LAC"
    assert normalize_team_abbrev("STL") == "LA"
    assert normalize_team_abbrev("WSH") == "WAS"


def test_normalize_team_abbrev_passthrough():
    assert normalize_team_abbrev("KC") == "KC"


def test_normalize_teams_in_df(sample_pbp_df):
    from data.transforms import normalize_teams_in_df
    result = normalize_teams_in_df(sample_pbp_df, TEAM_COLUMNS_PBP)
    assert result["home_team"].iloc[0] == "LV"
    assert result["away_team"].iloc[0] == "LAC"
    assert result["posteam"].iloc[0] == "LA"
    assert result["defteam"].iloc[0] == "WAS"


def test_filter_preseason():
    from data.transforms import filter_preseason
    df = pd.DataFrame({
        "season_type": ["PRE", "REG", "POST"],
        "value": [1, 2, 3],
    })
    result = filter_preseason(df)
    assert len(result) == 2
    assert "PRE" not in result["season_type"].values
    assert "REG" in result["season_type"].values
    assert "POST" in result["season_type"].values


def test_select_pbp_columns_keeps_curated(sample_pbp_df):
    from data.transforms import select_pbp_columns
    from data.sources import CURATED_PBP_COLUMNS
    result = select_pbp_columns(sample_pbp_df)
    assert list(result.columns) == CURATED_PBP_COLUMNS
    assert "extra_column_not_needed" not in result.columns


def test_select_pbp_columns_schema_drift():
    from data.transforms import select_pbp_columns
    df = pd.DataFrame({"game_id": ["test"], "play_id": [1]})
    with pytest.raises(KeyError, match="Schema drift"):
        select_pbp_columns(df)
