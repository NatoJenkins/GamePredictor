---
phase: 01-data-foundation
plan: 02
subsystem: database
tags: [nflreadpy, sqlalchemy, click, tenacity, parquet, upsert, ingestion]

# Dependency graph
requires:
  - "01-01: Project foundation (sources.py, transforms.py, validators.py, db.py, sql/init.sql)"
provides:
  - "data/loaders.py: cached nflreadpy download with tenacity retry"
  - "data/ingest.py: Click CLI for full ingestion pipeline with upsert"
  - "data/__main__.py: python -m data entry point"
  - "upsert_dataframe helper for PostgreSQL ON CONFLICT DO UPDATE"
  - "Ingestion logging to ingestion_log table"
  - "27 passing unit tests across all data modules"
affects: [02-feature-engineering]

# Tech tracking
tech-stack:
  added: []
  patterns: [parquet-caching, chunked-upsert, validate-after-ingest]

key-files:
  created:
    - data/loaders.py
    - data/ingest.py
    - data/__main__.py
    - tests/test_ingestion.py
  modified: []

key-decisions:
  - "Separated nflreadpy download into private retry-decorated functions for testability"
  - "Chunked upsert at 5000 rows to avoid memory issues with large PBP seasons"

patterns-established:
  - "Parquet caching in data/cache/ for network resilience"
  - "Click CLI with --seasons multiple option for selective ingestion"
  - "Validate-after-ingest: finish all seasons, then exit non-zero on mismatch"

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04]

# Metrics
duration: 4min
completed: 2026-03-16
---

# Phase 1 Plan 02: Ingestion Pipeline Summary

**Click CLI ingesting 20 seasons of PBP and schedule data via nflreadpy with Parquet caching, PostgreSQL upsert, team normalization, and post-ingest validation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-16T19:10:21Z
- **Completed:** 2026-03-16T19:14:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Cached data loaders with tenacity retry for network resilience
- Full ingestion CLI with --seasons support, chunked upsert, ingestion logging
- 7 unit tests + 3 integration tests covering upsert, CLI, normalization, filtering, validation
- All 27 unit tests pass across the full test suite

## Task Commits

Each task was committed atomically:

1. **Task 1: Data loaders with caching and ingestion CLI** - `348057a` (feat)
2. **Task 2: Integration tests for ingestion pipeline** - `84bc7e2` (test)

## Files Created/Modified
- `data/loaders.py` - Cached nflreadpy loading with tenacity retry (load_pbp_cached, load_schedules_cached)
- `data/ingest.py` - Click CLI: --seasons option, upsert to PostgreSQL, validation, ingestion logging
- `data/__main__.py` - Package entry point for python -m data invocation
- `tests/test_ingestion.py` - 7 unit tests + 3 integration tests (skipped without DATABASE_URL)

## Decisions Made
- Separated nflreadpy download calls into private retry-decorated functions (_download_pbp, _download_schedules) for clean testability
- Chunked upsert at 5000 rows per transaction to handle large PBP seasons without memory issues

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing Python dependencies**
- **Found during:** Task 1 (verification)
- **Issue:** tenacity, sqlalchemy, psycopg, python-dotenv not installed in environment
- **Fix:** pip install tenacity click sqlalchemy "psycopg[binary]" python-dotenv
- **Verification:** All imports succeed, CLI --help works
- **Committed in:** N/A (runtime dependency, already in pyproject.toml)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Dependency installation needed for verification. No scope creep.

## Issues Encountered
None beyond the dependency installation above.

## User Setup Required

Before running `python -m data`, the following must be set up:
- Docker: `docker compose up -d postgres` to start PostgreSQL
- Environment: Copy `.env.example` to `.env` (default values work for local Docker)

## Next Phase Readiness
- Ingestion pipeline complete, ready for Phase 2 (Feature Engineering)
- Run `python -m data --seasons 2023` to verify single-season load
- Run `python -m data` for full 20-season ingestion

## Self-Check: PASSED

- All 4 created files confirmed present on disk
- Both commit hashes (348057a, 84bc7e2) confirmed in git log
- All 27 unit tests pass

---
*Phase: 01-data-foundation*
*Completed: 2026-03-16*
