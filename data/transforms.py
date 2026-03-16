"""Data transformation functions for NFL data ingestion."""
import pandas as pd
from data.sources import (
    TEAM_ABBREV_MAP,
    TEAM_COLUMNS_PBP,
    TEAM_COLUMNS_SCHEDULE,
    CURATED_PBP_COLUMNS,
    CURATED_SCHEDULE_COLUMNS,
)


def normalize_teams_in_df(df: pd.DataFrame, team_columns: list[str]) -> pd.DataFrame:
    """Apply TEAM_ABBREV_MAP to specified team columns in a DataFrame."""
    df = df.copy()
    for col in team_columns:
        if col in df.columns:
            df[col] = df[col].map(lambda x: TEAM_ABBREV_MAP.get(x, x) if pd.notna(x) else x)
    return df


def filter_preseason(df: pd.DataFrame, season_type_col: str = "season_type") -> pd.DataFrame:
    """Remove preseason rows. Keep REG and playoff game types."""
    return df[df[season_type_col] != "PRE"].reset_index(drop=True)


def select_pbp_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select curated PBP columns. Raises KeyError if any required column missing (schema drift)."""
    missing = [c for c in CURATED_PBP_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Schema drift: missing columns in PBP data: {missing}")
    return df[CURATED_PBP_COLUMNS].copy()


def select_schedule_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select curated schedule columns. Raises KeyError if any required column missing."""
    missing = [c for c in CURATED_SCHEDULE_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Schema drift: missing columns in schedule data: {missing}")
    return df[CURATED_SCHEDULE_COLUMNS].copy()
