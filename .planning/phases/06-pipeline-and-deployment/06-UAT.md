---
status: complete
phase: 06-pipeline-and-deployment
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md]
started: 2026-03-18T05:00:00Z
updated: 2026-03-18T06:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running containers (`docker compose down`). Run `docker compose build` then `docker compose up -d`. After ~30 seconds, `docker compose ps` shows all 5 services (postgres, api, worker, mlflow, caddy) with healthy/running status. No services in restart loops or exited state.
result: pass

### 2. Pipeline Module Imports
expected: Run `python -c "from pipeline.refresh import run_pipeline, ingest_new_data, recompute_features, retrain_and_stage, generate_current_predictions; from pipeline.worker import main; print('OK')"`. Command exits 0 and prints "OK". All 5 pipeline functions and worker entrypoint are importable without errors.
result: pass

### 3. Pipeline Unit Tests Pass
expected: Run `python -m pytest tests/test_pipeline.py -v`. All 10 tests pass. Tests cover: step execution, non-fatal retrain, hard stops on steps 1-2, offseason guard, cache invalidation, staleness check, worker schedule config, and MLflow URI override.
result: pass

### 4. API Health Through Caddy
expected: With the Docker stack running, `curl http://localhost/api/health` returns `{"status":"ok"}`. This confirms Caddy is proxying `/api/*` requests to the api container, and the API is connected to postgres and serving.
result: pass

### 5. Frontend Served by Caddy
expected: With the Docker stack running and `frontend/dist` built (`cd frontend && npm run build`), open `http://localhost` in a browser. The React dashboard loads. Navigate to a sub-route and refresh — the page should still load (Caddy's `try_files` SPA fallback working).
result: pass
note: This Week and History pages work. Accuracy and Experiments pages show "Connection Failed" because no model/experiments exist yet on fresh deploy. API returns proper error responses (503/404) — frontend treats any non-OK as connection failure. Follow-up: fix frontend error handling to show contextual messages, alongside API graceful-degradation for bootstrap state. Bootstrap UX issues, not deployment failures.

### 6. Models Volume Sharing
expected: With the stack running, verify the models volume is correctly mounted. Run `docker compose exec worker ls /app/models-vol/` — should show the volume contents (may be empty initially). Run `docker compose exec api ls /app/models-vol/` — same contents visible. Verify api mount is read-only: `docker compose exec api touch /app/models-vol/test-file` should fail with "Read-only file system".
result: pass

### 7. Worker Schedule Configuration
expected: Run `docker compose logs worker | head -20`. Log output shows "Worker started. Next refresh: Tuesday 06:00 UTC" (or whatever REFRESH_CRON_HOUR is set to). Worker is running and waiting for the next scheduled trigger.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
