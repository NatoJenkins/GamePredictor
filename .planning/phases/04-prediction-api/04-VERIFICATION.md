---
phase: 04-prediction-api
verified: 2026-03-17T00:00:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
---

# Phase 4: Prediction API Verification Report

**Phase Goal:** Serve predictions and model metadata via FastAPI endpoints
**Verified:** 2026-03-17
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Plan 01)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | predictions table exists in PostgreSQL with correct schema | VERIFIED | `sql/init.sql` lines 130-143: `CREATE TABLE IF NOT EXISTS predictions` with all required columns including `game_id VARCHAR(20) PRIMARY KEY`, `season`, `week`, `game_date`, `home_team`, `away_team`, `predicted_winner`, `confidence`, `confidence_tier`, `model_id`, `actual_winner`, `correct` |
| 2 | models/predict.py generates predictions from the trained model and stores them in the DB | VERIFIED | `generate_predictions()` builds features, runs `model.predict_proba(X)[:, 1]`, computes winner/confidence, and upserts via `on_conflict_do_update` (lines 264-320) |
| 3 | Pydantic response schemas define the contract for all API endpoints | VERIFIED | `api/schemas.py` defines `PredictionResponse`, `WeekPredictionsResponse`, `PredictionHistoryResponse`, `HistorySummary`, `ModelInfoResponse`, `ExperimentResponse`, `ReloadResponse`, `HealthResponse` |
| 4 | Confidence score is computed as max(home_prob, 1-home_prob) not raw predict_proba output | VERIFIED | `models/predict.py` lines 271-276: `if home_prob >= 0.5: confidence = home_prob` else `confidence = 1.0 - home_prob` |
| 5 | Confidence tiers are configurable via api/config.py, not hardcoded | VERIFIED | `api/config.py` `Settings` class has `CONFIDENCE_HIGH = float(os.environ.get("CONFIDENCE_HIGH", "0.65"))` and `CONFIDENCE_MEDIUM = float(os.environ.get("CONFIDENCE_MEDIUM", "0.55"))` read from env vars |

### Observable Truths (Plan 02)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | GET /api/predictions/week/{week} returns predicted winner and confidence per game | VERIFIED | `api/routes/predictions.py` line 18, queries `predictions` table, returns `WeekPredictionsResponse`; test `test_get_week_predictions` passes |
| 7 | GET /api/predictions/current auto-resolves to the current unplayed week | VERIFIED | `api/routes/predictions.py` line 86, calls `detect_current_week(engine)` and delegates to `get_week_predictions`; test `test_current_week` passes |
| 8 | GET /api/predictions/current returns offseason status when no unplayed games exist | VERIFIED | `api/routes/predictions.py` lines 95-101: returns `WeekPredictionsResponse(season=0, week=0, status="offseason", predictions=[])`; test `test_offseason` with `offseason_client` passes |
| 9 | GET /api/predictions/history returns past predictions with actual outcomes and summary stats | VERIFIED | `api/routes/predictions.py` line 111, query filters `actual_winner IS NOT NULL`, builds `HistorySummary(correct, total, accuracy)`; tests `test_history` and `test_history_summary` pass |
| 10 | GET /api/predictions/history accepts optional season and team query params | VERIFIED | `api/routes/predictions.py` lines 113-121: `season: int | None = Query(...)`, `team: str | None = Query(...)`; test `test_history_filters` passes |
| 11 | GET /api/model/info returns experiment metadata including both baseline accuracies | VERIFIED | `api/routes/model.py` lines 30-38: returns `ModelInfoResponse` including `baseline_always_home` and `baseline_better_record`; test `test_model_info_baselines` passes |
| 12 | POST /api/model/reload swaps model AND regenerates current week predictions | VERIFIED | `api/routes/model.py` lines 67-96: loads new model, re-parses experiments.jsonl, calls `generate_predictions`, updates `app_state["model"]` and `app_state["model_info"]`; test `test_reload` passes |
| 13 | POST /api/model/reload rejects requests without valid X-Reload-Token | VERIFIED | `api/routes/model.py` line 62: `if not settings.RELOAD_TOKEN or x_reload_token != settings.RELOAD_TOKEN: raise HTTPException(status_code=403)`; tests `test_reload_auth` (422 missing header) and `test_reload_bad_token` (403 wrong token) pass |
| 14 | GET /api/experiments returns parsed experiments.jsonl entries | VERIFIED | `api/routes/experiments.py`: reads JSONL line-by-line, parses `ExperimentResponse(**entry)`, returns 404 on missing file; tests `test_list_experiments` and `test_experiments_structure` pass |
| 15 | All API tests pass with mocked model and DB | VERIFIED | `pytest tests/api/ tests/models/test_predict.py` — 23 passed in 1.15s; full suite `pytest -x -q` — 102 passed, 0 regressions |

**Score:** 15/15 truths verified

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `sql/init.sql` | predictions table DDL | VERIFIED | Contains `CREATE TABLE IF NOT EXISTS predictions` with all 12 required columns, plus both indexes (`idx_predictions_season_week`, `idx_predictions_season`) |
| `models/predict.py` | Prediction generation pipeline | VERIFIED | 323 lines; exports `load_best_model`, `get_best_experiment`, `detect_current_week`, `generate_predictions`, `_get_team_rolling_features`; no imports from `api/` |
| `api/schemas.py` | Pydantic response models for all endpoints | VERIFIED | 99 lines; defines 8 Pydantic v2 `BaseModel` subclasses covering every endpoint response type |
| `api/config.py` | Confidence tier thresholds and app settings | VERIFIED | `Settings` class with `RELOAD_TOKEN`, `CONFIDENCE_HIGH`, `CONFIDENCE_MEDIUM`, `CORS_ORIGINS`; `get_confidence_tier()` function |

### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `api/main.py` | FastAPI app with lifespan, CORS, router includes | VERIFIED | Lifespan loads engine, model, experiment metadata at startup; CORSMiddleware configured; all 4 routers included |
| `api/deps.py` | Dependency injection for DB engine and app state | VERIFIED | `app_state: dict = {}` and `get_app_state() -> dict` |
| `api/routes/predictions.py` | Prediction endpoints | VERIFIED | 3 endpoints: `/api/predictions/week/{week}`, `/api/predictions/current`, `/api/predictions/history` |
| `api/routes/model.py` | Model info and reload endpoints | VERIFIED | 2 endpoints: `GET /api/model/info`, `POST /api/model/reload` |
| `api/routes/experiments.py` | Experiments endpoint | VERIFIED | `GET /api/experiments` reads JSONL directly |
| `api/routes/health.py` | Health check endpoint | VERIFIED | `GET /api/health` returns `{"status": "ok"}` |
| `tests/api/conftest.py` | Test fixtures with mocked model and DB | VERIFIED | `client` and `offseason_client` fixtures; patches lifespan AND route-level dependencies; `SAMPLE_EXPERIMENTS`, `SAMPLE_PREDICTIONS` data |
| `tests/api/test_health.py` | Health test | VERIFIED | `test_health` |
| `tests/api/test_experiments.py` | Experiments tests | VERIFIED | `test_list_experiments`, `test_experiments_structure` |
| `tests/api/test_predictions.py` | Prediction endpoint tests | VERIFIED | 7 tests covering week, default season, current, offseason, history, summary, filters |
| `tests/api/test_model.py` | Model endpoint tests | VERIFIED | 5 tests covering info, baselines, reload, missing header (422), bad token (403) |
| `tests/models/test_predict.py` | predict.py unit tests | VERIFIED | 8 tests including prefix flip correctness (`test_get_team_rolling_features_as_home`, `test_get_team_rolling_features_as_away`), path normalization |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `models/predict.py` | `models/artifacts/best_model.json` | `XGBClassifier.load_model()` | VERIFIED | `model.load_model(path)` at line 43 |
| `models/predict.py` | `models/experiments.jsonl` | JSON line parsing | VERIFIED | `with open(jsonl_path) as f:` + `json.loads(line)` at lines 70-78; `.replace("\\", "/")` normalizes Windows paths |
| `models/predict.py` | `sql predictions table` | SQLAlchemy upsert | VERIFIED | `pg_insert(predictions_table).values(records)` + `on_conflict_do_update(index_elements=["game_id"])` at lines 303-320 |

### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `api/main.py` | `models/predict.py` | lifespan calls `load_best_model` and `get_best_experiment` | VERIFIED | `api/main.py` lines 20-21 import and call both functions at startup |
| `api/routes/predictions.py` | `api/deps.py` | `Depends(get_app_state)` | VERIFIED | Every endpoint handler has `state: dict = Depends(get_app_state)` |
| `api/routes/model.py` | `models/predict.py` | reload calls `generate_predictions` | VERIFIED | `api/routes/model.py` line 84: `preds = generate_predictions(new_model, ...)` |
| `api/routes/predictions.py` | `sql predictions table` | `pd.read_sql` query | VERIFIED | `pd.read_sql(query, engine, params=...)` with `FROM predictions WHERE season = ...` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| API-01 | 04-01-PLAN, 04-02-PLAN | GET /predictions/week/{week} returns predicted winner and confidence per game | SATISFIED | `GET /api/predictions/week/{week}` endpoint implemented and tested; returns `predicted_winner`, `confidence`, `confidence_tier` per game |
| API-02 | 04-01-PLAN, 04-02-PLAN | GET /predictions/history returns all past predictions with actual outcomes | SATISFIED | `GET /api/predictions/history` implemented; filters by `actual_winner IS NOT NULL`; returns outcomes + `HistorySummary` with `correct/total/accuracy` |
| API-03 | 04-01-PLAN, 04-02-PLAN | GET /model/info returns current model version, training date, and 2023 validation accuracy | SATISFIED | `GET /api/model/info` returns `experiment_id`, `training_date`, `val_accuracy_2023`, plus `feature_count`, `hypothesis`, and both baseline accuracies per CONTEXT.md |
| API-04 | 04-01-PLAN, 04-02-PLAN | POST /model/reload hot-swaps the serving model after manual approval | SATISFIED | `POST /api/model/reload` validates `X-Reload-Token`, loads new model, re-parses experiments.jsonl, regenerates current week predictions, updates in-memory `app_state` |

All 4 requirements satisfied. No orphaned requirements (traceability table in REQUIREMENTS.md maps exactly API-01 through API-04 to Phase 4).

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | — |

No TODO/FIXME comments, placeholder returns, empty handlers, or stub implementations found in any phase 4 files. All functions have substantive implementations. No `from api` imports in `models/` (isolation maintained).

---

## Human Verification Required

### 1. Live Server Smoke Test

**Test:** With PostgreSQL running and `models/artifacts/best_model.json` present, start `uvicorn api.main:app --reload` and visit `http://localhost:8000/docs`.
**Expected:** OpenAPI docs display all 6 endpoints; `GET /api/health` returns `{"status": "ok"}`.
**Why human:** Requires real DB and model artifact; TestClient mocks bypass actual lifespan loading.

### 2. Reload Token End-to-End

**Test:** With server running, call `POST /api/model/reload` with `X-Reload-Token: <value from env>`.
**Expected:** Response shows `status: "reloaded"` and `predictions_generated >= 0`; subsequent `GET /api/model/info` shows updated experiment metadata if a new model was staged.
**Why human:** Requires real model artifact and real DB with schedules data to verify prediction regeneration.

### 3. Predictions Population

**Test:** After calling `generate_predictions` (either via reload or direct script), `GET /api/predictions/week/{current_week}` should return actual game predictions.
**Expected:** Non-empty predictions list with `predicted_winner`, `confidence` values in [0.5, 1.0] range, `confidence_tier` in {high, medium, low}.
**Why human:** Requires populated schedules table with a future (unscored) week.

---

## Gaps Summary

No gaps. All 15 truths verified, all 15 artifacts substantive and wired, all 4 key links confirmed, all 4 requirements satisfied. Full test suite (102 tests) passes with zero regressions.

---

_Verified: 2026-03-17_
_Verifier: Claude (gsd-verifier)_
