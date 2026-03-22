# Phase 6: Pipeline and Deployment - Context

**Gathered:** 2026-03-22 (updated — replaces 2026-03-17 version)
**Status:** Ready for planning

<domain>
## Phase Boundary

Containerize the full stack and deploy it to a Hostinger VPS at `nostradamus.silverreyes.net`. The system runs four services (postgres, api, worker, nginx) with the pre-trained Experiment 5 model (62.9% 2023 val accuracy) shipped directly in the image. The VPS already runs Nginx with existing sites — the app gets one new server block and its own nginx container on port 8080. Weekly pipeline handles data refresh and prediction generation automatically after the first interactive seed run.

**NOTE: This context supersedes the 2026-03-17 version. Key changes:**
- MLflow removed entirely (no service, no code, no Dockerfiles)
- Caddy replaced by nginx (app nginx container + VPS system nginx as reverse proxy)
- 4 services instead of 5: postgres, api, worker, nginx
- Pre-trained model ships in image with entrypoint-based volume seeding

</domain>

<decisions>
## Implementation Decisions

### Docker service architecture
- **4 services:** `postgres`, `api`, `worker`, `nginx`
- **No MLflow** — removed entirely. No mlflow service, no `mlflow.Dockerfile`, no mlflow imports anywhere
- **No Caddy** — replaced by nginx. `Caddyfile` can be deleted
- Single `Dockerfile` for the Python app, run as two services: `api` (uvicorn) and `worker` (APScheduler)
- Nginx gets its own `docker/nginx.Dockerfile` — multi-stage build (Node → nginx)
- The `mlflow.Dockerfile` file is deleted

### Nginx architecture (two layers)
- **App nginx container** (service name: `nginx`):
  - Routes `/api/*` → `api:8000` (FastAPI)
  - Serves `frontend/dist/` as static files at `/`
  - Listens on container port 80
  - Bound to **host port 8080** (`8080:80`) — port 80/443 are owned by VPS system nginx
  - Config lives at `docker/nginx.conf`
- **VPS system nginx** (already running, DO NOT touch existing blocks):
  - One new server block added for `nostradamus.silverreyes.net`
  - Proxies all traffic to `http://localhost:8080`
  - SSL via Certbot: `sudo certbot --nginx -d nostradamus.silverreyes.net` after adding the block
  - New block file: `/etc/nginx/sites-available/nostradamus.silverreyes.net`
  - Existing blocks (silverreyes.net, ghost.silverreyes.net, gameblazers.silverreyes.net) — untouched

### Frontend build strategy
- **Multi-stage Docker build** in `docker/nginx.Dockerfile`:
  - Stage 1 (builder): `node:20-alpine`, runs `npm ci && npm run build`, outputs to `/app/frontend/dist/`
  - Stage 2 (runtime): `nginx:alpine`, copies built dist from stage 1 + `docker/nginx.conf`
- **No pre-built `dist/` committed to git** — Docker handles the build
- Build context for nginx service is the project root (needs `frontend/` directory)

### Named volumes
- `pgdata` — PostgreSQL data (existing, unchanged)
- `models` — Model artifacts (`best_model.json`, `experiments.jsonl`). Mounted at `/app/models-vol`
  - `api`: read-only mount (`models:/app/models-vol:ro`)
  - `worker`: read-write mount (`models:/app/models-vol`)
- Volumes removed: `mlartifacts`, `caddy_data` (delete from compose)

### Model volume seeding (entrypoint pattern)
- Pre-trained model files (`models/artifacts/best_model.json`, `models/artifacts/model_exp001.json`, `models/artifacts/model_exp005.json`, `models/experiments.jsonl`) are committed to git and present in the image via `COPY . .`
- **`docker/entrypoint.sh`** — new file, copied into image, set as `ENTRYPOINT`:
  ```sh
  #!/bin/sh
  # Seed models volume on first boot if volume is empty
  MODEL_VOL="/app/models-vol"
  if [ ! -f "$MODEL_VOL/best_model.json" ]; then
      echo "[entrypoint] Seeding models volume from image..."
      cp /app/models/artifacts/best_model.json "$MODEL_VOL/"
      cp /app/models/experiments.jsonl "$MODEL_VOL/"
  fi
  exec "$@"
  ```
- `Dockerfile` gains: `COPY docker/entrypoint.sh /entrypoint.sh && RUN chmod +x /entrypoint.sh` and `ENTRYPOINT ["/entrypoint.sh"]`
- `MODEL_PATH` and `EXPERIMENTS_PATH` env vars stay pointing to `/app/models-vol/` (no path change)

### MLflow removal (code changes required)
**`models/train.py`** — remove all MLflow:
- `import mlflow` (top-level import)
- `setup_mlflow()` function and its call at line 375
- The `with mlflow.start_run(...):` block inside `log_experiment()` and all calls inside it:
  `mlflow.log_params`, `mlflow.log_metrics`, `mlflow.set_tag`, `mlflow.log_artifact`
- `log_experiment()` continues to exist — it still writes to `experiments.jsonl`; just strips the MLflow tracking side-effect

**`pipeline/refresh.py`** — remove all MLflow:
- `import mlflow` (top-level import, line 8)
- Inside `retrain_and_stage()`: remove the entire MLflow setup block (lines 154–159):
  ```python
  if os.environ.get("MLFLOW_TRACKING_URI"):
      mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
      mlflow.set_experiment("nfl-game-predictor")
  else:
      setup_mlflow()
  ```
- Remove `setup_mlflow` from the `from models.train import (...)` import list

### docker-compose.yml changes
Remove:
- `mlflow` service entirely
- `caddy` service entirely
- `mlartifacts` volume
- `caddy_data` volume
- `MLFLOW_TRACKING_URI` env var from `worker`

Add:
- `nginx` service (build from `docker/nginx.Dockerfile`, port `8080:80`, depends_on api healthy)

Modify:
- `api`: no env var changes needed (MLFLOW_TRACKING_URI was only in worker)
- `worker`: remove `MLFLOW_TRACKING_URI: http://mlflow:5000`

### Weekly refresh pipeline
- Unchanged from prior design. APScheduler with CronTrigger inside worker container
- Default schedule: Tuesday 6 AM UTC. Configurable via `REFRESH_CRON_HOUR` env var
- Pipeline sequence (unchanged):
  1. `ingest_new_data()` — FATAL: stops pipeline on failure. Includes staleness check.
  2. `recompute_features()` — FATAL: stops pipeline on failure
  3. `retrain_and_stage()` — NON-FATAL: logs error, continues to step 4
  4. `generate_current_predictions()` — runs if steps 1–2 succeeded
- Staged model does NOT go live automatically. Human calls `POST /model/reload` with token.

### Secrets and environment management
- `.env` at project root (gitignored): `POSTGRES_PASSWORD`, `RELOAD_TOKEN`, `REFRESH_CRON_HOUR` (optional)
- `.env.example` committed with placeholder values
- `POSTGRES_PASSWORD` is single source — database URLs constructed via `${POSTGRES_PASSWORD}` interpolation

### Health checks and startup ordering
- Unchanged: postgres → api, postgres → worker; nginx depends_on api (service_healthy)
- API health check: Python-based (`urllib.request.urlopen('http://localhost:8000/api/health')`) — no curl needed in slim image

### VPS bootstrap sequence
1. **Install Docker** on VPS (Ubuntu):
   ```sh
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   newgrp docker
   sudo apt-get install -y docker-compose-plugin
   ```
2. `git clone https://github.com/NatoJenkins/GamePredictor.git && cd GamePredictor`
3. `cp .env.example .env` — fill in real `POSTGRES_PASSWORD` and `RELOAD_TOKEN`
4. **Get VPS IP for DNS step:** `curl -4 ifconfig.me` — note this IP
5. **DNS (user action):** Add A record in Hostinger DNS panel: `nostradamus.silverreyes.net` → `<VPS IP>`. Wait for propagation before proceeding.
6. **Add VPS nginx server block:**
   ```sh
   sudo nano /etc/nginx/sites-available/nostradamus.silverreyes.net
   # (paste server block — see canonical_refs below)
   sudo ln -s /etc/nginx/sites-available/nostradamus.silverreyes.net /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
7. **SSL with Certbot:**
   ```sh
   sudo certbot --nginx -d nostradamus.silverreyes.net
   ```
8. `docker compose up -d` — postgres starts (init.sql creates schema), API loads model from seeded volume, nginx container builds frontend
9. **First data run** (interactive — watch it, don't background it):
   ```sh
   docker compose exec worker python -m pipeline.refresh
   ```
   This is the 20-season initial ingestion (~30+ min). Runs ingestion, feature build, retrain (step 3), and generates first predictions.

### SSL note
SSL termination happens at the **VPS system nginx level** via Certbot — not inside the app's nginx container. Certbot modifies the VPS server block (adds `ssl_certificate`, `listen 443`, 80→443 redirect). The app's nginx container remains plain HTTP on port 8080 internally; the VPS nginx handles HTTPS externally. This replaces the Caddy auto-SSL approach from prior context.

### Claude's Discretion
- Exact `docker/nginx.conf` content (routing rules, proxy headers, try_files for SPA)
- Exact VPS nginx server block content (proxy_pass headers, timeouts)
- `docker/entrypoint.sh` defensive logic (cp error handling)
- Dockerfile layer optimization and `.dockerignore`
- APScheduler job store configuration (in-memory is fine)
- Exact tenacity retry parameters in data ingestion
- Log rotation strategy

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Files to modify
- `docker-compose.yml` — currently has 5 services (postgres, api, worker, mlflow, caddy) — rewrite to 4 services, 2 volumes
- `Dockerfile` — add entrypoint.sh COPY + ENTRYPOINT
- `models/train.py` — strip all MLflow (import + setup_mlflow + mlflow.start_run block in log_experiment)
- `pipeline/refresh.py` — strip import mlflow + MLflow setup block in retrain_and_stage()

### Files to create
- `docker/entrypoint.sh` — seeds models volume on first boot
- `docker/nginx.conf` — app nginx routing config (SPA + /api/ proxy)
- `docker/nginx.Dockerfile` — multi-stage build: node:20-alpine (npm build) → nginx:alpine

### Files to delete
- `mlflow.Dockerfile`
- `Caddyfile`

### API and model interfaces
- `api/main.py` — FastAPI app with lifespan model loading, CORS config
- `api/config.py` — Settings class (DATABASE_URL, MODEL_PATH, EXPERIMENTS_PATH, RELOAD_TOKEN, CORS origins)
- `api/routes/` — All routes including GET /api/health (used by Docker health check)
- `models/predict.py` — `load_best_model()`, `get_best_experiment()`, `generate_predictions()`
- `models/train.py` — training pipeline (after MLflow removal)
- `models/artifacts/` — pre-trained model files: `best_model.json`, `model_exp001.json`, `model_exp005.json`
- `models/experiments.jsonl` — experiment log (seeded into models volume)

### Data and feature pipeline
- `data/sources.py` — team abbreviation constants (OAK→LV, SD→LAC, STL→LA, WSH→WAS)
- `data/db.py` — `get_engine()` via `DATABASE_URL` env var
- `features/build.py` — `build_game_features()` (read-only per CLAUDE.md)

### Frontend
- `frontend/` — React app, built by `docker/nginx.Dockerfile` Stage 1 via `npm ci && npm run build`
- `frontend/package.json` — build configuration
- `frontend/dist/` — output dir used by Stage 2 (DO NOT commit build artifacts to git)

### VPS nginx server block (reference template for planner)
```nginx
server {
    listen 80;
    server_name nostradamus.silverreyes.net;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
# Certbot will modify this block to add SSL after: sudo certbot --nginx -d nostradamus.silverreyes.net
```

### Project rules
- `CLAUDE.md` — Critical rules: forbidden features (result, home_score, away_score), temporal split, experiment loop constraints
- `.planning/REQUIREMENTS.md` — PIPE-01 through PIPE-04 requirements

</canonical_refs>

<code_context>
## Existing Code Insights

### Current docker-compose.yml state (starting point for rewrite)
- `postgres`: already correct — has `pgdata` volume, health check, `sql/` init mount. Keep as-is.
- `api`: correct structure — remove nothing. MLFLOW_TRACKING_URI was never in api, only in worker.
- `worker`: remove `MLFLOW_TRACKING_URI: http://mlflow:5000` env var. Everything else stays.
- `mlflow`: **delete entire service block**
- `caddy`: **delete entire service block**
- `volumes`: keep `pgdata`, keep `models`. Delete `mlartifacts`, delete `caddy_data`.

### MLflow in models/train.py — exact surgery needed
- Line 20: `import mlflow` → delete
- Lines ~33-40: `def setup_mlflow():` function → delete entirely
- Line 375: `setup_mlflow()` call (likely in `if __name__ == "__main__":` block) → delete
- Inside `log_experiment()`: the `with mlflow.start_run(run_name=f"exp-{experiment_id:03d}"):` block
  and all `mlflow.log_params`, `mlflow.log_metrics`, `mlflow.set_tag`, `mlflow.log_artifact` calls → delete
- `log_experiment()` function itself STAYS — it still writes to experiments.jsonl (that's its primary job)

### MLflow in pipeline/refresh.py — exact surgery needed
- Line 8: `import mlflow` → delete
- Lines 154-159 in `retrain_and_stage()`: the `if os.environ.get("MLFLOW_TRACKING_URI"):` / `else: setup_mlflow()` block → delete
- `from models.train import (... setup_mlflow ...)` → remove `setup_mlflow` from the import list

### Model artifacts on disk
- `models/artifacts/best_model.json` — Experiment 5 best model (62.9% 2023 val accuracy) ← this is the one that ships
- `models/artifacts/model_exp001.json` — Experiment 1 model
- `models/artifacts/model_exp005.json` — Experiment 5 model (same as best)
- `models/experiments.jsonl` — 5 experiment entries, append-only log
- All of these are COPY'd into image via `COPY . .` — present at `/app/models/artifacts/` and `/app/models/experiments.jsonl`

### Existing Dockerfile
```
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install (deps from pyproject.toml)

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "api.main:app", ...]
```
Add to runtime stage: `COPY docker/entrypoint.sh /entrypoint.sh && RUN chmod +x /entrypoint.sh`
Add after ENV lines: `ENTRYPOINT ["/entrypoint.sh"]`
The existing `CMD` in service definitions in docker-compose.yml overrides CMD — `ENTRYPOINT` wraps it.

### Reusable assets (pipeline unchanged)
- `pipeline/worker.py` — APScheduler loop, no MLflow dependency, stays as-is
- `pipeline/refresh.py` — after MLflow removal, all 4 steps remain intact
- `models/predict.py` — `generate_predictions()`, `detect_current_week()` — no changes needed
- `api/routes/` — all routes unchanged including POST /model/reload approval gate

</code_context>

<specifics>
## Specific Details

- **App nginx host port:** 8080 (VPS system nginx proxies nostradamus → localhost:8080)
- **Frontend build:** Multi-stage Docker (Node 20 Alpine → nginx Alpine). No committed build artifacts.
- **Model seeding:** Entrypoint script copies from `/app/models/artifacts/` → `/app/models-vol/` on first boot if volume is empty
- **SSL:** VPS system nginx + Certbot. Not the app's nginx container. Run after DNS propagates.
- **VPS IP lookup:** `curl -4 ifconfig.me` on the VPS. Plan should include this step before the DNS reminder.
- **Docker install:** `curl -fsSL https://get.docker.com | sh` is the canonical Docker convenience script for Ubuntu. Then `docker-compose-plugin` via apt.
- **First run is interactive:** `docker compose exec worker python -m pipeline.refresh` — 20-season ingest, ~30+ min. Must not be backgrounded so failures are visible.
- **mlflow dependency in pyproject.toml:** After MLflow removal from code, `mlflow` can be removed from `pyproject.toml` dependencies too — reduces image size.

</specifics>

<deferred>
## Deferred Ideas

- Notification on pipeline failure (email, Slack) — v2
- CI/CD with pre-built images on a registry — over-engineering for single-VPS
- Monitoring/alerting (Prometheus, Grafana) — v2
- Automatic model comparison (staged vs current) with metrics diff before reload — v2
- HTTPS redirect at app nginx level (vs VPS nginx level) — not needed with VPS nginx handling SSL

</deferred>

---

*Phase: 06-pipeline-and-deployment*
*Context gathered: 2026-03-22 (supersedes 2026-03-17)*
