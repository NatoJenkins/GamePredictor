# Architecture Patterns

**Domain:** NFL game outcome prediction (ML pipeline + serving + dashboard)
**Researched:** 2026-03-15
**Confidence:** MEDIUM (based on established ML pipeline patterns and training knowledge of nfl-data-py; no live verification of current library APIs was possible)

## System Overview

The system is a classic **batch ML pipeline with an API serving layer**. There is no real-time inference -- games are predicted pre-kickoff and results are refreshed weekly. This simplifies the architecture considerably: no streaming, no low-latency model serving, no feature stores with real-time updates.

```
                          Weekly Refresh Trigger
                                  |
                                  v
  nfl-data-py -----> [Data Ingestion] -----> PostgreSQL
                                                 |
                                                 v
                                        [Feature Engineering]
                                         (no-leakage pipeline)
                                                 |
                                                 v
                                         Feature Tables (PG)
                                                 |
                          +----------------------+----------------------+
                          |                                             |
                          v                                             v
                 [Autoresearch Loop]                          [Prediction Service]
                 (experiment agent)                             (FastAPI)
                          |                                             |
                     +----+----+                                        v
                     |         |                                  [React Dashboard]
              experiments   MLflow                              (picks + scoreboard)
               .jsonl        UI
```

## Component Boundaries

### 1. Data Ingestion Pipeline (`data/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Fetch play-by-play and schedule data from nfl-data-py, normalize it, load into PostgreSQL |
| **Input** | nfl-data-py API calls (`import_pbp_data(years)`, `import_schedules(years)`) |
| **Output** | Populated `raw_pbp` and `raw_schedules` tables in PostgreSQL |
| **Communicates with** | nfl-data-py (external), PostgreSQL |
| **Boundary rule** | This component fetches and stores raw data ONLY. No feature computation here. |

**Key design decisions:**
- Store raw data in PostgreSQL rather than CSV/parquet files. Enables SQL-based feature engineering, handles the ~300+ columns in play-by-play data efficiently with proper indexing, and supports the weekly incremental refresh pattern.
- Use upsert logic (INSERT ON CONFLICT) so re-running ingestion is idempotent.
- The `raw_pbp` table will have ~700K rows per season (every play). Index on `(season, game_id, play_id)`.
- The `raw_schedules` table has ~285 rows per season (one per game). Index on `(season, game_id)`.

### 2. Feature Engineering Pipeline (`features/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Compute game-level features from raw play-by-play data with strict temporal ordering |
| **Input** | Raw tables in PostgreSQL |
| **Output** | `game_features` table -- one row per team-game with all engineered features |
| **Communicates with** | PostgreSQL (reads raw, writes features) |
| **Boundary rule** | NEVER reads future data. Every rolling computation uses `WHERE game_date < current_game_date` or equivalent window function with proper ordering. |

**No-leakage guarantees (critical):**

The single most dangerous part of the system. Leakage = using information from a game to predict that same game, or using future data to predict past games.

**Enforcement mechanisms:**
1. **SQL window functions with explicit ordering**: All rolling stats use `ROWS BETWEEN N PRECEDING AND 1 PRECEDING` (note: 1 PRECEDING, not CURRENT ROW).
2. **Temporal filter in every query**: Feature queries join on `season` and filter `week < target_week` (or `game_date < target_game_date` for cross-season).
3. **Validation test**: A dedicated test asserts that for every row in `game_features`, no input data point has a `game_date >= target_game_date`. Run this test in CI.
4. **Feature computation is game-by-game**: Process games in chronological order. For each game, compute features using only data from completed games.

**Feature categories (game-level, per team):**

| Category | Examples | Window |
|----------|----------|--------|
| Offensive efficiency | yards/play, pass rate, EPA/play (from pbp) | Rolling 4-8 games |
| Defensive efficiency | yards allowed/play, EPA allowed/play | Rolling 4-8 games |
| Situational | 3rd down conversion rate, red zone TD rate | Rolling 4-8 games |
| Strength of schedule | Opponent win% to date | Season-to-date |
| Rest/travel | Days since last game, time zone differential | Per-game |
| Home/away | Boolean home indicator | Per-game |
| Season momentum | Win streak, point differential trend | Season-to-date |

**Leakage test (pseudo-code):**
```python
def test_no_leakage():
    """For every game_features row, verify no source data is from on or after game date."""
    for row in game_features:
        source_games = get_source_games_for_feature_row(row)
        for sg in source_games:
            assert sg.game_date < row.game_date, (
                f"Leakage: feature for game {row.game_id} on {row.game_date} "
                f"used data from game {sg.game_id} on {sg.game_date}"
            )
```

### 3. Model Training + Autoresearch Experiment Loop (`models/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Train XGBoost classifier, run experiments, log results, keep/revert |
| **Input** | `game_features` table, `program.md` (experiment plan) |
| **Output** | Trained model artifact (pickle/joblib), `experiments.jsonl`, MLflow run |
| **Communicates with** | PostgreSQL (reads features), filesystem (model artifacts, experiments.jsonl), MLflow server |
| **Boundary rule** | Only modifies `models/train.py`. Never touches feature engineering or data ingestion code. |

**Temporal split (hardcoded):**
```python
TRAIN_SEASONS = range(2005, 2023)   # 2005-2022
VAL_SEASON = 2023                    # validation
TEST_SEASON = 2024                   # holdout, never touch until final eval
```

**Autoresearch loop pattern:**

This is the most novel part of the architecture. An AI agent (Claude) operates as an automated researcher:

```
Loop:
  1. Agent reads program.md (experiment backlog)
  2. Agent selects next experiment (e.g., "try adding EPA features")
  3. Agent modifies ONLY models/train.py
  4. Agent runs: python models/train.py
  5. train.py:
     a. Loads features from PostgreSQL
     b. Splits by temporal boundary
     c. Trains XGBoost with current config
     d. Evaluates on 2023 validation set
     e. Logs to experiments.jsonl:
        {"timestamp": "...", "experiment": "...", "val_accuracy": 0.57,
         "params": {...}, "features_used": [...], "notes": "..."}
     f. Logs to MLflow (same metrics + model artifact)
  6. Agent reads result
  7. If val_accuracy improved: KEEP changes to train.py
     If val_accuracy did not improve: REVERT train.py (git checkout)
  8. Agent updates program.md (mark experiment done, note result)
  9. Repeat
```

**Key constraints on the loop:**
- The agent ONLY modifies `models/train.py` -- never feature engineering code (that would break the leakage guarantees).
- Each experiment is atomic: one change, one run, one decision.
- `experiments.jsonl` is append-only. Never delete entries.
- The benchmark is 53% on 2023 validation accuracy specifically.

**experiments.jsonl schema:**
```json
{
  "id": "exp_001",
  "timestamp": "2026-03-15T10:30:00Z",
  "experiment_name": "baseline_win_pct_features",
  "description": "XGBoost with basic win%, points scored/allowed rolling 4 games",
  "val_accuracy_2023": 0.541,
  "val_log_loss_2023": 0.689,
  "train_accuracy": 0.612,
  "n_features": 12,
  "features_used": ["home", "rolling_win_pct_4", "rolling_pts_scored_4", "..."],
  "xgb_params": {"max_depth": 6, "learning_rate": 0.1, "n_estimators": 200},
  "kept": false,
  "notes": "Below 53% benchmark, revert"
}
```

### 4. Prediction Service (`api/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Serve predictions via REST API, load current model, return picks with confidence |
| **Input** | HTTP requests, loaded model artifact, current week's feature data |
| **Output** | JSON responses (predictions, historical accuracy, experiment history) |
| **Communicates with** | PostgreSQL (reads features + schedules), model artifacts (filesystem), React frontend |
| **Boundary rule** | Read-only. Never trains models or writes to feature tables. |

**API endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /api/predictions/current` | GET | This week's game predictions with confidence scores |
| `GET /api/predictions/history` | GET | Past predictions vs actual outcomes |
| `GET /api/model/info` | GET | Current model metadata (which experiment, accuracy) |
| `GET /api/experiments` | GET | Experiment history from experiments.jsonl |
| `GET /api/health` | GET | Service health check |

**Model loading pattern:**
- Load model artifact at startup (not per-request).
- Expose a `POST /api/model/reload` endpoint (protected) that reloads the model from disk after a new model is approved.
- The model file path is configured via environment variable `MODEL_PATH`.

**Confidence scores:**
- XGBoost outputs probabilities via `predict_proba()`.
- Confidence = the model's predicted probability for the favored team (e.g., 0.72 means 72% confidence).
- Display as: "Team A: 72% confidence" meaning the model gives Team A a 72% win probability.

### 5. React Dashboard (`frontend/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Display predictions, model performance, experiment history |
| **Input** | FastAPI endpoints (JSON) |
| **Output** | Rendered UI |
| **Communicates with** | FastAPI backend only (never PostgreSQL directly) |
| **Boundary rule** | Pure presentation layer. No business logic. |

**Views:**

1. **This Week's Picks** -- Card grid showing each game with predicted winner, confidence bar, team logos/names.
2. **Season Record** -- Running tally of correct/incorrect predictions with accuracy percentage.
3. **Experiment Scoreboard** -- Table of all experiments from experiments.jsonl, sorted by val_accuracy, showing which is currently deployed.
4. **Historical Predictions** -- Past weeks' predictions with actual outcomes (correct/incorrect badges).

### 6. Weekly Refresh Pipeline (`pipeline/`)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Orchestrate the weekly data refresh + optional retrain cycle |
| **Input** | Cron trigger (or manual) |
| **Output** | Updated data, new features, optionally a new model candidate |
| **Communicates with** | All other components (orchestrator) |
| **Boundary rule** | Orchestrates but does not contain business logic. Calls other components' scripts. |

**Weekly pipeline steps:**
```
1. Fetch new game results from nfl-data-py (data ingestion)
2. Update feature tables with new completed games (feature engineering)
3. Generate predictions for upcoming week using current model (prediction)
4. Optionally: retrain model with expanded data, compare to current model
5. If retrain: log experiment, present diff to operator for manual approval
6. Operator approves -> deploy new model; Operator rejects -> keep current
```

**Semi-automated pattern:**
- Steps 1-4 run automatically (cron or GitHub Actions).
- Step 5-6 require human approval. This can be a simple CLI prompt, a Slack notification, or a dashboard button.
- This prevents a bad model from auto-deploying during the season.

### 7. PostgreSQL Database

**Schema design:**

```sql
-- Raw data (populated by ingestion)
CREATE TABLE raw_pbp (
    play_id         BIGINT,
    game_id         VARCHAR(20),
    season          INT,
    week            INT,
    game_date       DATE,
    posteam         VARCHAR(5),    -- team with possession
    defteam         VARCHAR(5),
    play_type       VARCHAR(20),
    yards_gained    INT,
    epa             FLOAT,         -- expected points added
    -- ... ~300+ columns from nfl-data-py
    PRIMARY KEY (game_id, play_id)
);

CREATE INDEX idx_pbp_season_week ON raw_pbp(season, week);
CREATE INDEX idx_pbp_game_date ON raw_pbp(game_date);
CREATE INDEX idx_pbp_posteam ON raw_pbp(posteam, season);

CREATE TABLE raw_schedules (
    game_id         VARCHAR(20) PRIMARY KEY,
    season          INT,
    week            INT,
    game_date       DATE,
    home_team       VARCHAR(5),
    away_team       VARCHAR(5),
    home_score      INT,
    away_score      INT,
    result          INT,           -- home point differential
    -- ... additional schedule columns
);

CREATE INDEX idx_sched_season ON raw_schedules(season, week);

-- Engineered features (populated by feature pipeline)
CREATE TABLE game_features (
    game_id             VARCHAR(20),
    team                VARCHAR(5),
    opponent            VARCHAR(5),
    season              INT,
    week                INT,
    game_date           DATE,
    is_home             BOOLEAN,
    -- Rolling offensive features
    rolling_epa_play_4g FLOAT,
    rolling_pass_rate_4g FLOAT,
    rolling_yds_play_4g FLOAT,
    -- Rolling defensive features
    rolling_epa_allowed_4g FLOAT,
    rolling_yds_allowed_4g FLOAT,
    -- Situational
    rolling_3rd_conv_4g FLOAT,
    rolling_rz_td_rate_4g FLOAT,
    -- Contextual
    days_rest           INT,
    win_streak          INT,
    season_win_pct      FLOAT,
    opp_season_win_pct  FLOAT,
    -- Target
    won                 BOOLEAN,
    PRIMARY KEY (game_id, team)
);

CREATE INDEX idx_gf_season ON game_features(season, week);
CREATE INDEX idx_gf_team ON game_features(team, season);

-- Predictions (written by prediction service)
CREATE TABLE predictions (
    game_id         VARCHAR(20),
    season          INT,
    week            INT,
    predicted_winner VARCHAR(5),
    confidence      FLOAT,
    model_id        VARCHAR(50),
    predicted_at    TIMESTAMP DEFAULT NOW(),
    actual_winner   VARCHAR(5),    -- filled in after game
    correct         BOOLEAN,       -- filled in after game
    PRIMARY KEY (game_id, model_id)
);
```

**Schema notes:**
- `game_features` has TWO rows per game (one per team). This mirrors how the model sees data -- each row is "will THIS team win THIS game?"
- `raw_pbp` is large (~14M rows for 2005-2024). Partition by season for query performance if needed.
- `predictions` tracks every prediction made by every model version, enabling the scoreboard view.

## Data Flow

### Training-time data flow

```
nfl-data-py API
      |
      v
[data/ingest.py]  --- raw play-by-play + schedules ---> PostgreSQL (raw_pbp, raw_schedules)
      |
      v
[features/build.py] --- reads raw tables, computes rolling stats ---> PostgreSQL (game_features)
      |
      v
[models/train.py] --- reads game_features WHERE season IN train_seasons ---> XGBoost model
      |
      +---> model artifact (models/artifacts/model_v{N}.pkl)
      +---> experiments.jsonl (append)
      +---> MLflow (log run)
```

### Serving-time data flow

```
[pipeline/refresh.py] --- fetches new data ---> PostgreSQL (updated raw + features)
      |
      v
[api/main.py] --- loads model artifact + reads game_features for upcoming week
      |
      v
Model.predict_proba(upcoming_game_features) ---> prediction + confidence
      |
      v
[api/main.py] --- writes to predictions table + returns JSON
      |
      v
[frontend/] --- fetches /api/predictions/current ---> renders dashboard
```

### Weekly refresh data flow

```
Cron (Tuesday after games)
      |
      v
1. python data/ingest.py --update      # fetch latest results
2. python features/build.py --update   # recompute features for new games
3. python api/predict_week.py          # generate predictions for next week
4. (optional) python models/train.py   # retrain with expanded data
5. Human reviews retrain result        # approve or reject
```

## Patterns to Follow

### Pattern 1: Temporal Isolation via Configuration

All temporal boundaries live in ONE configuration file. No magic numbers scattered through code.

```python
# config.py
TEMPORAL_CONFIG = {
    "train_seasons": list(range(2005, 2023)),  # 2005-2022
    "val_season": 2023,
    "test_season": 2024,
    "feature_windows": [4, 8],  # rolling game windows
}
```

**Why:** Prevents accidental leakage from a stale hardcoded year in one file. Single source of truth.

### Pattern 2: Append-Only Experiment Log

`experiments.jsonl` is append-only. Each line is a self-contained JSON record. Never edit or delete.

**Why:** Provides a complete audit trail. The autoresearch loop agent can read the full history to avoid repeating experiments. The dashboard reads it to show the scoreboard. Git history is a backup but the file itself is the primary record.

### Pattern 3: Model Artifact Versioning

Models are saved as `model_v{experiment_id}.pkl`. The "current" model is a symlink or config pointer, not a filename convention.

```python
# config.py or .env
CURRENT_MODEL = "models/artifacts/model_exp_012.pkl"
```

**Why:** Multiple model versions coexist. Rollback is changing a pointer, not restoring from backup.

### Pattern 4: Feature-as-View Pattern

Consider implementing features as SQL views or materialized views over raw data. This makes the feature computation transparent and auditable.

```sql
CREATE MATERIALIZED VIEW mv_rolling_offense AS
SELECT
    g.game_id,
    g.team,
    AVG(prev.epa_play) AS rolling_epa_4g
FROM game_schedule g
JOIN game_stats prev ON prev.team = g.team
    AND prev.game_date < g.game_date
    AND prev.game_date >= (
        SELECT game_date FROM game_schedule
        WHERE team = g.team AND game_date < g.game_date
        ORDER BY game_date DESC OFFSET 3 LIMIT 1
    )
GROUP BY g.game_id, g.team;
```

**Why:** SQL views are declarative and auditable. The temporal constraint (`prev.game_date < g.game_date`) is visible in the view definition.

**Tradeoff:** Complex rolling windows may be easier in pandas. Use SQL for simple aggregates, pandas for complex multi-step feature engineering. But always apply the temporal filter at the SQL level when reading raw data.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Feature Engineering in the Training Script

**What:** Computing features inside `models/train.py` rather than in a separate pipeline.
**Why bad:** The autoresearch loop modifies `train.py`. If feature engineering lives there, the agent might accidentally introduce leakage. Feature engineering must be a separate, stable pipeline that the experiment loop never touches.
**Instead:** Feature engineering happens in `features/build.py` and writes to `game_features`. The training script only reads from `game_features`.

### Anti-Pattern 2: Using pandas groupby Without Temporal Guards

**What:** `df.groupby('team').rolling(4).mean()` without ensuring the rolling window respects game chronology.
**Why bad:** Pandas rolling on a grouped DataFrame will roll over whatever rows are present. If the DataFrame contains future games (e.g., loaded the full 2023 season), rolling stats will leak.
**Instead:** Sort by date, iterate game-by-game, and compute features using only `df[df['game_date'] < current_game_date]`.

### Anti-Pattern 3: Shuffled Train/Test Split

**What:** Using `train_test_split(X, y, test_size=0.2, random_state=42)`.
**Why bad:** Random splitting mixes 2023 games into training and 2019 games into validation. This inflates accuracy because the model can "learn" season-specific patterns.
**Instead:** Strict temporal split. All 2005-2022 games train, all 2023 games validate. No exceptions.

### Anti-Pattern 4: Auto-deploying Retrained Models

**What:** Pipeline automatically replaces the live model with a retrained version.
**Why bad:** A bad retrain (overfitting, data issue) goes live without review. During the NFL season, a bad model means wrong predictions published for a week.
**Instead:** Semi-automated: retrain runs automatically, but deployment requires manual approval (checking val metrics).

## Suggested Build Order

Components must be built in dependency order. Each phase should produce a testable, runnable artifact.

### Phase 1: Data Foundation
**Build:** Data ingestion + PostgreSQL schema + raw data loading
**Why first:** Everything else depends on having data in the database.
**Deliverable:** `python data/ingest.py` populates `raw_pbp` and `raw_schedules` for 2005-2024.
**Test:** Query counts match expected (~285 games/season, ~700K plays/season).

### Phase 2: Feature Engineering Pipeline
**Build:** Feature computation with no-leakage guarantees
**Why second:** Model training requires features. This is the hardest component to get right.
**Deliverable:** `python features/build.py` populates `game_features` with one row per team-game.
**Test:** Leakage test passes. Feature values are reasonable (no future data contamination).

### Phase 3: Model Training + Experiment Loop
**Build:** XGBoost training script, experiments.jsonl logging, MLflow integration, program.md, autoresearch loop infrastructure
**Why third:** Requires features to be available. This is where the 53% benchmark gets tackled.
**Deliverable:** Run N experiments via the autoresearch loop, achieve >53% on 2023 validation.
**Test:** experiments.jsonl has entries, MLflow shows runs, best model beats benchmark.

### Phase 4: API Serving Layer
**Build:** FastAPI app, model loading, prediction endpoints
**Why fourth:** Requires a trained model to serve.
**Deliverable:** `uvicorn api.main:app` serves predictions at localhost:8000.
**Test:** `/api/predictions/current` returns valid JSON with predictions.

### Phase 5: React Dashboard
**Build:** React frontend consuming FastAPI endpoints
**Why fifth:** Requires API to be running. Pure presentation, no business logic.
**Deliverable:** Dashboard shows this week's picks and experiment scoreboard.
**Test:** Visual inspection, all views render correctly.

### Phase 6: Weekly Pipeline + Docker Deployment
**Build:** Refresh pipeline orchestration, Docker Compose, deployment
**Why last:** All components must exist before orchestrating them. Docker wraps everything.
**Deliverable:** `docker compose up` runs the full stack. Weekly refresh works end-to-end.
**Test:** Simulated weekly refresh cycle completes successfully.

## Directory Structure

```
GamePredictor/
  .planning/              # Project planning files
  data/
    ingest.py             # Fetch and load raw data
    sources.py            # nfl-data-py wrapper
  features/
    build.py              # Feature engineering pipeline
    definitions.py        # Feature definitions and SQL/pandas logic
    tests/
      test_leakage.py     # No-leakage validation tests
  models/
    train.py              # Training script (modified by autoresearch loop)
    artifacts/            # Saved model files
    program.md            # Experiment backlog for autoresearch
    experiments.jsonl     # Experiment log (append-only)
  api/
    main.py               # FastAPI app
    predict_week.py       # Generate predictions for upcoming games
    schemas.py            # Pydantic models for API responses
  frontend/
    src/
      components/         # React components
      pages/              # Dashboard views
  pipeline/
    refresh.py            # Weekly refresh orchestrator
  config.py               # Temporal config, DB connection, model path
  docker-compose.yml
  Dockerfile.api
  Dockerfile.frontend
  requirements.txt
```

## Scalability Considerations

| Concern | Current Scale | At Scale |
|---------|--------------|----------|
| Raw data volume | ~14M PBP rows (2005-2024), fits in memory | Partition by season if queries slow; consider materialized views |
| Feature computation time | ~5-10 min full rebuild | Incremental: only compute features for new games |
| Model training time | Seconds (XGBoost on ~10K rows) | Not a concern -- tabular data, small dataset |
| API latency | Model loaded in memory, sub-50ms inference | Not a concern for single-user/small audience |
| Dashboard traffic | Single user | Static build served by nginx, API behind reverse proxy |

This system is fundamentally small-scale. The data is bounded (17 weeks x 16 games x 20 seasons = ~5,400 game-rows for features). Performance optimization is not a priority -- correctness (especially no-leakage) is.

## Sources

- nfl-data-py library documentation and GitHub repository (MEDIUM confidence -- based on training knowledge, nfl-data-py wraps nflfastR data and provides `import_pbp_data()`, `import_schedules()`, etc.)
- XGBoost documentation for `predict_proba()` and classification patterns (HIGH confidence -- well-established)
- FastAPI standard patterns for model serving (HIGH confidence -- well-established)
- MLflow experiment tracking patterns (HIGH confidence -- well-established)
- NFL play-by-play data schema from nflfastR project (MEDIUM confidence -- based on training knowledge of the ~300 column schema including EPA, WPA, play-level stats)
