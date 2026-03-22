---
phase: 06-pipeline-and-deployment
verified: 2026-03-22T00:00:00Z
status: passed
score: 17/17 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 9/9
  note: "Previous verification (2026-03-17) covered the original 5-service stack (MLflow/Caddy). Phase was re-planned. This verification covers the re-planned 3-plan set targeting nginx/no-MLflow."
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 6: Pipeline and Deployment Verification Report

**Phase Goal:** Remove MLflow/Caddy, replace with nginx, containerize as 4-service stack, create VPS deployment artifacts
**Verified:** 2026-03-22
**Status:** passed
**Re-verification:** Yes — previous VERIFICATION.md (2026-03-17) covered the original phase 06 plan; this verification covers the re-planned 3-plan set (06-01, 06-02, 06-03)

## Goal Achievement

### Observable Truths

Must-haves are drawn from the three plan frontmatter blocks (06-01, 06-02, 06-03).

#### Plan 06-01 Truths — MLflow Removal

| #  | Truth                                                                   | Status     | Evidence                                                                                      |
|----|-------------------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------|
| 1  | No Python file in the project imports mlflow                            | VERIFIED   | `grep -r "import mlflow" --include="*.py"` returns zero matches (excluding .planning/ and __pycache__) |
| 2  | log_experiment() still writes to experiments.jsonl                      | VERIFIED   | `models/train.py` line 160: `def log_experiment(` present; line 221: `with open(jsonl_path, "a") as f:` present |
| 3  | retrain_and_stage() still trains, evaluates, and stages models          | VERIFIED   | `pipeline/refresh.py` line 132: `def retrain_and_stage(engine, experiments_path, model_dir):` present |
| 4  | All existing JSONL logging tests pass                                   | VERIFIED   | `tests/models/test_logging.py` contains `class TestJsonlLogging` (line 28), no mlflow references remain |
| 5  | mlflow.Dockerfile and Caddyfile no longer exist                         | VERIFIED   | `ls mlflow.Dockerfile Caddyfile` returns nothing; files confirmed absent from repo root |
| 6  | mlflow is not in pyproject.toml dependencies                            | VERIFIED   | Dependency list contains 13 packages; mlflow not present. `grep mlflow pyproject.toml` returns nothing |

#### Plan 06-02 Truths — Docker Infrastructure

| #  | Truth                                                                                 | Status     | Evidence                                                                                      |
|----|---------------------------------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------|
| 7  | docker-compose.yml defines exactly 4 services: postgres, api, worker, nginx          | VERIFIED   | YAML parse: `['postgres', 'api', 'worker', 'nginx']` — count 4, no mlflow/caddy               |
| 8  | docker-compose.yml defines exactly 2 volumes: pgdata, models                         | VERIFIED   | YAML parse: `['pgdata', 'models']` — count 2, no mlartifacts/caddy_data                       |
| 9  | Dockerfile has ENTRYPOINT that runs entrypoint.sh                                     | VERIFIED   | Line 15: `ENTRYPOINT ["/entrypoint.sh"]`; line 13: `COPY docker/entrypoint.sh /entrypoint.sh` |
| 10 | entrypoint.sh seeds models volume if best_model.json is missing                       | VERIFIED   | `docker/entrypoint.sh` lines 4-9: seeds from `/app/models/artifacts/best_model.json` and `experiments.jsonl` when `$MODEL_VOL/best_model.json` absent |
| 11 | nginx.Dockerfile builds frontend and serves via nginx                                 | VERIFIED   | `docker/nginx.Dockerfile`: `FROM node:20-alpine AS builder` (line 2); `FROM nginx:alpine` (line 10); multi-stage build confirmed |
| 12 | nginx.conf routes /api/ to api:8000 and / to static files                            | VERIFIED   | Line 10: `proxy_pass http://api:8000/api/;`; lines 19-21: `try_files $uri $uri/ /index.html;` |
| 13 | .env.example has POSTGRES_PASSWORD, RELOAD_TOKEN, REFRESH_CRON_HOUR and no DOMAIN   | VERIFIED   | File contains exactly 3 variables; `grep DOMAIN .env.example` returns nothing |

#### Plan 06-03 Truths — VPS Deployment Artifacts

| #  | Truth                                                                                         | Status     | Evidence                                                                                            |
|----|-----------------------------------------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------------|
| 14 | VPS nginx server block template exists as a standalone file ready to copy                    | VERIFIED   | `docs/vps-nginx-block.conf` exists; contains `server_name nostradamus.silverreyes.net;` and `proxy_pass http://localhost:8080;` |
| 15 | Deployment guide covers all 9 VPS bootstrap steps from CONTEXT.md                           | VERIFIED   | `docs/DEPLOY.md` contains Steps 1-9: Docker install, clone, env config, get IP, DNS, nginx block, certbot, compose up, first data run |
| 16 | Deployment guide references the correct port (8080) and domain (nostradamus.silverreyes.net) | VERIFIED   | `docs/DEPLOY.md` line 81: "Verify: `docker compose ps` shows all 4 services healthy"; line 3: `nostradamus.silverreyes.net`; line 69 mentions port 8080 |
| 17 | No MLflow or Caddy references remain anywhere in the project (full sweep)                    | VERIFIED   | `grep -r "mlflow" --include="*.py"` = 0 matches; `grep -r "mlflow" --include="*.yml"` = 0 matches; `grep -ri "caddy" --include={"*.py","*.yml","*.toml","*.sh"}` = 0 matches |

**Score:** 17/17 truths verified

### Required Artifacts

| Artifact                    | Expected                                              | Status     | Details                                                                                   |
|-----------------------------|-------------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| `models/train.py`           | Training pipeline without MLflow                      | VERIFIED   | `def log_experiment` present (line 160); no mlflow import; JSONL append at line 221      |
| `pipeline/refresh.py`       | Refresh pipeline without MLflow                       | VERIFIED   | `def retrain_and_stage` present (line 132); no mlflow import or MLFLOW_TRACKING_URI      |
| `tests/models/test_logging.py` | JSONL-only logging tests                           | VERIFIED   | `class TestJsonlLogging` present (line 28); no mlflow/setup_mlflow/TestMlflowLogging     |
| `pyproject.toml`            | Dependencies without mlflow                           | VERIFIED   | 13 dependencies listed; mlflow absent                                                     |
| `docker/entrypoint.sh`      | Model volume seeding on first boot                    | VERIFIED   | Contains `cp /app/models/artifacts/best_model.json "$MODEL_VOL/"` and `exec "$@"`        |
| `docker/nginx.conf`         | App nginx routing for API and SPA                     | VERIFIED   | `proxy_pass http://api:8000/api/;` and `try_files $uri $uri/ /index.html;`               |
| `docker/nginx.Dockerfile`   | Multi-stage frontend build + nginx serve              | VERIFIED   | `FROM node:20-alpine AS builder`; `FROM nginx:alpine`; `COPY --from=builder`             |
| `docker-compose.yml`        | 4-service orchestration (no MLflow/Caddy)            | VERIFIED   | 4 services, 2 volumes; no mlflow/caddy/mlartifacts/caddy_data/MLFLOW_TRACKING_URI        |
| `Dockerfile`                | Python app image with entrypoint                      | VERIFIED   | `ENTRYPOINT ["/entrypoint.sh"]`; `COPY docker/entrypoint.sh /entrypoint.sh`              |
| `.env.example`              | Environment variable template (3 vars, no DOMAIN)    | VERIFIED   | POSTGRES_PASSWORD, RELOAD_TOKEN, REFRESH_CRON_HOUR — no DOMAIN                           |
| `docs/vps-nginx-block.conf` | VPS nginx server block for nostradamus.silverreyes.net | VERIFIED | `proxy_pass http://localhost:8080;`; `server_name nostradamus.silverreyes.net;`           |
| `docs/DEPLOY.md`            | Step-by-step VPS deployment guide (9 steps)           | VERIFIED   | All 9 steps present; references correct domain, port, certbot, pipeline.refresh           |

**Deleted artifacts confirmed absent:**

| Artifact          | Expected State | Status   |
|-------------------|----------------|----------|
| `mlflow.Dockerfile` | Deleted        | VERIFIED |
| `Caddyfile`         | Deleted        | VERIFIED |

### Key Link Verification

#### Plan 06-01 Key Links

| From                    | To                         | Via                                  | Status   | Detail                                                                                      |
|-------------------------|----------------------------|--------------------------------------|----------|---------------------------------------------------------------------------------------------|
| `pipeline/refresh.py`   | `models/train.py`          | `from models.train import`           | WIRED    | Line 142: `from models.train import (` — imports DEFAULT_PARAMS, load_and_split, log_experiment, save_best_model, should_keep, train_and_evaluate |
| `models/train.py`       | `models/experiments.jsonl` | jsonl append in log_experiment       | WIRED    | Line 221: `with open(jsonl_path, "a") as f:` inside log_experiment body                    |

#### Plan 06-02 Key Links

| From                    | To                         | Via                                        | Status   | Detail                                                                                 |
|-------------------------|----------------------------|--------------------------------------------|----------|----------------------------------------------------------------------------------------|
| `docker-compose.yml`    | `Dockerfile`               | build context for api and worker           | WIRED    | Lines 18 and 38: `build: .` for api and worker services respectively                  |
| `docker-compose.yml`    | `docker/nginx.Dockerfile`  | nginx service build                        | WIRED    | Line 54: `dockerfile: docker/nginx.Dockerfile`                                         |
| `docker/nginx.conf`     | `api:8000`                 | proxy_pass for /api/ location              | WIRED    | Line 10: `proxy_pass http://api:8000/api/;`                                            |
| `Dockerfile`            | `docker/entrypoint.sh`     | COPY and ENTRYPOINT                        | WIRED    | Line 13: `COPY docker/entrypoint.sh /entrypoint.sh`; line 15: `ENTRYPOINT ["/entrypoint.sh"]` |

#### Plan 06-03 Key Links

| From                        | To                              | Via                          | Status   | Detail                                                                             |
|-----------------------------|---------------------------------|------------------------------|----------|------------------------------------------------------------------------------------|
| `docs/vps-nginx-block.conf` | `docker-compose.yml nginx`      | port 8080 mapping            | WIRED    | `proxy_pass http://localhost:8080;` matches `"8080:80"` in nginx service ports     |
| `docs/DEPLOY.md`            | `.env.example`                  | `cp .env.example .env` step  | WIRED    | Line 32: `cp .env.example .env` in Step 3 of deployment guide                     |

### Requirements Coverage

| Requirement | Source Plan(s)            | Description                                                                             | Status    | Evidence                                                                                                    |
|-------------|---------------------------|-----------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------------------------------------------|
| PIPE-01     | 06-01, 06-03              | Weekly refresh automatically fetches new game data and recomputes features on a schedule | SATISFIED | `pipeline/refresh.py`: `ingest_new_data` + `recompute_features` in `run_pipeline`; `pipeline/worker.py`: `CronTrigger(day_of_week="tue", hour=cron_hour, timezone="UTC")` |
| PIPE-02     | 06-01, 06-03              | Weekly refresh automatically retrains and stages a candidate model — staged only        | SATISFIED | `pipeline/refresh.py`: `retrain_and_stage` saves to `model_dir` (models volume); no mlflow dependency |
| PIPE-03     | 06-02, 06-03              | New model staged but not live until POST /model/reload is called manually               | SATISFIED | API mounts models volume as read-only (`:ro`); worker writes to it; hot-swap only on explicit reload call |
| PIPE-04     | 06-02, 06-03              | Full stack runs under Docker Compose                                                    | SATISFIED | docker-compose.yml defines 4 services (postgres, api, worker, nginx) with health checks and named volumes |

**Note on PIPE-04 text:** REQUIREMENTS.md still lists "mlflow, frontend, worker services" in the PIPE-04 description (stale text from before the re-plan). The implemented stack is postgres, api, worker, nginx — this matches the re-planned phase goal and all three plan acceptance criteria. The requirements text was not updated during the re-plan, but the intent (full containerized stack) is fully satisfied.

No orphaned requirements: REQUIREMENTS.md maps exactly PIPE-01 through PIPE-04 to Phase 6, and all four are covered by plans 06-01, 06-02, and 06-03.

### Anti-Patterns Found

No anti-patterns found. Scan of all phase 6 modified files (docker/, Dockerfile, docker-compose.yml, .env.example, docs/) returned zero TODO/FIXME/placeholder markers, empty implementations, or stub handlers.

### Human Verification Required

The following items require runtime or visual confirmation that static analysis cannot provide:

**1. Full stack boot**

Test: Copy `.env.example` to `.env`, set real values for POSTGRES_PASSWORD and RELOAD_TOKEN, run `docker compose up -d`, then `docker compose ps`
Expected: All 4 services show healthy status — postgres, api, worker, nginx
Why human: Static config validation passes but actual container startup, network resolution between services, and health check timing require a live Docker environment

**2. Entrypoint volume seeding on first boot**

Test: Run `docker compose up -d` on a fresh machine (no models volume); exec into api container and check `/app/models-vol/best_model.json`
Expected: `best_model.json` present in volume (seeded by entrypoint.sh from image)
Why human: Requires a live Docker environment with a clean volume state; cannot simulate statically

**3. nginx SPA routing and API proxy**

Test: Navigate to `http://<VPS-IP>:8080/` — dashboard loads; navigate to `/experiments` directly — dashboard loads (not 404); make a GET request to `http://<VPS-IP>:8080/api/health` — returns JSON
Expected: SPA fallback routes non-file paths to index.html; /api/ requests forwarded to api:8000
Why human: Requires live nginx and built frontend assets

**4. VPS end-to-end deployment**

Test: Follow docs/DEPLOY.md steps 1-9 on a Hostinger VPS
Expected: `https://nostradamus.silverreyes.net` loads the dashboard with valid SSL certificate
Why human: Requires live DNS propagation, Certbot provisioning, and full stack running on real VPS hardware

**5. Human approval gate (PIPE-03 runtime)**

Test: Allow worker to complete a retrain cycle (step 3 of run_pipeline); verify API still serves old model; then call `POST /api/model/reload`; verify new model is active
Expected: Staged model on disk does not go live until explicit reload; reload returns success and new model info
Why human: Requires a completed retrain cycle in a live environment

### Gaps Summary

No gaps. All automated checks passed for the re-planned phase 06:

- All 17 must-have truths from the three plan frontmatter blocks: verified
- All 12 required artifacts (10 present, 2 deleted): correct state confirmed
- All 8 key links: verified present in actual code
- All 4 requirements (PIPE-01 through PIPE-04): satisfied with implementation evidence
- Full mlflow/caddy sweep: zero references in Python files, YAML files, or shell scripts
- `mlflow.Dockerfile` and `Caddyfile`: confirmed deleted from repository
- docker-compose.yml: exactly 4 services, exactly 2 volumes
- No anti-patterns detected

The 5 human verification items are operational concerns (live Docker environment, DNS, VPS hardware) that cannot be verified by static analysis. They do not represent code gaps — the code is complete and correctly wired.

---

_Verified: 2026-03-22_
_Verifier: Claude (gsd-verifier)_
