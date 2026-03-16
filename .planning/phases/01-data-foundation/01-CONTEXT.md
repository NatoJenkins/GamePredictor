# Phase 1: Data Foundation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Ingest and validate 20 seasons (2005-2024) of NFL play-by-play and schedule data into PostgreSQL with normalized team abbreviations and validated completeness. This phase delivers raw data tables ready for feature engineering in Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Ingestion behavior
- Upsert strategy on re-runs — insert new rows, update existing. No drop & recreate
- CLI supports both modes: default loads all 2005-2024, `--seasons 2023 2024` narrows to specific seasons
- Raw CSV downloads cached locally in `data/cache/` (gitignored) to avoid re-downloading on re-runs
- Curated column subset for raw_pbp: ~30-40 columns needed for feature engineering (EPA, play type, yards, down, distance, posteam, defteam, game_id, season, week, game_date, score differential, turnover flags, etc.) — NOT the full 300+ columns from nfl-data-py
- Team abbreviation normalization (TEAM_ABBREV_MAP: OAK->LV, SD->LAC, STL->LA, WSH->WAS) applied at ingestion before any row touches Postgres — this is an ingestion responsibility, not feature engineering
- Hardcoded expected game counts for validation: 256 games for 2005-2020, 272 for 2021-2024. Do not rely on nfl-data-py to determine season completeness

### Validation reporting
- Stdout summary printed during run: per-season table showing expected vs actual game counts and status
- `ingestion_log` table in Postgres for queryable history — one row per season per table type (pbp and schedule tracked separately)
- On validation failure: finish ingesting all seasons, then exit with error code. Show the full picture before failing
- Schema drift: hard fail if any curated columns are missing from nfl-data-py source. Extra columns in source silently ignored

### Data scope
- Regular season AND playoff games ingested — playoffs flagged with a boolean, not filtered out
- Preseason data excluded — filtered out before storing
- `games_in_season` metadata column stored so downstream code can adjust for the 16-to-17 game expansion in 2021
- 2020 COVID season: no special handling. Treated as normal 256-game season

### Dev environment
- PostgreSQL runs in Docker from day one (`docker compose up postgres`). No local install
- Database connection config via `.env` file (gitignored) with `DATABASE_URL`. `.env.example` checked into repo with placeholder values and comments
- Quick-load mode for development: `--seasons 2023 2024` loads 1-2 seasons for fast iteration. Full 20-season load for integration testing

### Claude's Discretion
- PostgreSQL table schema design (column types, indexes, constraints)
- Ingestion script internal architecture (modules, error handling patterns)
- Network failure retry strategy for nfl-data-py downloads
- Exact curated column list (within the ~30-40 scope described above)
- Docker Compose service configuration details

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project specs
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-04 define ingestion requirements
- `.planning/PROJECT.md` — Team normalization constraint, temporal split, stack decisions
- `CLAUDE.md` — Critical rules: team abbreviation constants mapping in data/sources.py, never use result/home_score/away_score as features

### Data source
- nfl-data-py PyPI package — primary data source for play-by-play and schedule data (verify column schema at research time)
- **NOTE (from research):** nfl-data-py was archived Sep 2025. Research recommends nflreadpy as replacement (returns Polars, needs `.to_pandas()`). Plans use nflreadpy — executor MUST verify `pip install nflreadpy` works and API matches before the 20-season load. If nflreadpy fails, fall back to nfl-data-py.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code — greenfield project. Phase 1 establishes the foundation

### Established Patterns
- None yet. This phase sets the patterns for data layer code

### Integration Points
- Phase 2 (Feature Engineering) will read from the PostgreSQL tables created here
- `data/sources.py` will contain TEAM_ABBREV_MAP constant (per CLAUDE.md)
- `data/cache/` directory for cached CSV downloads

</code_context>

<specifics>
## Specific Ideas

- Include `location` field in curated PBP columns — needed by Phase 2 for international game detection (London, Mexico City) which affects rest days features
- The `ingestion_log` table serves double duty: validation reporting AND debugging aid when feature engineering finds unexpected data weeks later
- Quick-load mode (`--seasons`) doubles as the mechanism for weekly pipeline updates in Phase 6

</specifics>

<deferred>
## Deferred Ideas

- International game flagging (London, Mexico City) for rest/travel feature adjustments — Phase 2 feature engineering concern, not ingestion
- Playoff game features (different dynamics, bye weeks) — Phase 2 MUST filter to `game_type == 'REG'` before computing rolling features. Playoff games are stored but must not pollute rolling stats
- Phase 2 MUST exclude `total_home_score`, `total_away_score`, `home_score`, `away_score`, `result` from the feature matrix per CLAUDE.md. These are stored in Phase 1 for target variable construction and validation only

</deferred>

---

*Phase: 01-data-foundation*
*Context gathered: 2026-03-16*
