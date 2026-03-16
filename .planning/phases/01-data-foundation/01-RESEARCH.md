# Phase 1: Data Foundation - Research

**Researched:** 2026-03-16
**Domain:** NFL data ingestion, PostgreSQL storage, Python data pipeline
**Confidence:** HIGH

## Summary

Phase 1 requires ingesting 20 seasons (2005-2024) of NFL play-by-play and schedule data into PostgreSQL with normalized team abbreviations and validation. The primary data source specified in project docs is nfl-data-py, but this package was **archived on Sep 25, 2025** and replaced by **nflreadpy** (v0.1.5). Research recommends using nflreadpy as the data source library.

The data comes from the nflverse ecosystem, which provides ~370 columns of play-by-play data per season and 46 columns of schedule data. Only ~30-40 PBP columns are needed (per CONTEXT.md). PostgreSQL runs in Docker, and SQLAlchemy 2.0 with psycopg provides the upsert pattern needed for idempotent re-runs.

**Primary recommendation:** Use nflreadpy (successor to nfl-data-py) with SQLAlchemy 2.0 + psycopg for PostgreSQL upserts. Cache raw downloads as Parquet in data/cache/. Validate against hardcoded game counts (256 for 2005-2020, 272 for 2021-2024).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Upsert strategy on re-runs -- insert new rows, update existing. No drop & recreate
- CLI supports both modes: default loads all 2005-2024, `--seasons 2023 2024` narrows to specific seasons
- Raw CSV downloads cached locally in `data/cache/` (gitignored) to avoid re-downloading on re-runs
- Curated column subset for raw_pbp: ~30-40 columns needed for feature engineering (EPA, play type, yards, down, distance, posteam, defteam, game_id, season, week, game_date, score differential, turnover flags, etc.) -- NOT the full 300+ columns from nfl-data-py
- Team abbreviation normalization (TEAM_ABBREV_MAP: OAK->LV, SD->LAC, STL->LA, WSH->WAS) applied at ingestion before any row touches Postgres -- this is an ingestion responsibility, not feature engineering
- Hardcoded expected game counts for validation: 256 games for 2005-2020, 272 for 2021-2024. Do not rely on nfl-data-py to determine season completeness
- Stdout summary printed during run: per-season table showing expected vs actual game counts and status
- `ingestion_log` table in Postgres for queryable history -- one row per season per table type (pbp and schedule tracked separately)
- On validation failure: finish ingesting all seasons, then exit with error code. Show the full picture before failing
- Schema drift: hard fail if any curated columns are missing from nfl-data-py source. Extra columns in source silently ignored
- Regular season AND playoff games ingested -- playoffs flagged with a boolean, not filtered out
- Preseason data excluded -- filtered out before storing
- `games_in_season` metadata column stored so downstream code can adjust for the 16-to-17 game expansion in 2021
- 2020 COVID season: no special handling. Treated as normal 256-game season
- PostgreSQL runs in Docker from day one (`docker compose up postgres`). No local install
- Database connection config via `.env` file (gitignored) with `DATABASE_URL`. `.env.example` checked into repo with placeholder values and comments
- Quick-load mode for development: `--seasons 2023 2024` loads 1-2 seasons for fast iteration. Full 20-season load for integration testing

### Claude's Discretion
- PostgreSQL table schema design (column types, indexes, constraints)
- Ingestion script internal architecture (modules, error handling patterns)
- Network failure retry strategy for nfl-data-py downloads
- Exact curated column list (within the ~30-40 scope described above)
- Docker Compose service configuration details

### Deferred Ideas (OUT OF SCOPE)
- International game flagging (London, Mexico City) for rest/travel feature adjustments -- Phase 2 feature engineering concern, not ingestion
- Playoff game features (different dynamics, bye weeks) -- Phase 2 can decide whether to include/exclude playoff data in rolling stats

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | System ingests all regular season play-by-play data (2005-2024) from nfl-data-py into PostgreSQL | nflreadpy `load_pbp()` returns Polars DataFrame with ~370 columns per season; curated subset stored in `raw_pbp` table |
| DATA-02 | System ingests game schedule/metadata (dates, home/away, final scores, week numbers) for all seasons 2005-2024 | nflreadpy `load_schedules()` returns 46-column DataFrame with game_id, gameday, home/away teams, scores, week, game_type |
| DATA-03 | Team abbreviations normalized at ingestion via defined constants mapping | TEAM_ABBREV_MAP in data/sources.py covers OAK->LV, SD->LAC, STL->LA, WSH->WAS; applied to all team columns before insert |
| DATA-04 | Ingestion validates row counts, season completeness, and schema drift | Hardcoded game counts (256/272), column presence checks, ingestion_log table for audit trail |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nflreadpy | 0.1.5 | NFL data download (PBP + schedules) | Official successor to nfl-data-py (archived Sep 2025); maintained by nflverse |
| SQLAlchemy | 2.0+ | Database ORM and connection management | Industry standard; provides PostgreSQL-specific upsert via `on_conflict_do_update` |
| psycopg | 3.x (psycopg[binary]) | PostgreSQL driver | Modern async-capable driver; recommended for SQLAlchemy 2.0 |
| polars | latest | DataFrame library (nflreadpy default) | nflreadpy returns Polars DataFrames; convert to pandas for to_sql or use directly |
| pandas | 2.x | DataFrame manipulation and SQL I/O | `to_sql()` integration with SQLAlchemy for bulk inserts |
| python-dotenv | latest | .env file loading | Load DATABASE_URL from .env |
| click | latest | CLI framework | Lightweight, supports `--seasons` argument parsing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | latest | Retry logic for network calls | Wrap nflreadpy download calls with exponential backoff |
| docker (compose) | latest | PostgreSQL container | `docker compose up postgres` for local dev |
| alembic | latest | Database migrations | Optional -- may be overkill for 3 tables; raw SQL init script is simpler |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| nflreadpy | nfl-data-py (archived) | nfl-data-py still installable but receives no updates; nflreadpy is actively maintained |
| SQLAlchemy upsert | pangres | pangres simplifies upserts but adds a dependency; SQLAlchemy native is sufficient |
| alembic | Raw SQL init script | For 3 static tables, a SQL init script is simpler; alembic adds migration overhead |
| click | argparse | argparse is stdlib but click has cleaner multi-option handling |

**Installation:**
```bash
pip install nflreadpy sqlalchemy "psycopg[binary]" pandas polars python-dotenv click tenacity
```

## Architecture Patterns

### Recommended Project Structure
```
data/
  sources.py           # TEAM_ABBREV_MAP constant, column lists, game count expectations
  ingest.py            # CLI entry point: click-based script
  db.py                # SQLAlchemy engine/session factory, table definitions
  loaders.py           # Functions: load_pbp_from_nflverse(), load_schedules_from_nflverse()
  transforms.py        # normalize_teams(), filter_preseason(), select_columns()
  validators.py        # validate_game_counts(), validate_schema(), validate_completeness()
  cache/               # Gitignored; cached Parquet files from nflreadpy
docker-compose.yml     # PostgreSQL service definition
.env.example           # DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/nflpredictor
.env                   # Gitignored; actual credentials
```

### Pattern 1: Upsert with SQLAlchemy 2.0
**What:** Use PostgreSQL ON CONFLICT DO UPDATE for idempotent inserts
**When to use:** Every ingestion run -- enables safe re-runs without data loss
**Example:**
```python
# Source: SQLAlchemy 2.0 PostgreSQL dialect docs
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine, Table, MetaData

engine = create_engine(DATABASE_URL)
metadata = MetaData()
raw_pbp = Table("raw_pbp", metadata, autoload_with=engine)

def upsert_dataframe(engine, table, df, conflict_columns):
    """Upsert a pandas DataFrame into a PostgreSQL table."""
    records = df.to_dict(orient="records")
    stmt = insert(table).values(records)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in table.columns
        if c.name not in conflict_columns
    }
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=update_cols,
    )
    with engine.begin() as conn:
        conn.execute(upsert_stmt)
```

### Pattern 2: Cache-Then-Transform Pipeline
**What:** Download raw data to local cache, then transform and load
**When to use:** Every ingestion run to avoid redundant downloads
**Example:**
```python
import nflreadpy as nfl
from pathlib import Path

CACHE_DIR = Path("data/cache")

def load_pbp_cached(season: int) -> pd.DataFrame:
    """Load PBP data, using local cache if available."""
    cache_path = CACHE_DIR / f"pbp_{season}.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    # nflreadpy returns Polars; convert to pandas
    df = nfl.load_pbp(season).to_pandas()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path)
    return df
```

### Pattern 3: Validate-After-Ingest
**What:** Ingest all seasons, collect validation results, report at end, exit with error code if any fail
**When to use:** Per CONTEXT.md decision -- show full picture before failing
**Example:**
```python
from dataclasses import dataclass

@dataclass
class ValidationResult:
    season: int
    table: str
    expected_games: int
    actual_games: int
    status: str  # "OK" or "MISMATCH"

def validate_season_counts(engine, results: list[ValidationResult]):
    """Print summary table and return True if all pass."""
    all_ok = True
    for r in results:
        icon = "OK" if r.status == "OK" else "FAIL"
        print(f"  {r.season} | {r.table:10s} | expected={r.expected_games} actual={r.actual_games} | {icon}")
        if r.status != "OK":
            all_ok = False
    return all_ok
```

### Anti-Patterns to Avoid
- **Drop-and-recreate on re-run:** CONTEXT.md explicitly requires upsert. Never truncate tables on re-run.
- **Downloading all 370 columns to Postgres:** Store only the curated ~30-40 columns. The full dataset is ~2GB per season.
- **Normalizing team names in feature engineering:** Normalization happens at ingestion. Downstream code assumes clean abbreviations.
- **Inline string replacements for teams:** CLAUDE.md mandates using the constants mapping in data/sources.py.
- **Silent validation failures:** Must exit with error code after showing all validation results.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| NFL data download | Custom scraper | nflreadpy | Handles nflverse CDN, caching, format changes |
| PostgreSQL upsert | Custom INSERT/UPDATE logic | SQLAlchemy `on_conflict_do_update` | Handles conflict resolution atomically |
| Network retry | Manual retry loops | tenacity decorator | Configurable backoff, jitter, max attempts |
| CLI argument parsing | sys.argv parsing | click | Type validation, help text, composable commands |
| .env loading | os.environ manual parse | python-dotenv | Standard .env format, gitignore-friendly |

**Key insight:** The nflverse ecosystem handles all data sourcing complexity. The ingestion script's job is to download, subset columns, normalize teams, validate, and store -- not to scrape or parse NFL data.

## Common Pitfalls

### Pitfall 1: nfl-data-py is Archived
**What goes wrong:** Using `nfl_data_py` which was archived Sep 2025 and receives no updates
**Why it happens:** Project docs reference nfl-data-py (written before archival)
**How to avoid:** Use nflreadpy instead. API is similar but returns Polars DataFrames (convert with `.to_pandas()`)
**Warning signs:** Import errors, missing seasons, stale data

### Pitfall 2: nflreadpy Returns Polars, Not Pandas
**What goes wrong:** Calling pandas methods on Polars DataFrames
**Why it happens:** nflreadpy uses Polars by default for performance
**How to avoid:** Call `.to_pandas()` immediately after loading, or work in Polars throughout
**Warning signs:** AttributeError on DataFrame operations

### Pitfall 3: Team Abbreviation Inconsistency Across Seasons
**What goes wrong:** OAK appears in 2005-2019 data, LV in 2020+. Same for SD/LAC, STL/LA, WSH/WAS
**Why it happens:** Teams relocated or rebranded at different points
**How to avoid:** Apply TEAM_ABBREV_MAP to ALL team columns (posteam, defteam, home_team, away_team) before storing
**Warning signs:** Duplicate teams in aggregations (e.g., both OAK and LV appearing)

### Pitfall 4: Season Type Filtering
**What goes wrong:** Including preseason data or accidentally excluding playoffs
**Why it happens:** PBP data includes all game types; schedule has game_type column
**How to avoid:** Filter on `season_type == 'REG'` or `game_type in ('REG', 'WC', 'DIV', 'CON', 'SB')` for PBP. Schedule uses `game_type` column. CONTEXT.md says include playoffs but exclude preseason.
**Warning signs:** Game counts don't match expectations

### Pitfall 5: Validation Game Counts Include Only Regular Season
**What goes wrong:** Comparing total games (including playoffs) against the 256/272 hardcoded counts
**Why it happens:** The expected counts (256 for 2005-2020, 272 for 2021-2024) are regular-season only
**How to avoid:** Validate regular season counts separately; ingest playoffs but don't count them toward the validation threshold
**Warning signs:** "Extra" games showing up in validation

### Pitfall 6: PBP game_id Format vs Schedule game_id
**What goes wrong:** Assuming game_id formats are identical between PBP and schedule tables
**Why it happens:** Both have game_id but format may differ slightly across sources
**How to avoid:** Verify game_id format from both `load_pbp()` and `load_schedules()` during development. PBP uses format like "2023_01_KC_DET"; schedule uses similar format.
**Warning signs:** JOINs between tables return zero rows

### Pitfall 7: Large Upsert Batch Size
**What goes wrong:** Trying to upsert millions of PBP rows in a single transaction
**Why it happens:** A single season can have 40,000-50,000 plays
**How to avoid:** Process one season at a time. Each season's PBP is a manageable batch (~50K rows)
**Warning signs:** Memory errors, long-running transactions, PostgreSQL OOM

## Code Examples

### Team Abbreviation Mapping (data/sources.py)
```python
# Source: CLAUDE.md mandates this constant in data/sources.py
TEAM_ABBREV_MAP = {
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LA",
    "WSH": "WAS",
}

def normalize_team_abbrev(abbrev: str) -> str:
    """Map historical team abbreviations to current canonical form."""
    return TEAM_ABBREV_MAP.get(abbrev, abbrev)
```

### Curated PBP Column List
```python
# Source: nflverse field descriptions + CONTEXT.md scope
# ~35 columns covering EPA, play type, yards, situation, teams, scoring
CURATED_PBP_COLUMNS = [
    # Identifiers
    "play_id", "game_id", "old_game_id", "season", "season_type", "week", "game_date",
    # Teams
    "home_team", "away_team", "posteam", "posteam_type", "defteam",
    # Situation
    "down", "ydstogo", "yardline_100", "quarter_seconds_remaining",
    "half_seconds_remaining", "game_seconds_remaining", "game_half",
    # Play details
    "play_type", "yards_gained", "rush_attempt", "pass_attempt",
    "complete_pass", "incomplete_pass", "interception", "fumble_lost",
    "sack", "touchdown", "safety",
    # EPA and advanced
    "epa", "wp", "wpa",
    # Score context
    "score_differential", "posteam_score", "defteam_score",
    "total_home_score", "total_away_score",
    # Location (needed for Phase 2 international game detection per CONTEXT.md specifics)
    "location",
]
```

### Schedule Table Curated Columns
```python
# Source: nflverse schedule data dictionary
CURATED_SCHEDULE_COLUMNS = [
    "game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
    "away_team", "away_score", "home_team", "home_score",
    "location", "result", "total", "overtime",
    "away_rest", "home_rest", "div_game",
    "roof", "surface",
]
```

### Expected Game Counts
```python
# Source: CONTEXT.md locked decision + NFL season structure
# 16-game season: 32 teams * 16 games / 2 (each game has 2 teams) = 256
# 17-game season: 32 teams * 17 games / 2 = 272
EXPECTED_REG_SEASON_GAMES = {
    year: 256 if year <= 2020 else 272
    for year in range(2005, 2025)
}
```

### Docker Compose PostgreSQL Service
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nflpredictor
      POSTGRES_USER: nfl
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-nfldev}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  pgdata:
```

### .env.example
```bash
# Database connection
DATABASE_URL=postgresql+psycopg://nfl:nfldev@localhost:5432/nflpredictor

# Postgres container credentials (match docker-compose.yml)
POSTGRES_PASSWORD=nfldev
```

### PostgreSQL Table Schema
```sql
-- sql/init.sql
CREATE TABLE IF NOT EXISTS raw_pbp (
    play_id INTEGER NOT NULL,
    game_id VARCHAR(20) NOT NULL,
    old_game_id VARCHAR(20),
    season SMALLINT NOT NULL,
    season_type VARCHAR(4) NOT NULL,
    week SMALLINT NOT NULL,
    game_date DATE,
    home_team VARCHAR(3) NOT NULL,
    away_team VARCHAR(3) NOT NULL,
    posteam VARCHAR(3),
    posteam_type VARCHAR(4),
    defteam VARCHAR(3),
    down SMALLINT,
    ydstogo SMALLINT,
    yardline_100 SMALLINT,
    quarter_seconds_remaining SMALLINT,
    half_seconds_remaining SMALLINT,
    game_seconds_remaining SMALLINT,
    game_half VARCHAR(10),
    play_type VARCHAR(20),
    yards_gained SMALLINT,
    rush_attempt SMALLINT,
    pass_attempt SMALLINT,
    complete_pass SMALLINT,
    incomplete_pass SMALLINT,
    interception SMALLINT,
    fumble_lost SMALLINT,
    sack SMALLINT,
    touchdown SMALLINT,
    safety SMALLINT,
    epa REAL,
    wp REAL,
    wpa REAL,
    score_differential SMALLINT,
    posteam_score SMALLINT,
    defteam_score SMALLINT,
    total_home_score SMALLINT,
    total_away_score SMALLINT,
    location VARCHAR(10),
    PRIMARY KEY (game_id, play_id)
);

CREATE TABLE IF NOT EXISTS schedules (
    game_id VARCHAR(20) PRIMARY KEY,
    season SMALLINT NOT NULL,
    game_type VARCHAR(4) NOT NULL,
    week SMALLINT NOT NULL,
    gameday DATE,
    weekday VARCHAR(10),
    gametime VARCHAR(5),
    away_team VARCHAR(3) NOT NULL,
    away_score SMALLINT,
    home_team VARCHAR(3) NOT NULL,
    home_score SMALLINT,
    location VARCHAR(10),
    result SMALLINT,
    total SMALLINT,
    overtime SMALLINT,
    away_rest SMALLINT,
    home_rest SMALLINT,
    div_game SMALLINT,
    roof VARCHAR(10),
    surface VARCHAR(20),
    games_in_season SMALLINT NOT NULL DEFAULT 16
);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id SERIAL PRIMARY KEY,
    season SMALLINT NOT NULL,
    table_name VARCHAR(20) NOT NULL,
    rows_inserted INTEGER NOT NULL,
    rows_updated INTEGER NOT NULL,
    expected_games INTEGER,
    actual_games INTEGER,
    status VARCHAR(20) NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (season, table_name, ingested_at)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_pbp_season ON raw_pbp (season);
CREATE INDEX IF NOT EXISTS idx_pbp_game_id ON raw_pbp (game_id);
CREATE INDEX IF NOT EXISTS idx_pbp_posteam ON raw_pbp (posteam);
CREATE INDEX IF NOT EXISTS idx_schedules_season ON schedules (season);
CREATE INDEX IF NOT EXISTS idx_schedules_game_type ON schedules (game_type);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nfl-data-py | nflreadpy | Sep 2025 | Must use nflreadpy; nfl-data-py archived, no updates |
| pandas-only DataFrames | Polars DataFrames (nflreadpy default) | 2025 | Need `.to_pandas()` conversion or Polars-native code |
| psycopg2 | psycopg 3.x | 2023+ | Modern driver, async support; SQLAlchemy 2.0 prefers it |
| SQLAlchemy 1.x execute | SQLAlchemy 2.0 connection context | 2023 | `engine.execute()` removed; must use `with engine.begin()` |

**Deprecated/outdated:**
- **nfl-data-py:** Archived Sep 25, 2025. Use nflreadpy instead. Project docs reference nfl-data-py but the package is unmaintained.
- **psycopg2:** Still works but psycopg 3.x is the modern replacement.
- **SQLAlchemy 1.x patterns:** `engine.execute()` removed in 2.0. Use `with engine.begin() as conn: conn.execute(...)`.

## Open Questions

1. **nflreadpy vs nfl-data-py in project references**
   - What we know: CONTEXT.md and REQUIREMENTS.md reference nfl-data-py. But nfl-data-py was archived Sep 2025 and replaced by nflreadpy.
   - What's unclear: Whether user is aware of the deprecation and wants to use nflreadpy instead
   - Recommendation: Use nflreadpy. The API is compatible (similar function names), and nfl-data-py will not receive updates. Code references in CLAUDE.md to "data/sources.py" are unaffected.

2. **Exact PBP column availability across all seasons (2005-2024)**
   - What we know: EPA columns exist from 2006+. Early seasons (1999-2005) may have incomplete EPA data.
   - What's unclear: Whether 2005 season has full EPA coverage
   - Recommendation: During implementation, load 2005 PBP and check for null EPA rates. If too high, document as known limitation.

3. **nflreadpy caching behavior**
   - What we know: nflreadpy has built-in "intelligent caching (memory or filesystem)". CONTEXT.md also specifies local caching in data/cache/.
   - What's unclear: Whether nflreadpy's built-in cache is sufficient or if we need explicit Parquet caching
   - Recommendation: Use explicit Parquet caching in data/cache/ as specified in CONTEXT.md. This gives full control over cache location and format, and survives process restarts.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (standard for Python projects) |
| Config file | None -- Wave 0 must create pytest.ini or pyproject.toml [tool.pytest] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | PBP data for 20 seasons ingested to PostgreSQL | integration | `pytest tests/test_ingestion.py::test_pbp_ingestion -x` | No -- Wave 0 |
| DATA-02 | Schedule data for 20 seasons ingested to PostgreSQL | integration | `pytest tests/test_ingestion.py::test_schedule_ingestion -x` | No -- Wave 0 |
| DATA-03 | Team abbreviations normalized via constants mapping | unit | `pytest tests/test_transforms.py::test_team_normalization -x` | No -- Wave 0 |
| DATA-04 | Validation surfaces errors for bad data | unit | `pytest tests/test_validators.py::test_validation_failures -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q` (quick: unit tests only)
- **Per wave merge:** `pytest tests/ -v` (full suite including integration if DB available)
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `pyproject.toml` -- project config with [tool.pytest] section
- [ ] `tests/__init__.py` -- test package init
- [ ] `tests/conftest.py` -- shared fixtures (test DB engine, sample DataFrames)
- [ ] `tests/test_transforms.py` -- team normalization, column selection, preseason filtering
- [ ] `tests/test_validators.py` -- game count validation, schema drift detection
- [ ] `tests/test_ingestion.py` -- integration tests (requires running PostgreSQL)
- [ ] Framework install: `pip install pytest` -- if not already in dependencies

## Sources

### Primary (HIGH confidence)
- [nflreadpy PyPI](https://pypi.org/project/nflreadpy/) -- v0.1.5, installation, API overview
- [nflreadpy docs](https://nflreadpy.nflverse.com/) -- load_pbp(), load_schedules() parameters and behavior
- [nflreadpy load functions API](https://nflreadpy.nflverse.com/api/load_functions/) -- function signatures and return types
- [nfl-data-py GitHub](https://github.com/nflverse/nfl_data_py) -- confirmed archived Sep 25, 2025; recommends nflreadpy
- [nflverse schedule data dictionary](https://raw.githubusercontent.com/nflverse/nflreadr/1f23027a27ec565f1272345a80a208b8f529f0fc/data-raw/dictionary_schedules.csv) -- complete 46-column schema
- [nflfastR field descriptions](https://nflfastr.com/reference/field_descriptions.html) -- PBP column definitions
- [SQLAlchemy 2.0 PostgreSQL docs](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) -- on_conflict_do_update pattern
- [NFL regular season Wikipedia](https://en.wikipedia.org/wiki/NFL_regular_season) -- 256 games (2005-2020), 272 games (2021+)

### Secondary (MEDIUM confidence)
- [nflreadr load_schedules R docs](https://nflreadr.nflverse.com/reference/load_schedules.html) -- column descriptions (R equivalent of Python API)

### Tertiary (LOW confidence)
- EPA column availability for 2005 season -- training data only, needs live verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- nflreadpy confirmed as replacement, SQLAlchemy 2.0 upsert well-documented
- Architecture: HIGH -- standard ETL pattern with clear module boundaries
- Pitfalls: HIGH -- nfl-data-py deprecation verified, team normalization well-understood
- Column lists: MEDIUM -- based on nflverse docs but exact availability per season needs live verification

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable domain; nflverse data format rarely changes mid-season)
