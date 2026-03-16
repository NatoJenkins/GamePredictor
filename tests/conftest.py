"""Shared test fixtures."""
import pytest
import pandas as pd


@pytest.fixture
def sample_pbp_df():
    """Sample PBP DataFrame with all curated columns plus extras."""
    from data.sources import CURATED_PBP_COLUMNS
    data = {col: ["test_val"] for col in CURATED_PBP_COLUMNS}
    data["extra_column_not_needed"] = ["should_be_dropped"]
    # Use old team abbreviations to test normalization
    data["home_team"] = ["OAK"]
    data["away_team"] = ["SD"]
    data["posteam"] = ["STL"]
    data["defteam"] = ["WSH"]
    return pd.DataFrame(data)


@pytest.fixture
def sample_schedule_df():
    """Sample schedule DataFrame with curated columns."""
    from data.sources import CURATED_SCHEDULE_COLUMNS
    data = {col: ["test_val"] for col in CURATED_SCHEDULE_COLUMNS}
    data["home_team"] = ["OAK"]
    data["away_team"] = ["SD"]
    return pd.DataFrame(data)
