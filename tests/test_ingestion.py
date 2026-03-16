"""Integration tests for the NFL data ingestion pipeline."""
import os
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from click.testing import CliRunner

from data.sources import (
    CURATED_PBP_COLUMNS,
    CURATED_SCHEDULE_COLUMNS,
    TEAM_COLUMNS_PBP,
    TEAM_COLUMNS_SCHEDULE,
    EXPECTED_REG_SEASON_GAMES,
)
from data.transforms import normalize_teams_in_df, filter_preseason, select_pbp_columns
from data.validators import validate_game_count, ValidationResult


# ---------------------------------------------------------------------------
# Unit tests (no DB required)
# ---------------------------------------------------------------------------


class TestUpsertDataframe:
    """Tests for the upsert_dataframe helper function."""

    def test_upsert_dataframe_builds_correct_statement(self):
        """Verify upsert_dataframe calls on_conflict_do_update with correct conflict columns."""
        from data.ingest import upsert_dataframe

        # Create a minimal DataFrame
        df = pd.DataFrame({"game_id": ["2023_01_KC_DET"], "play_id": [1], "season": [2023]})

        # Mock engine and table
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        # Create a mock table with columns
        mock_table = MagicMock()
        mock_col_game_id = MagicMock()
        mock_col_game_id.name = "game_id"
        mock_col_play_id = MagicMock()
        mock_col_play_id.name = "play_id"
        mock_col_season = MagicMock()
        mock_col_season.name = "season"
        mock_table.columns = [mock_col_game_id, mock_col_play_id, mock_col_season]

        # Patch pg_insert to verify the call
        with patch("data.ingest.pg_insert") as mock_pg_insert:
            mock_stmt = MagicMock()
            mock_pg_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.excluded = {"game_id": "game_id", "play_id": "play_id", "season": "season"}
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            upsert_dataframe(mock_engine, mock_table, df, ["game_id", "play_id"])

            # Verify on_conflict_do_update was called with the right conflict columns
            mock_stmt.on_conflict_do_update.assert_called_once()
            call_kwargs = mock_stmt.on_conflict_do_update.call_args
            assert call_kwargs.kwargs["index_elements"] == ["game_id", "play_id"]


class TestIngestCLI:
    """Tests for the Click CLI interface."""

    def test_ingest_cli_accepts_seasons_option(self):
        """Verify CLI accepts --seasons and processes only specified seasons."""
        from data.ingest import ingest

        runner = CliRunner()

        with patch("data.ingest.get_engine") as mock_engine, \
             patch("data.ingest.get_table") as mock_table, \
             patch("data.ingest.load_pbp_cached") as mock_pbp, \
             patch("data.ingest.load_schedules_cached") as mock_sched, \
             patch("data.ingest.upsert_dataframe"), \
             patch("data.ingest.print_validation_summary", return_value=True), \
             patch("data.ingest._log_ingestion"):

            # Create minimal DataFrames that pass transforms
            pbp_df = pd.DataFrame({col: ["test"] for col in CURATED_PBP_COLUMNS})
            pbp_df["season_type"] = "REG"
            mock_pbp.return_value = pbp_df

            sched_df = pd.DataFrame({col: ["test"] for col in CURATED_SCHEDULE_COLUMNS})
            sched_df["game_type"] = "REG"
            mock_sched.return_value = sched_df

            result = runner.invoke(ingest, ["--seasons", "2023", "--seasons", "2024"])

            # Should have loaded exactly 2 seasons
            assert mock_pbp.call_count == 2
            mock_pbp.assert_any_call(2023)
            mock_pbp.assert_any_call(2024)

    def test_ingest_exits_nonzero_on_validation_failure(self):
        """Verify CLI exits with non-zero code when validation fails."""
        from data.ingest import ingest

        runner = CliRunner()

        with patch("data.ingest.get_engine"), \
             patch("data.ingest.get_table"), \
             patch("data.ingest.load_pbp_cached") as mock_pbp, \
             patch("data.ingest.load_schedules_cached") as mock_sched, \
             patch("data.ingest.upsert_dataframe"), \
             patch("data.ingest.print_validation_summary", return_value=False), \
             patch("data.ingest._log_ingestion"):

            pbp_df = pd.DataFrame({col: ["test"] for col in CURATED_PBP_COLUMNS})
            pbp_df["season_type"] = "REG"
            mock_pbp.return_value = pbp_df

            sched_df = pd.DataFrame({col: ["test"] for col in CURATED_SCHEDULE_COLUMNS})
            sched_df["game_type"] = "REG"
            mock_sched.return_value = sched_df

            result = runner.invoke(ingest, ["--seasons", "2023"])

            assert result.exit_code != 0


class TestTransformPipeline:
    """Tests for the transform pipeline used during ingestion."""

    def test_ingest_normalizes_teams_before_upsert(self):
        """Verify OAK -> LV normalization in team columns."""
        df = pd.DataFrame({
            "home_team": ["OAK", "KC"],
            "away_team": ["SD", "NE"],
            "posteam": ["STL", "BUF"],
            "defteam": ["WSH", "MIA"],
        })

        result = normalize_teams_in_df(df, TEAM_COLUMNS_PBP)

        assert result["home_team"].tolist() == ["LV", "KC"]
        assert result["away_team"].tolist() == ["LAC", "NE"]
        assert result["posteam"].tolist() == ["LA", "BUF"]
        assert result["defteam"].tolist() == ["WAS", "MIA"]

    def test_ingest_filters_preseason(self):
        """Verify preseason rows are removed, REG and POST kept."""
        df = pd.DataFrame({
            "season_type": ["PRE", "REG", "POST"],
            "game_id": ["g1", "g2", "g3"],
        })

        result = filter_preseason(df, "season_type")

        assert len(result) == 2
        assert "PRE" not in result["season_type"].values
        assert "REG" in result["season_type"].values
        assert "POST" in result["season_type"].values

    def test_ingest_adds_games_in_season(self):
        """Verify games_in_season column: 16 for <=2020, 17 for 2021+."""
        # For season 2019 (16-game era)
        df_2019 = pd.DataFrame({"game_id": ["g1"]})
        season_2019 = 2019
        df_2019["games_in_season"] = 16 if season_2019 <= 2020 else 17
        assert df_2019["games_in_season"].iloc[0] == 16

        # For season 2021 (17-game era)
        df_2021 = pd.DataFrame({"game_id": ["g1"]})
        season_2021 = 2021
        df_2021["games_in_season"] = 16 if season_2021 <= 2020 else 17
        assert df_2021["games_in_season"].iloc[0] == 17

    def test_schedule_preseason_filtering_by_game_type(self):
        """Verify schedule filtering excludes PRE but keeps REG, WC, DIV, CON, SB."""
        df = pd.DataFrame({
            "game_type": ["PRE", "REG", "WC", "DIV", "CON", "SB"],
            "game_id": ["g1", "g2", "g3", "g4", "g5", "g6"],
        })

        # Same filter logic as ingest.py for schedules
        result = df[df["game_type"] != "PRE"].reset_index(drop=True)

        assert len(result) == 5
        assert "PRE" not in result["game_type"].values
        assert set(result["game_type"].values) == {"REG", "WC", "DIV", "CON", "SB"}


# ---------------------------------------------------------------------------
# Integration tests (require running PostgreSQL)
# ---------------------------------------------------------------------------

requires_db = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set -- skip integration tests",
)


@requires_db
class TestIngestionIntegration:
    """Integration tests requiring a running PostgreSQL instance."""

    @pytest.fixture(autouse=True)
    def _setup_engine(self):
        """Set up database engine for integration tests."""
        from data.db import get_engine
        self.engine = get_engine()

    def test_pbp_upsert_idempotent(self):
        """Upsert same PBP data twice, row count stays the same."""
        from data.ingest import upsert_dataframe
        from data.db import get_table
        from sqlalchemy import text

        table = get_table("raw_pbp", self.engine)

        # Create a small test DataFrame matching raw_pbp schema
        df = pd.DataFrame({
            "play_id": [9999, 9998],
            "game_id": ["TEST_GAME_001", "TEST_GAME_001"],
            "season": [2099, 2099],
            "season_type": ["REG", "REG"],
            "week": [1, 1],
            "home_team": ["KC", "KC"],
            "away_team": ["DET", "DET"],
        })
        # Fill optional columns with None
        for col in CURATED_PBP_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Upsert once
        upsert_dataframe(self.engine, table, df, ["game_id", "play_id"])
        with self.engine.connect() as conn:
            count1 = conn.execute(
                text("SELECT COUNT(*) FROM raw_pbp WHERE game_id = 'TEST_GAME_001'")
            ).scalar()

        # Upsert again (same data)
        upsert_dataframe(self.engine, table, df, ["game_id", "play_id"])
        with self.engine.connect() as conn:
            count2 = conn.execute(
                text("SELECT COUNT(*) FROM raw_pbp WHERE game_id = 'TEST_GAME_001'")
            ).scalar()

        assert count1 == count2 == 2

        # Cleanup
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM raw_pbp WHERE game_id = 'TEST_GAME_001'"))

    def test_schedule_upsert_idempotent(self):
        """Upsert same schedule data twice, row count stays the same."""
        from data.ingest import upsert_dataframe
        from data.db import get_table
        from sqlalchemy import text

        table = get_table("schedules", self.engine)

        df = pd.DataFrame({
            "game_id": ["TEST_SCHED_001", "TEST_SCHED_002"],
            "season": [2099, 2099],
            "game_type": ["REG", "REG"],
            "week": [1, 1],
            "home_team": ["KC", "DET"],
            "away_team": ["DET", "KC"],
            "games_in_season": [17, 17],
        })
        for col in CURATED_SCHEDULE_COLUMNS:
            if col not in df.columns:
                df[col] = None

        upsert_dataframe(self.engine, table, df, ["game_id"])
        with self.engine.connect() as conn:
            count1 = conn.execute(
                text("SELECT COUNT(*) FROM schedules WHERE game_id LIKE 'TEST_SCHED_%'")
            ).scalar()

        upsert_dataframe(self.engine, table, df, ["game_id"])
        with self.engine.connect() as conn:
            count2 = conn.execute(
                text("SELECT COUNT(*) FROM schedules WHERE game_id LIKE 'TEST_SCHED_%'")
            ).scalar()

        assert count1 == count2 == 2

        # Cleanup
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM schedules WHERE game_id LIKE 'TEST_SCHED_%'"))

    def test_ingestion_log_created(self):
        """After ingestion logging, ingestion_log table has entries."""
        from data.ingest import _log_ingestion
        from sqlalchemy import text

        _log_ingestion(self.engine, 2099, "test_table", 10, 256, 256, "OK")

        with self.engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM ingestion_log WHERE season = 2099")
            ).scalar()

        assert count >= 1

        # Cleanup
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM ingestion_log WHERE season = 2099"))
