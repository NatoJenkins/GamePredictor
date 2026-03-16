---
phase: 02-feature-engineering
verified: 2026-03-16T22:30:00Z
status: human_needed
score: 12/12 must-haves verified
re_verification: true
  previous_status: gaps_found
  previous_score: 11/12
  gaps_closed:
    - "sql/init.sql game_features DDL column names now match pipeline output exactly (14/14 rolling columns aligned)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run python -m features --seasons 2023 --store against a live PostgreSQL instance"
    expected: "Command completes without errors; SELECT COUNT(*) FROM game_features WHERE season = 2023 returns ~285 rows; rolling columns are NULL for week 1 games and have plausible EPA values for later weeks"
    why_human: "store_game_features() requires a live DB; automated checks confirm DDL and pipeline columns align but cannot execute the actual INSERT without a running PostgreSQL container"
---

# Phase 2: Feature Engineering Verification Report

**Phase Goal:** A game_features table exists with one row per game (home perspective) containing rolling offensive, defensive, and situational features computed with zero data leakage
**Verified:** 2026-03-16T22:30:00Z
**Status:** human_needed
**Re-verification:** Yes — after plan 02-03 gap closure (DDL column name fix)

## Re-verification Summary

The single gap identified in the initial verification has been closed. Plan 02-03 corrected `sql/init.sql` by renaming 6 abbreviated column names and adding 4 missing columns. All 24 feature tests continue to pass (no regressions). All 12 must-haves are now verified. One human verification item remains (end-to-end live DB write), unchanged from the initial verification.

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|---------|
| 1  | Rolling EPA/play features use only games prior to each row's game date | VERIFIED | `compute_rolling_features` applies `x.shift(1).expanding().mean()` grouped by `(team, season)`; regression: 24/24 tests pass |
| 2  | Rolling point diff, turnover diff, and win rate use only prior-game data | VERIFIED | Same shift(1) mechanism; all 7 rolling columns share the same loop in `compute_rolling_features` |
| 3  | Situational features (home_rest, away_rest, div_game, week) are populated for every row | VERIFIED | `build_home_perspective` joins these directly from schedule; confirmed present in pipeline output columns |
| 4  | Feature matrix has exactly one row per regular-season game from home team perspective | VERIFIED | `build_home_perspective` filters `game_type == "REG"` then merges home and away rolling; `test_home_perspective_one_row_per_game` passes |
| 5  | Week 1 games have NaN for all rolling features (no prior data within season) | VERIFIED | `test_week1_rolling_features_are_nan` passes (leakage test); shift(1) pushes first row to NaN with no fill |
| 6  | No feature column contains result, home_score, or away_score directly | VERIFIED | `build_game_features` asserts FORBIDDEN_FEATURES not in output; `test_no_forbidden_features_in_output` passes |
| 7  | Leakage tests structurally verify no rolling feature for game G includes data from game G or later | VERIFIED | `features/tests/test_leakage.py` has 6 tests; all pass; CLAUDE.md gate is in place |
| 8  | Removing the last game of the season does not change any prior game's features | VERIFIED | `test_removing_future_game_does_not_change_past_features` passes |
| 9  | Rolling resets at season boundaries (per-season groupby) | VERIFIED | `groupby(["team", "season"])` in `compute_rolling_features`; `test_rolling_resets_at_season_boundary` passes |
| 10 | Feature pipeline is runnable via CLI command `python -m features` | VERIFIED | `features/__main__.py` exists with Click command; `--help` flag works |
| 11 | Pipeline in-memory computation is substantive and non-stub | VERIFIED | `features/build.py` is 286 lines with 5 complete functions; no TODO/placeholder/pass stubs found |
| 12 | sql/init.sql DDL column names match the pipeline output column names for store_game_features() | VERIFIED (gap closed) | DDL now declares 14 rolling columns (7 home + 7 away) that exactly match pipeline output. Python cross-check confirms 0 missing columns, 0 extra columns. Old abbreviated names (`home_rolling_off_epa`, `home_rolling_def_epa`, `home_rolling_win_rate` and away equivalents) are absent. All 4 previously missing turnover columns are present. |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `features/definitions.py` | Feature column lists and rolling config | VERIFIED | Contains ROLLING_FEATURES (7 items), SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES, EPA_PLAY_TYPES; importable |
| `features/build.py` | Full feature pipeline | VERIFIED | 286 lines; exports all 5 functions: aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features, store_game_features; uses shift(1) + groupby(team, season) |
| `features/tests/test_features.py` | Unit tests for feature correctness | VERIFIED | 18 tests across 4 classes; all pass (regression confirmed) |
| `features/tests/conftest.py` | Synthetic test fixtures | VERIFIED | Contains synthetic_pbp, synthetic_schedule, synthetic_two_season_schedule, synthetic_two_season_pbp |
| `features/tests/test_leakage.py` | Leakage validation tests (FEAT-05 gate) | VERIFIED | 6 tests in TestLeakagePrevention class; all pass (regression confirmed) |
| `features/__main__.py` | CLI entry point for feature build | VERIFIED | Click command with --seasons and --store/--no-store; builds and reports feature matrix |
| `sql/init.sql` | game_features DDL | VERIFIED | CREATE TABLE IF NOT EXISTS game_features with exactly 14 rolling columns whose names match pipeline output; 2 indexes; no old abbreviated names; all 4 missing turnover columns added |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `features/build.py` | `features/definitions.py` | `from features.definitions import` | WIRED | Line 8: imports ROLLING_FEATURES, SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES, EPA_PLAY_TYPES |
| `features/build.py` | `data/loaders.py` | `load_pbp_cached, load_schedules_cached` | WIRED | Lines 207-208 inside conditional load path; called when pbp/schedule args are None |
| `features/build.py` | `data/sources.py` | `TEAM_COLUMNS_PBP, TEAM_COLUMNS_SCHEDULE` | WIRED | Line 209 imports constants; `play_type.isin(EPA_PLAY_TYPES)` filter at line 30 |
| `features/tests/test_features.py` | `features/build.py` | `from features.build import` | WIRED | Line 1 imports aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features |
| `features/tests/test_leakage.py` | `features/build.py` | `from features.build import` | WIRED | Lines 9-13 import aggregate_game_stats, compute_rolling_features, build_game_features |
| `features/__main__.py` | `features/build.py` | `from features.build import build_game_features, store_game_features` | WIRED | Line 5 |
| `store_game_features()` | `sql/init.sql` DDL | column names must match at runtime | WIRED | Python cross-check confirms 14/14 DDL rolling column names exactly equal pipeline output column names; 0 missing, 0 extra |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| FEAT-01 | 02-01-PLAN.md | Rolling EPA/play features (offensive and defensive) using only data prior to each game — strictly no leakage | SATISFIED | compute_rolling_features uses shift(1).expanding().mean() grouped by (team, season); leakage tests pass (regression confirmed) |
| FEAT-02 | 02-01-PLAN.md | Rolling basic game stats (point differential, turnover differential, win rate) using only prior-game data | SATISFIED | All computed in same shift(1) loop; 18 unit tests verify correctness (regression confirmed) |
| FEAT-03 | 02-01-PLAN.md | Situational features per game: home/away flag, rest days, week of season, divisional game flag | SATISFIED | home_rest, away_rest, div_game, week all present in pipeline output; test_home_perspective_situational_features passes |
| FEAT-04 | 02-01-PLAN.md | Feature matrix structured as one row per game from the home team perspective | SATISFIED | build_home_perspective produces one row per REG game; test_home_perspective_one_row_per_game passes |
| FEAT-05 | 02-02-PLAN.md | Automated leakage validation tests run against the feature pipeline and must pass before any model training | SATISFIED | 6 tests in features/tests/test_leakage.py; all pass; CLAUDE.md mandated gate documented and active |

No orphaned requirements. All 5 Phase 2 requirement IDs (FEAT-01 through FEAT-05) are claimed by plans and verified.

### Anti-Patterns Found

None. No TODO/FIXME/PLACEHOLDER comments in any feature file. No empty function bodies or stub return values. The DDL blocker from the initial verification has been resolved.

### Human Verification Required

#### 1. End-to-end DB storage

**Test:** Run `python -m features --seasons 2023 --store` against a live PostgreSQL instance (Docker container from Phase 1).
**Expected:** Command completes without errors; `SELECT COUNT(*) FROM game_features WHERE season = 2023` returns approximately 285 rows; a sample SELECT shows rolling columns as NULL for week 1 games and plausible EPA values (typically -0.3 to +0.3 range) for later weeks.
**Why human:** store_game_features() requires a live running PostgreSQL container. Automated checks have confirmed DDL and pipeline column sets are identical, making a SQL column mismatch error impossible — but the actual INSERT execution and data sanity check require a live DB.

### Gap Closure Confirmation

The single gap from the initial verification is confirmed closed:

**Gap:** DDL column names in `sql/init.sql` did not match pipeline output.

**Fix applied (plan 02-03, commit 04bd28c):**
- Renamed 6 columns: `home_rolling_off_epa` -> `home_rolling_off_epa_per_play`, `home_rolling_def_epa` -> `home_rolling_def_epa_per_play`, `home_rolling_win_rate` -> `home_rolling_win` (and away equivalents)
- Added 4 missing columns: `home_rolling_turnovers_committed REAL`, `home_rolling_turnovers_forced REAL`, `away_rolling_turnovers_committed REAL`, `away_rolling_turnovers_forced REAL`

**Verification:** Python cross-check against both `sql/init.sql` and `features/build.py` confirms 14/14 DDL rolling column names exactly match pipeline output column names. 0 missing, 0 extra, 0 old abbreviated names remaining.

**Regression check:** All 24 feature tests pass (`pytest features/tests/ -x -q` exits 0 in 0.54s). No regressions introduced by the DDL change.

---

_Verified: 2026-03-16T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
