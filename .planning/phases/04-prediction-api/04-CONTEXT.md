# Phase 4: Prediction API - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

FastAPI prediction service exposing 5 endpoints (API-01 through API-04 + GET /api/health) that the React dashboard (Phase 5) will consume. Read-only except for POST /model/reload. Predictions are pre-computed and stored, not generated per-request. No user authentication (out of scope), but model reload requires a shared secret.

</domain>

<decisions>
## Implementation Decisions

### Prediction Computation
- Pre-compute and store: `models/predict.py` runs after weekly refresh, writes predictions to a `predictions` DB table. API reads from the table.
- POST /model/reload both swaps the in-memory model AND re-generates predictions for the current week with the new model.
- Predictions table keyed by game_id only (no model version tracking). Regenerate replaces existing predictions for that week.
- Prediction logic lives in `models/predict.py` (not in api/), keeping prediction code with model code.

### Current Week Detection
- Auto-detect from schedule: query for earliest week in current season where `home_score IS NULL`.
- Current season = `MAX(season)` from `raw_schedules` table. Data-driven, not calendar-based.
- GET /predictions/current is a convenience endpoint that auto-resolves to the detected current week.
- Offseason behavior: return `{"status": "offseason", "predictions": []}` when no unplayed games exist.

### Response Schemas
- Prediction responses include full game metadata: home_team, away_team, game_date, week — no second lookup needed by dashboard.
- Predictions return predicted_winner + confidence (single number), NOT both teams' probabilities.
- API returns a confidence_tier field (high/medium/low) alongside raw confidence. Tier thresholds must be configurable in config.py — do NOT hardcode until model output distribution is observed. Initial defaults TBD.
- GET /model/info returns: experiment ID, training date, 2023 val accuracy, feature count, experiment description, AND both baseline accuracies (always-home, better-record).

### Season & Filtering
- /predictions/week/{week} accepts optional `?season=` query param. Defaults to current season when omitted.
- /predictions/history accepts optional `?season=` and `?team=` query params. Defaults to current season when both omitted.
- /predictions/history response includes a summary object (`{correct, total, accuracy}`) alongside the predictions array.

### History & Correctness
- Prediction correctness (actual_winner, correct columns) filled by the weekly refresh pipeline when new results are ingested — not computed by the API on-the-fly.

### Reload Protection
- POST /model/reload requires `X-Reload-Token` header checked against a `RELOAD_TOKEN` env var. Rejects with 403 if missing/wrong. No full auth system — just a shared secret to prevent accidental triggers.

### Experiments Endpoint
- GET /api/experiments reads and parses `experiments.jsonl` directly on each request. File is the single source of truth.
- At 20-30 experiments max, per-request parsing is negligible.
- Docker deployment note: experiments.jsonl must be accessible to the API container via volume mount.

### Health Endpoint
- GET /api/health included (not in requirements but needed for Docker health checks in Phase 6). Trivial implementation.

### Implementation Notes (Flagged During Discussion)
- **Current week detection**: predict_week logic must query schedule for next unplayed week — do NOT hardcode week numbers.
- **Features for unplayed games**: features/build.py needs to handle games where home_score IS NULL. Rolling stats should still compute correctly (stats as of before the game based on all prior results). If build.py currently skips NULL-outcome rows, that's a bug for prediction generation. Verify during implementation.

### Claude's Discretion
- Pydantic response model exact field names and types
- FastAPI app structure (single file vs routes/ directory)
- Error response format and status codes
- Health check response content (just {"status": "ok"} vs deeper checks)
- Initial confidence tier threshold values

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & API Design
- `.planning/research/ARCHITECTURE.md` §4 — Prediction Service component boundary, endpoint table, model loading pattern, confidence score design
- `.planning/research/ARCHITECTURE.md` §7 — PostgreSQL schema including predictions table design

### Model & Feature Interfaces
- `models/train.py` — Training pipeline functions (load_and_split, train_and_evaluate, save_best_model); model artifact format
- `models/artifacts/` — Best model checkpoint location
- `models/experiments.jsonl` — Experiment log schema and format (API reads this directly)
- `features/definitions.py` — Feature column lists (ROLLING_FEATURES, SITUATIONAL_FEATURES, TARGET, META_COLS, FORBIDDEN_FEATURES)

### Data Access
- `data/db.py` — SQLAlchemy engine and table access pattern (get_engine, get_table)
- `features/build.py` — Feature pipeline (must verify it handles NULL-outcome games for prediction generation)

### Project Rules
- `CLAUDE.md` — Critical rules including forbidden features, temporal split constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data/db.py`: SQLAlchemy engine via `get_engine()` + `get_table()` — API can use same DB access pattern
- `models/train.py`: `load_and_split()` shows how features are loaded from DB; prediction code can reuse the feature loading pattern
- `features/definitions.py`: Feature column constants — prediction code needs META_COLS to separate features from metadata

### Established Patterns
- Database access via `DATABASE_URL` env var + dotenv (Phase 1)
- Model artifacts stored in `models/artifacts/` directory (Phase 3)
- Dual logging: experiments.jsonl (flat file) + MLflow (Phase 3)
- Dependencies managed in pyproject.toml (no requirements.txt)

### Integration Points
- `models/artifacts/best_model.json` — Current best model metadata (experiment ID, accuracy, path)
- `models/experiments.jsonl` — Read by GET /api/experiments endpoint
- `features/build.py` — Must be verified to handle unplayed games for prediction feature generation
- PostgreSQL `raw_schedules` table — Source for week/season detection and game metadata

</code_context>

<specifics>
## Specific Ideas

- GET /predictions/current as convenience alias that resolves to current week — dashboard's "this week" view calls this one URL
- Confidence tier thresholds configurable in config.py so they can be tuned after observing the model's actual probability distribution
- experiments.jsonl read directly (not loaded into DB) to keep it as single source of truth
- Reload token via env var — lightweight protection without a full auth system

</specifics>

<deferred>
## Deferred Ideas

- Per-model prediction versioning (tracking which model version made each prediction) — not needed for v1, could add later if model comparison becomes important
- Pagination for /predictions/history — not needed at current scale but worth adding if prediction volume grows significantly
- Both-team probabilities in response — currently just winner + confidence, could expose full predict_proba output later

</deferred>

---

*Phase: 04-prediction-api*
*Context gathered: 2026-03-16*
