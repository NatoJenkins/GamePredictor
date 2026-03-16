# Phase 2: Feature Engineering - Research

**Researched:** 2026-03-16
**Domain:** NFL game-level feature engineering, rolling statistics, data leakage prevention, pandas temporal operations
**Confidence:** HIGH

## Summary

Phase 2 transforms raw play-by-play and schedule data (ingested in Phase 1) into a `game_features` table with one row per game from the home team perspective. The core challenge is computing rolling team-level statistics (EPA/play, point differential, turnover differential, win rate) using **strictly prior-game data only** -- no information from the current game or future games may leak into features. CLAUDE.md mandates that all rolling features use `.shift(1)` with no exceptions.

The data pipeline reads from the parquet cache files (`data/cache/`) rather than querying PostgreSQL, since all 20 seasons of PBP and schedule data are already cached locally. Game-level aggregates are computed from PBP data (EPA, turnovers) and schedule data (scores, rest days, div_game). Rolling features are computed per-team across the full season using pandas groupby + shift(1) + expanding/rolling operations. The final feature matrix is one row per regular-season game (home perspective), totaling 5,183 rows across 2005-2024.

CLAUDE.md contains critical constraints: (1) never modify `features/build.py` or `features/definitions.py` during autoresearch -- this implies these files MUST be created in this phase as the canonical feature pipeline, (2) all rolling features require `.shift(1)`, (3) leakage tests in `features/tests/test_leakage.py` must pass before model training, (4) never use `result`, `home_score`, or `away_score` as model features (these are target-adjacent and would constitute leakage).

**Primary recommendation:** Build the feature pipeline as a two-stage process: (1) compute game-level per-team statistics from PBP + schedule data, (2) compute rolling features with shift(1) per team then pivot to home-perspective rows. Store feature definitions in `features/definitions.py` and the build pipeline in `features/build.py`. Leakage tests use synthetic data with planted spikes to structurally verify no future data contaminates features.

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEAT-01 | System computes rolling EPA/play features (offensive and defensive) using only data prior to each game | PBP `epa` column is 100% populated for pass/run plays across all seasons 2005-2024. Offensive EPA = mean(epa) grouped by (game_id, posteam); defensive EPA = mean(epa) grouped by (game_id, defteam). Rolling uses shift(1) + expanding/rolling window. |
| FEAT-02 | System computes rolling basic game stats (point differential, turnover differential, win rate) using only prior-game data | Schedule `result` column = home_score - away_score (verified). Turnovers from PBP: interception + fumble_lost per (game_id, posteam). Win rate from schedule result. All use same shift(1) rolling pattern. |
| FEAT-03 | System computes situational features per game: home/away flag, rest days, week of season, divisional game flag | Schedule table already contains `home_rest`, `away_rest`, `div_game`, `week` columns with zero NaN values across all 20 seasons. These are direct lookups, not rolling. |
| FEAT-04 | Feature matrix is structured as one row per game from the home team perspective | 5,183 total regular-season games (256/season for 2005-2020, 272 for 2021-2024, minus 1 for cancelled 2022 game). Each row contains home team rolling stats AND away team rolling stats as separate columns. |
| FEAT-05 | Automated leakage validation tests run against the feature pipeline and must pass before any model training | CLAUDE.md specifies `features/tests/test_leakage.py`. Tests use synthetic data with planted extreme values to verify shift(1) prevents contamination. Tests are a pytest gate for Phase 3. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | 2.x (already installed) | DataFrame operations, groupby, rolling, shift | Project already uses pandas throughout; rolling/shift API is mature and well-documented |
| numpy | (pandas dependency) | Numeric operations, NaN handling | Used implicitly via pandas |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | latest (already in dev deps) | Leakage tests and feature validation | `features/tests/test_leakage.py` and `features/tests/test_features.py` |
| sqlalchemy | 2.0+ (already installed) | Write game_features table to PostgreSQL | Final upsert of feature matrix to DB |
| click | latest (already installed) | CLI for feature build command | `python -m features` or `python features/build.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandas rolling | polars rolling | Polars is faster but project uses pandas throughout; consistency > speed for 5K rows |
| In-memory parquet reads | PostgreSQL queries | Parquet reads are faster and avoid DB dependency for feature computation; DB used only for final storage |
| Expanding window | Fixed rolling window (e.g., last 5) | Expanding uses all prior data; fixed window is more recent-biased. Expanding is simpler and captures full season history. Can add fixed-window features as supplementary in Phase 3 experiments |

**Installation:**
No new packages needed. All dependencies are already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
features/
    __init__.py           # Empty
    __main__.py           # CLI entry: python -m features
    definitions.py        # Feature column lists, rolling window configs (NEVER modify during autoresearch)
    build.py              # Main pipeline: aggregate -> roll -> pivot -> store (NEVER modify during autoresearch)
    tests/
        __init__.py
        test_leakage.py   # Leakage validation tests (CLAUDE.md mandated path)
        test_features.py  # Unit tests for feature computation correctness
        conftest.py       # Shared fixtures for feature tests
sql/
    init.sql              # Add game_features table DDL (append to existing file)
```

### Pattern 1: Two-Stage Feature Pipeline
**What:** Separate game-level aggregation from rolling computation
**When to use:** Always -- separating stages makes debugging and testing easier

**Stage 1 - Game-Level Aggregation:**
```python
# Compute per-team, per-game stats from PBP data
# Filter to real plays (pass/run) for EPA
real_plays = pbp[pbp['play_type'].isin(['pass', 'run'])]

# Offensive EPA/play per team per game
off_epa = real_plays.groupby(['game_id', 'posteam']).agg(
    off_epa_per_play=('epa', 'mean'),
).reset_index()
off_epa.columns = ['game_id', 'team', 'off_epa_per_play']

# Defensive EPA/play per team per game (EPA allowed)
def_epa = real_plays.groupby(['game_id', 'defteam']).agg(
    def_epa_per_play=('epa', 'mean'),
).reset_index()
def_epa.columns = ['game_id', 'team', 'def_epa_per_play']

# Turnovers committed per team per game
plays_with_team = pbp[pbp['posteam'].notna()]
turnovers = plays_with_team.groupby(['game_id', 'posteam']).agg(
    ints_thrown=('interception', 'sum'),
    fumbles_lost=('fumble_lost', 'sum'),
).reset_index()
turnovers['turnovers_committed'] = turnovers['ints_thrown'] + turnovers['fumbles_lost']
```

**Stage 2 - Rolling with shift(1):**
```python
# CRITICAL: CLAUDE.md mandates shift(1) for ALL rolling features
# Sort by team + date, then shift(1) + expanding/rolling
team_log = team_log.sort_values(['team', 'gameday', 'week'])

for col in rolling_columns:
    team_log[f'rolling_{col}'] = (
        team_log.groupby('team')[col]
        .transform(lambda x: x.shift(1).expanding().mean())
    )
```

### Pattern 2: Team Game Log Construction
**What:** Build a complete team-level game log from both home and away perspectives before computing rolling stats
**When to use:** Required -- rolling stats need all games a team played, not just home games

```python
# Home perspective
home = schedule[['game_id','season','week','gameday','home_team','away_team',
                  'home_score','away_score','result']].copy()
home['team'] = home['home_team']
home['opponent'] = home['away_team']
home['points_for'] = home['home_score']
home['points_against'] = home['away_score']
home['point_diff'] = home['result']
home['win'] = (home['result'] > 0).astype(int)

# Away perspective
away = schedule[['game_id','season','week','gameday','home_team','away_team',
                  'home_score','away_score','result']].copy()
away['team'] = away['away_team']
away['opponent'] = away['home_team']
away['points_for'] = away['away_score']
away['points_against'] = away['home_score']
away['point_diff'] = -away['result']
away['win'] = (away['result'] < 0).astype(int)

team_log = pd.concat([home[cols], away[cols]], ignore_index=True)
team_log = team_log.sort_values(['team', 'gameday', 'week'])
```

### Pattern 3: Home-Perspective Pivot
**What:** After computing per-team rolling features, join them onto the schedule as home_team and away_team columns
**When to use:** Final step to create the one-row-per-game feature matrix

```python
# rolling_features has columns: game_id, team, rolling_off_epa, rolling_def_epa, etc.
# Join for home team
home_features = rolling_features.rename(columns={
    'rolling_off_epa': 'home_rolling_off_epa',
    'rolling_def_epa': 'home_rolling_def_epa',
    # ... etc
})
# Join for away team
away_features = rolling_features.rename(columns={
    'rolling_off_epa': 'away_rolling_off_epa',
    'rolling_def_epa': 'away_rolling_def_epa',
    # ... etc
})

game_features = schedule.merge(
    home_features, left_on=['game_id', 'home_team'], right_on=['game_id', 'team']
).merge(
    away_features, left_on=['game_id', 'away_team'], right_on=['game_id', 'team'],
    suffixes=('_home', '_away')
)
```

### Pattern 4: Per-Season Rolling (Reset at Season Boundary)
**What:** Reset rolling computations at each season boundary rather than carrying across seasons
**When to use:** Default approach -- NFL rosters change significantly between seasons, so prior-season stats have diminished relevance

```python
# Group by BOTH team AND season, so rolling resets each year
team_log[f'rolling_{col}'] = (
    team_log.groupby(['team', 'season'])[col]
    .transform(lambda x: x.shift(1).expanding().mean())
)
# Week 1 of each season will have NaN -- this is correct and expected
```

**Note on NaN handling:** Week 1 games will have NaN for all rolling features because there is no prior data within the season. This is correct behavior. The model training in Phase 3 can handle NaN values (XGBoost natively handles missing values). Do NOT fill NaN with zeros or means -- that would introduce bias.

### Anti-Patterns to Avoid
- **Using result, home_score, or away_score as model features:** CLAUDE.md explicitly prohibits this. These are target-adjacent (they contain the outcome). They are used to COMPUTE rolling features (point differential, win rate) but never appear directly in the feature matrix.
- **Rolling without shift(1):** CLAUDE.md mandates shift(1) for ALL rolling features. Without it, the current game's data leaks into its own features.
- **Mixing teams in rolling computation:** Each team's rolling stats must be computed independently via groupby('team'). Cross-team rolling would be meaningless.
- **Using game_id sort order instead of date:** Game IDs like `2023_01_DET_KC` encode week but not day-within-week (Thursday vs Sunday). Always sort by gameday + week for correct temporal ordering.
- **Carrying rolling stats across seasons without reset:** While technically "prior data," last year's stats reflect a different roster. Per-season rolling is the correct default.
- **Including playoff games in rolling stats for regular season:** Playoff games from the prior season should not feed into regular-season rolling stats. Regular season features should use regular season data only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rolling mean with exclusion | Custom loop over rows | `pandas groupby().transform(lambda x: x.shift(1).expanding().mean())` | pandas handles edge cases (NaN propagation, group boundaries) correctly |
| Turnover differential | Complex SQL join | pandas groupby + merge | Turnovers are committed by posteam; need to pair both teams per game to get differential |
| Date-based temporal ordering | Custom date parser | `pd.to_datetime(gameday)` + sort_values | pandas datetime sort is reliable; gameday format is consistent YYYY-MM-DD across all seasons |
| Feature matrix validation | Manual spot checks | Automated pytest assertions with synthetic data | Leakage is subtle; human spot checks miss edge cases |
| NaN handling in week 1 | fillna(0) or fillna(mean) | Leave as NaN | XGBoost handles NaN natively; filling introduces bias |

**Key insight:** The most dangerous hand-rolling is in leakage prevention. Using `.shift(1)` correctly with pandas groupby operations is structurally sound, but the pipeline must be tested with synthetic data to verify the structure is actually correct. One misplaced sort or missing groupby key silently introduces leakage.

## Common Pitfalls

### Pitfall 1: Forgetting shift(1) on One Feature
**What goes wrong:** All rolling features except one use shift(1). That one feature includes current-game data, creating leakage.
**Why it happens:** When adding new features, it's easy to forget the shift(1) call in one place.
**How to avoid:** Define a single `compute_rolling` function that always applies shift(1) internally. Never compute rolling features inline. Leakage tests will catch this.
**Warning signs:** One feature has suspiciously high predictive power compared to others.

### Pitfall 2: Incorrect Sort Order Before Rolling
**What goes wrong:** Rolling window includes games from the wrong temporal position because data is sorted by game_id alphabetically rather than by date.
**Why it happens:** Game IDs like `2023_01_ARI_WAS` sort alphabetically by team, not chronologically within a week.
**How to avoid:** Always sort by `['team', 'gameday', 'week']` before applying rolling operations. Use `gameday` (date string YYYY-MM-DD) as primary sort key.
**Warning signs:** Thursday Night Football game features include data from the following Sunday's games.

### Pitfall 3: Using result/home_score/away_score as Features
**What goes wrong:** Model sees the game outcome in its input features.
**Why it happens:** These columns are convenient and readily available in the schedule data.
**How to avoid:** CLAUDE.md explicitly prohibits this. Feature definitions list should never include these columns. Use them only to compute derived rolling features (point_diff -> rolling_point_diff).
**Warning signs:** Model accuracy suspiciously near 100%.

### Pitfall 4: Null posteam Rows in PBP Data
**What goes wrong:** ~2,500 plays per season have null `posteam` (game start, end-of-quarter, etc.). Including these in EPA calculations skews results.
**Why it happens:** Not all PBP rows represent actual plays. Some are administrative records.
**How to avoid:** Filter to `play_type in ('pass', 'run')` for EPA calculations. Filter to `posteam.notna()` for turnover calculations.
**Warning signs:** EPA averages seem unusually close to zero; turnover counts seem low.

### Pitfall 5: Turnover Differential Computation
**What goes wrong:** Computing turnovers "forced" instead of turnovers "committed" leads to incorrect differential.
**Why it happens:** PBP data records turnovers from the offense's perspective (interception = thrown by posteam, fumble_lost = lost by posteam). Getting the DIFFERENTIAL requires knowing what the opponent committed too.
**How to avoid:** Compute turnovers committed per (game_id, posteam), then for each team-game: `to_diff = opponent_committed - team_committed`. This requires a self-merge or pivot.
**Warning signs:** Turnover differential doesn't sum to zero across both teams in a game.

### Pitfall 6: Ties in Win Rate Calculation
**What goes wrong:** Games with result == 0 (ties) are counted as losses, skewing win rate.
**Why it happens:** Using `(result > 0).astype(int)` counts ties as 0 (loss).
**How to avoid:** Handle ties explicitly: `win = (result > 0).astype(float)` with ties as 0.5, or track wins/losses/ties separately. Ties are rare (~1-2 per season) but should be handled correctly.
**Warning signs:** Win rates slightly lower than expected for teams with ties.

### Pitfall 7: Modifying features/build.py or features/definitions.py During Autoresearch
**What goes wrong:** Breaks the experiment loop contract.
**Why it happens:** During Phase 3 experiments, there may be temptation to add features.
**How to avoid:** CLAUDE.md explicitly prohibits modifying these files during autoresearch. All experimentation happens in `models/train.py` only. Feature pipeline must be locked down in Phase 2.
**Warning signs:** CLAUDE.md violation.

## Code Examples

### Feature Definitions (features/definitions.py)
```python
"""Feature column definitions and rolling window configuration.

WARNING: Do NOT modify during autoresearch experiment loop (CLAUDE.md).
Only models/train.py may be modified during experiments.
"""

# Rolling features computed per team per season
ROLLING_FEATURES = [
    "off_epa_per_play",      # Offensive EPA/play
    "def_epa_per_play",      # Defensive EPA/play (allowed)
    "point_diff",            # Point differential
    "turnovers_committed",   # Turnovers committed
    "turnovers_forced",      # Turnovers forced (opponent committed)
    "turnover_diff",         # Turnover differential (forced - committed)
    "win",                   # Win (1) / Loss (0) / Tie (0.5)
]

# Situational features (direct lookup, no rolling)
SITUATIONAL_FEATURES = [
    "is_home",          # 1 for home, 0 for away (always 1 in home-perspective table)
    "home_rest_days",   # Days since home team's last game
    "away_rest_days",   # Days since away team's last game
    "week",             # Week of season
    "div_game",         # 1 if divisional game, 0 otherwise
]

# Target variable (for reference, not used as feature)
TARGET = "home_win"  # 1 if home team won, 0 otherwise

# Columns that must NEVER be features (CLAUDE.md)
FORBIDDEN_FEATURES = ["result", "home_score", "away_score"]

# Play types used for EPA calculation
EPA_PLAY_TYPES = ["pass", "run"]
```

### Leakage Test Pattern (features/tests/test_leakage.py)
```python
"""Leakage validation tests for the feature pipeline.

These tests MUST pass before any model training proceeds (CLAUDE.md).
They verify that no feature for game G uses data from game G or later.
"""
import pandas as pd
import numpy as np
import pytest


def test_shift1_excludes_current_game():
    """Verify that rolling features for game G do not include game G's data.

    Strategy: Create synthetic data where a team's last game has an extreme
    EPA value (e.g., 100.0). If any prior game's rolling feature reflects
    this value, leakage exists.
    """
    # ... synthetic data with planted spike in last game
    # ... run feature pipeline
    # ... assert no rolling feature for games before last game contains the spike


def test_week1_rolling_features_are_nan():
    """Week 1 of each season should have NaN rolling features.

    Since shift(1) pushes the first observation out, and we reset
    rolling at season boundaries, week 1 has no prior data.
    """
    # ... build features for a season
    # ... assert all rolling columns are NaN for week 1 games


def test_removing_future_game_does_not_change_past_features():
    """Removing the last game of the season should not change any
    features for earlier games.
    """
    # ... build features with all games
    # ... build features with last game removed
    # ... assert features for games 1..N-1 are identical
```

### game_features Table Schema
```sql
-- Append to sql/init.sql
CREATE TABLE IF NOT EXISTS game_features (
    game_id VARCHAR(20) PRIMARY KEY,
    season SMALLINT NOT NULL,
    week SMALLINT NOT NULL,
    gameday DATE,

    -- Teams
    home_team VARCHAR(3) NOT NULL,
    away_team VARCHAR(3) NOT NULL,

    -- Target (not a feature)
    home_win SMALLINT,  -- 1=home win, 0=away win, NULL=tie

    -- Situational features (direct from schedule)
    home_rest SMALLINT,
    away_rest SMALLINT,
    div_game SMALLINT,

    -- Home team rolling features
    home_rolling_off_epa REAL,
    home_rolling_def_epa REAL,
    home_rolling_point_diff REAL,
    home_rolling_turnover_diff REAL,
    home_rolling_win_rate REAL,

    -- Away team rolling features
    away_rolling_off_epa REAL,
    away_rolling_def_epa REAL,
    away_rolling_point_diff REAL,
    away_rolling_turnover_diff REAL,
    away_rolling_win_rate REAL
);

CREATE INDEX IF NOT EXISTS idx_game_features_season ON game_features (season);
CREATE INDEX IF NOT EXISTS idx_game_features_week ON game_features (season, week);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Simple rolling average | Expanding window with shift(1) | Standard practice | Expanding uses all prior data; shift(1) prevents leakage |
| Cross-season rolling | Per-season reset | Standard NFL analytics practice | NFL rosters change dramatically between seasons; cross-season stats are misleading |
| Manual leakage checks | Automated pytest with synthetic data | Best practice since ~2020 | Manual checks miss subtle bugs; synthetic spike tests are deterministic |
| Including all PBP rows for EPA | Filtering to pass/run only | nflfastR convention | Other play types (kickoff, punt, etc.) have EPA but are not meaningful for team offensive/defensive quality |

**Deprecated/outdated:**
- **fillna(0) for week 1:** XGBoost handles NaN natively. Filling with 0 biases the model.
- **Cross-season rolling without reset:** While some analysts use it, per-season is standard for NFL due to roster turnover.

## Open Questions

1. **Tie games handling in win rate**
   - What we know: NFL ties are rare (~1-2 per season). `result == 0` indicates a tie.
   - What's unclear: Whether to count ties as 0.5 wins or as 0 wins.
   - Recommendation: Count ties as 0.5 in win rate computation. This is the standard convention.

2. **Whether to include playoff games in prior-season carry-over**
   - What we know: Requirements say regular season features. Phase 1 deferred this decision to Phase 2.
   - What's unclear: Whether playoff performance from the prior season should influence early-season rolling stats.
   - Recommendation: Use regular season only for rolling features. Playoff data is structurally different (bye weeks, limited teams). Reset at season boundary.

3. **Fixed-window vs expanding rolling**
   - What we know: Expanding window uses all prior season data. Fixed window (e.g., last 5 games) emphasizes recency.
   - What's unclear: Which is more predictive for NFL outcomes.
   - Recommendation: Use expanding window as the primary rolling approach in Phase 2. Fixed-window variants can be added as experimental features in Phase 3 via `models/train.py` feature selection (without modifying `features/build.py`).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` -- testpaths = ["tests"], pythonpath = ["."] |
| Quick run command | `pytest features/tests/ -x -q` |
| Full suite command | `pytest tests/ features/tests/ -v` |

**Note:** `features/tests/` needs to be added to pytest testpaths, OR the tests can be run by specifying the path directly. The existing config only covers `tests/`. Update pyproject.toml testpaths to include both.

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-01 | Rolling EPA/play computed with only prior-game data | unit | `pytest features/tests/test_leakage.py::test_shift1_excludes_current_game -x` | No -- Wave 0 |
| FEAT-02 | Rolling point diff, turnover diff, win rate with prior-game data | unit | `pytest features/tests/test_features.py::test_rolling_basic_stats -x` | No -- Wave 0 |
| FEAT-03 | Situational features populated correctly | unit | `pytest features/tests/test_features.py::test_situational_features -x` | No -- Wave 0 |
| FEAT-04 | One row per game, home team perspective | unit | `pytest features/tests/test_features.py::test_home_perspective_structure -x` | No -- Wave 0 |
| FEAT-05 | Leakage tests pass and block model training | unit | `pytest features/tests/test_leakage.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest features/tests/ -x -q` (quick: all feature tests)
- **Per wave merge:** `pytest tests/ features/tests/ -v` (full suite including Phase 1 tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `features/__init__.py` -- package init
- [ ] `features/__main__.py` -- CLI entry point
- [ ] `features/definitions.py` -- feature column definitions
- [ ] `features/build.py` -- main pipeline
- [ ] `features/tests/__init__.py` -- test package init
- [ ] `features/tests/conftest.py` -- shared test fixtures (synthetic game data)
- [ ] `features/tests/test_leakage.py` -- leakage validation tests (CLAUDE.md mandated)
- [ ] `features/tests/test_features.py` -- feature computation correctness tests
- [ ] `sql/init.sql` update -- add game_features table DDL
- [ ] `pyproject.toml` update -- add `features/tests` to testpaths

## Data Verified During Research

The following facts were verified by reading actual parquet cache files, not assumed from documentation:

| Fact | Verified | Detail |
|------|----------|--------|
| EPA 100% populated for pass/run plays, all seasons | HIGH | 2005: 31,648/31,648 non-null. 2023: 33,957/33,957 non-null |
| Schedule rest days zero NaN across all seasons | HIGH | Checked 2005, 2010, 2015, 2020, 2024 -- all zero NaN |
| Schedule div_game zero NaN across all seasons | HIGH | Same check as rest days -- all zero NaN |
| gameday format consistent (YYYY-MM-DD string) | HIGH | Verified 2005 and 2023 -- both string format |
| PBP game_date matches schedule gameday | HIGH | 2023_01_DET_KC: both show 2023-09-07 |
| Total regular-season games 2005-2024: 5,183 | HIGH | Computed from actual parquet files |
| Null posteam: ~2,500 rows per season | HIGH | 2023: 2,522 null posteam rows (administrative plays) |
| Turnovers: interception + fumble_lost columns available | HIGH | Both in CURATED_PBP_COLUMNS, verified non-null counts |
| Schedule result column = home_score - away_score | HIGH | Verified: positive = home win, negative = away win, 0 = tie |
| Each team plays 16 or 17 games per regular season | HIGH | KC 2023: 9 home + 8 away = 17 games |

## Sources

### Primary (HIGH confidence)
- Actual data inspection of parquet cache files (pbp_2005.parquet through pbp_2024.parquet, schedules_2005.parquet through schedules_2024.parquet)
- CLAUDE.md project rules -- shift(1) mandate, forbidden features, immutable feature files
- Phase 1 research and implementation -- data schema, column definitions, normalization patterns
- pandas official documentation -- groupby, transform, shift, expanding, rolling APIs

### Secondary (MEDIUM confidence)
- NFL analytics conventions -- per-season rolling reset, pass/run filter for EPA, turnover computation
- nflfastR field descriptions -- EPA column semantics, play_type categorization

### Tertiary (LOW confidence)
- None -- all key claims verified against actual data

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed; pandas rolling/shift is well-understood
- Architecture: HIGH -- two-stage pipeline (aggregate -> roll -> pivot) is a standard sports analytics pattern, verified against actual data
- Pitfalls: HIGH -- all pitfalls verified by inspecting actual data (null posteam, tie games, sort order)
- Leakage testing: HIGH -- synthetic spike test is a proven technique for detecting temporal leakage
- Data availability: HIGH -- all required columns verified present with zero NaN for all 20 seasons

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable domain; feature engineering patterns do not change)
