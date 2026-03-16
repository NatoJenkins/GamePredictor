"""Validation functions for NFL data ingestion."""
from dataclasses import dataclass
from data.sources import EXPECTED_REG_SEASON_GAMES


@dataclass
class ValidationResult:
    season: int
    table: str
    expected_games: int
    actual_games: int
    status: str  # "OK" or "MISMATCH"


def validate_game_count(season: int, actual_count: int, table: str = "schedules") -> ValidationResult:
    """Validate actual game count against expected for a season."""
    expected = EXPECTED_REG_SEASON_GAMES.get(season)
    if expected is None:
        return ValidationResult(
            season=season, table=table, expected_games=0,
            actual_games=actual_count, status="UNKNOWN_SEASON",
        )
    status = "OK" if actual_count == expected else "MISMATCH"
    return ValidationResult(
        season=season, table=table, expected_games=expected,
        actual_games=actual_count, status=status,
    )


def print_validation_summary(results: list[ValidationResult]) -> bool:
    """Print validation summary table. Returns True if all pass."""
    print(f"\n{'Season':<8} {'Table':<12} {'Expected':<10} {'Actual':<10} {'Status':<10}")
    print("-" * 50)
    all_ok = True
    for r in results:
        icon = "OK" if r.status == "OK" else "FAIL"
        print(f"{r.season:<8} {r.table:<12} {r.expected_games:<10} {r.actual_games:<10} {icon:<10}")
        if r.status != "OK":
            all_ok = False
    return all_ok
