"""Tests for data/validators.py validation functions."""
from data.validators import validate_game_count


def test_validate_correct_count_pre2021():
    result = validate_game_count(2019, 256)
    assert result.status == "OK"
    assert result.expected_games == 256
    assert result.actual_games == 256


def test_validate_correct_count_post2021():
    result = validate_game_count(2021, 272)
    assert result.status == "OK"
    assert result.expected_games == 272
    assert result.actual_games == 272


def test_validate_mismatch():
    result = validate_game_count(2019, 250)
    assert result.status == "MISMATCH"
    assert result.expected_games == 256
    assert result.actual_games == 250


def test_validate_unknown_season():
    result = validate_game_count(1990, 100)
    assert result.status == "UNKNOWN_SEASON"
