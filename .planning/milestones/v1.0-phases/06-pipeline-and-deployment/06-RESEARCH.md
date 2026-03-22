# Phase 6: Pipeline and Deployment - Research

**Researched:** 2026-03-22 (supersedes 2026-03-17 version)
**Domain:** Docker Compose orchestration, nginx multi-layer proxy, multi-stage frontend build, MLflow removal, VPS deployment
**Confidence:** HIGH

## Summary

Phase 6 containerizes the full NFL Game Predictor stack and deploys it to a Hostinger VPS at `nostradamus.silverreyes.net`. The architecture uses four Docker Compose services (postgres, api, worker, nginx) with a two-layer nginx strategy: an app-level nginx container (port 8080) that serves the React SPA and proxies `/api/*` requests to FastAPI, and the existing VPS system nginx that reverse-proxies the subdomain to localhost:8080 with Certbot SSL. The pre-trained Experiment 5 model (62.9% 2023 validation accuracy) ships in the Docker image and is seeded into a named volume via an entrypoint script on first boot.

This is a re-research driven by significant architecture changes from the updated CONTEXT.md (2026-03-22). The prior research assumed MLflow as a service and Caddy as the edge proxy. Both are now removed. MLflow is stripped from all code (models/train.py, pipeline/refresh.py, tests/models/test_logging.py, pyproject.toml). Caddy is replaced by nginx at two layers. The frontend is no longer pre-built -- it uses a multi-stage Docker build (Node 20 Alpine to build, nginx Alpine to serve).

**Primary recommendation:** Execute in two waves: (1) MLflow removal surgery + Docker infrastructure files (Dockerfile updates, nginx.Dockerfile, nginx.conf, entrypoint.sh, docker-compose.yml rewrite, .dockerignore update, .env.example update, pyproject.toml cleanup, test updates), then (2) VPS bootstrap (Docker install, git clone, DNS, VPS nginx server block, Certbot SSL, docker compose up, first interactive data run).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **4 services:** `postgres`, `api`, `worker`, `nginx` -- NO MLflow, NO Caddy
- Single `Dockerfile` for the Python app, run as two services: `api` (uvicorn) and `worker` (APScheduler)
- Nginx gets its own `docker/nginx.Dockerfile` -- multi-stage build (Node 20 Alpine build, nginx Alpine serve)
- App nginx container listens on container port 80, bound to host port 8080 (`8080:80`)
- App nginx routes `/api/*` to `api:8000` and serves frontend at `/`
- VPS system nginx adds ONE new server block for `nostradamus.silverreyes.net` proxying to `localhost:8080`
- SSL via Certbot on VPS system nginx -- NOT inside the app's nginx container
- Frontend build: multi-stage Docker, no committed `dist/`
- Model volume seeding: `docker/entrypoint.sh` copies image artifacts to named volume on first boot if empty
- Named volumes: `pgdata` (postgres), `models` (model artifacts) -- no `mlartifacts`, no `caddy_data`
- API reads model volume read-only (`models:/app/models-vol:ro`), worker reads/writes (`models:/app/models-vol`)
- MLflow removed entirely from: `models/train.py`, `pipeline/refresh.py`, `pyproject.toml`, docker-compose.yml
- Files to delete: `mlflow.Dockerfile`, `Caddyfile`
- Docker install on VPS: `curl -fsSL https://get.docker.com | sh` + `docker-compose-plugin`
- First data run is interactive: `docker compose exec worker python -m pipeline.refresh`
- `.env` at project root (gitignored): `POSTGRES_PASSWORD`, `RELOAD_TOKEN`, `REFRESH_CRON_HOUR`
- `.env.example` committed with placeholder values

### Claude's Discretion
- Exact `docker/nginx.conf` content (routing rules, proxy headers, try_files for SPA)
- Exact VPS nginx server block content (proxy_pass headers, timeouts)
- `docker/entrypoint.sh` defensive logic (cp error handling)
- Dockerfile layer optimization and `.dockerignore`
- APScheduler job store configuration (in-memory is fine)
- Exact tenacity retry parameters in data ingestion
- Log rotation strategy

### Deferred Ideas (OUT OF SCOPE)
- Notification on pipeline failure (email, Slack) -- v2
- CI/CD with pre-built images on a registry -- over-engineering for single-VPS
- Monitoring/alerting (Prometheus, Grafana) -- v2
- Automatic model comparison (staged vs current) with metrics diff before reload -- v2
- HTTPS redirect at app nginx level (vs VPS nginx level) -- not needed with VPS nginx handling SSL
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | Weekly refresh automatically fetches new game data and recomputes features on a schedule (APScheduler) | APScheduler 3.x BlockingScheduler with CronTrigger already implemented in `pipeline/worker.py` -- no changes needed. Worker container runs steps 1-2 (ingest + feature recompute) on Tuesday 6 AM UTC |
| PIPE-02 | Weekly refresh automatically retrains and stages a candidate model on updated data -- staged only, not live until manual approval | Pipeline step 3 (retrain_and_stage) in `pipeline/refresh.py` -- needs MLflow removal only. Writes candidate model to shared `models` volume; non-fatal failure mode ensures predictions still run |
| PIPE-03 | New model is staged but not live until POST /model/reload is called manually -- human approval gate | Already implemented in `api/routes/model.py` (Phase 4). Worker writes to shared `models` volume, API reads on reload. No new code needed, just correct volume mounting |
| PIPE-04 | Full stack runs under Docker Compose: postgres, api, worker, nginx services | Docker Compose with 4 services; health checks + depends_on ordering; named volumes for persistence. Updated from original requirement's 5 services (MLflow removed) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docker Compose | v2 (built-in) | Service orchestration | Standard for multi-container apps on single host |
| nginx | alpine (1.29.x) | App-level reverse proxy + SPA server | Standard production web server; dual-layer architecture with VPS nginx |
| node | 20-alpine (20.20.x) | Frontend build stage | LTS version matching `frontend/package.json` dev environment |
| PostgreSQL | 16-alpine | Primary database | Already in use, unchanged |
| APScheduler | 3.x (already installed) | Cron-based job scheduling | Already implemented in `pipeline/worker.py`, no changes needed |
| Certbot | (VPS system) | SSL certificate provisioning | Standard Let's Encrypt client for VPS system nginx |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python:3.11-slim | (already in Dockerfile) | Python app runtime | Base image for api and worker services |
| tenacity | (already installed) | Retry logic for data fetching | Already used in data/loaders.py, no changes needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| nginx (app container) | Caddy | Caddy has auto-SSL but VPS already has nginx + Certbot; nginx avoids mixing proxy technologies |
| Multi-stage nginx.Dockerfile | Pre-commit `npm run build` | Multi-stage keeps build artifacts out of git; self-contained builds |
| VPS system nginx + Certbot | Traefik | Traefik is container-native but VPS already runs nginx for other sites |

**Version verification:**
- nginx: `alpine` tag currently resolves to 1.29.6 on Docker Hub (March 2026)
- node: `20-alpine` tag currently resolves to 20.20.1 on Docker Hub (March 2026)
- PostgreSQL: `16-alpine` already in docker-compose.yml, unchanged
- APScheduler: 3.x already in pyproject.toml (`>=3.10,<4.0`), no version change needed

## Architecture Patterns

### Recommended Project Structure (files to create/modify)
```
project-root/
|-- docker-compose.yml          # MODIFY: 4 services (was 5), 2 volumes (was 4)
|-- Dockerfile                  # MODIFY: add entrypoint.sh COPY + ENTRYPOINT
|-- .dockerignore               # MODIFY: add frontend/node_modules, frontend/dist
|-- .env.example                # MODIFY: remove DOMAIN, keep POSTGRES_PASSWORD/RELOAD_TOKEN/REFRESH_CRON_HOUR
|-- pyproject.toml              # MODIFY: remove mlflow dependency
|-- docker/
|   |-- nginx.Dockerfile        # CREATE: multi-stage Node+nginx build
|   |-- nginx.conf              # CREATE: SPA try_files + /api/ proxy_pass
|   +-- entrypoint.sh           # CREATE: model volume seeding script
|-- models/train.py             # MODIFY: strip MLflow imports, setup_mlflow(), mlflow.start_run block
|-- pipeline/refresh.py         # MODIFY: strip MLflow import, setup block, setup_mlflow from imports
|-- tests/models/test_logging.py # MODIFY: remove MLflow tests (TestMlflowLogging class)
|-- mlflow.Dockerfile           # DELETE
+-- Caddyfile                   # DELETE
```

### Pattern 1: Multi-Stage nginx.Dockerfile (Frontend Build + Serve)
**What:** Two-stage Dockerfile: Stage 1 uses node:20-alpine to build the Vite React app; Stage 2 uses nginx:alpine to serve the static output and proxy API requests.
**When to use:** When the frontend should not be pre-built or committed to git.
**Example:**
```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
```
**Key details:**
- Build context for this Dockerfile must be the project root (needs `frontend/` directory)
- `npm run build` command is `tsc -b && vite build` (from package.json scripts)
- Vite outputs to `frontend/dist/` by default
- The nginx default.conf is replaced entirely with our custom config

### Pattern 2: nginx.conf for SPA + API Proxy
**What:** nginx configuration that serves the SPA with `try_files` fallback to `index.html` for client-side routing, and proxies `/api/` requests to the FastAPI backend container.
**When to use:** When nginx serves both static frontend and proxies to a backend in Docker Compose.
**Example:**
```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # SPA client-side routing: try the file, then directory, then fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression for text assets
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 256;
}
```
**Key details:**
- `server_name _;` is a catch-all -- the VPS system nginx handles domain routing
- `try_files $uri $uri/ /index.html` enables React Router's client-side navigation
- `/api/` location block uses Docker Compose service name `api` as hostname (DNS resolution within compose network)
- Proxy headers are standard: Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
- Gzip compression reduces payload sizes for text assets

### Pattern 3: VPS System nginx Reverse Proxy Server Block
**What:** A server block file on the VPS system nginx that proxies the subdomain to the Docker Compose app's nginx container on localhost:8080.
**When to use:** When the VPS already runs nginx for other sites and the app needs its own subdomain.
**Example:**
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
# After running: sudo certbot --nginx -d nostradamus.silverreyes.net
# Certbot modifies this block to add:
#   listen 443 ssl;
#   ssl_certificate /etc/letsencrypt/live/nostradamus.silverreyes.net/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/nostradamus.silverreyes.net/privkey.pem;
#   include /etc/letsencrypt/options-ssl-nginx.conf;
#   ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
# And adds a separate server block for 80->443 redirect.
```
**File location:** `/etc/nginx/sites-available/nostradamus.silverreyes.net`
**Activation:** `sudo ln -s /etc/nginx/sites-available/nostradamus.silverreyes.net /etc/nginx/sites-enabled/`

### Pattern 4: Entrypoint Volume Seeding
**What:** Shell script that copies seed files from the Docker image to a named volume on first boot, then exec's the CMD.
**When to use:** When pre-trained model artifacts need to populate a shared named volume before the app starts.
**Example:**
```sh
#!/bin/sh
# Seed models volume on first boot if volume is empty
MODEL_VOL="/app/models-vol"
if [ ! -f "$MODEL_VOL/best_model.json" ]; then
    echo "[entrypoint] Seeding models volume from image..."
    cp /app/models/artifacts/best_model.json "$MODEL_VOL/" || echo "[entrypoint] WARNING: failed to copy best_model.json"
    cp /app/models/experiments.jsonl "$MODEL_VOL/" || echo "[entrypoint] WARNING: failed to copy experiments.jsonl"
fi
exec "$@"
```
**Key details:**
- `exec "$@"` replaces the shell process with the CMD, ensuring the CMD process becomes PID 1 and receives signals (SIGTERM for graceful shutdown)
- The seeding check uses `[ ! -f "$MODEL_VOL/best_model.json" ]` -- idempotent, won't overwrite on restarts
- Both `api` and `worker` services run this entrypoint, but only the `worker` has write access to the volume so only the worker's entrypoint copy actually succeeds on first boot
- The API mounts the volume as read-only (`:ro`), so its entrypoint seed attempt will silently fail if the volume is already populated by the worker (which starts first via depends_on chain: postgres -> worker starts, postgres -> api starts). If worker hasn't populated yet, the API entrypoint will fail the copy but the API's lifespan handles a missing model gracefully (sets `app_state["model"] = None`)

**IMPORTANT:** The worker service does NOT depend on api, so both worker and api start after postgres becomes healthy. The worker is the one that should seed the volume since it has write access. The `api` service mounts read-only and will simply skip seeding (the `cp` will fail silently with the `||` guard). This is fine because the API already handles a missing model file gracefully in its lifespan handler.

### Pattern 5: ENTRYPOINT + CMD Interaction
**What:** Dockerfile `ENTRYPOINT` wraps the `CMD` from docker-compose.yml.
**When to use:** When the same image needs pre-startup logic (volume seeding) regardless of which CMD is used.
**Example:**
```dockerfile
# In Dockerfile (runtime stage)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
```yaml
# In docker-compose.yml, CMD is overridden per service:
services:
  api:
    command: ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  worker:
    command: ["python", "-m", "pipeline.worker"]
```
**How it works:** Docker combines ENTRYPOINT and CMD into a single command. When compose overrides `command:`, it replaces CMD but ENTRYPOINT stays. So `worker` actually runs `/entrypoint.sh python -m pipeline.worker`, which seeds the volume then `exec`s the worker process.

### Anti-Patterns to Avoid
- **Running cron on the host:** Breaks containerization; APScheduler inside the worker container is already implemented and correct
- **Installing curl in slim Python images for health checks:** Use Python-based health checks (`python -c "import urllib.request; urllib.request.urlopen(...)"`) -- already done
- **Committing frontend/dist/ to git:** Multi-stage Docker build handles this; dist/ should be in .dockerignore
- **Mixing SSL termination layers:** SSL is at VPS system nginx ONLY; app nginx container stays plain HTTP
- **Using `CMD` shell form:** Always use exec form `CMD ["python", "-m", "pipeline.worker"]` so the process is PID 1 and receives SIGTERM

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSL certificate management | Custom certbot scripts inside container | VPS system nginx + `certbot --nginx` | Certbot auto-modifies nginx config, handles renewal via systemd timer |
| Frontend build pipeline in CI | Custom build scripts, committed dist/ | Multi-stage Docker build | Self-contained, reproducible, no Node.js needed on host |
| Volume initialization | Init containers, manual docker cp | Entrypoint script with first-boot check | Runs automatically, idempotent, standard Docker pattern |
| Health check ordering | wait-for-it scripts | Docker Compose `depends_on: condition: service_healthy` | Native Docker Compose feature, already configured |
| API readiness probe | curl/wget in slim image | `python -c "import urllib.request; ..."` | No extra deps, already implemented |

**Key insight:** All infrastructure in this phase uses standard Docker and nginx patterns. The only custom code changes are MLflow removal (deletion, not creation) and new configuration files (nginx.conf, entrypoint.sh, nginx.Dockerfile).

## Common Pitfalls

### Pitfall 1: Frontend Build Failure in Docker (Missing package-lock.json)
**What goes wrong:** `npm ci` fails because `package-lock.json` is missing or not copied into the build stage.
**Why it happens:** `npm ci` requires an exact `package-lock.json` (unlike `npm install`). If only `package.json` is copied, it fails.
**How to avoid:** Copy both `package.json` and `package-lock.json` in the COPY step before `npm ci`. Verify `package-lock.json` exists in the `frontend/` directory.
**Warning signs:** Docker build fails at the `npm ci` step with "npm ERR! The `npm ci` command can only install with an existing package-lock.json".

### Pitfall 2: nginx.Dockerfile Build Context
**What goes wrong:** The nginx.Dockerfile can't find `frontend/` because the build context is wrong.
**Why it happens:** If `build: docker/nginx.Dockerfile` is used without specifying context, Docker uses the `docker/` directory as context, not the project root.
**How to avoid:** In docker-compose.yml, set both `context: .` (project root) and `dockerfile: docker/nginx.Dockerfile`:
```yaml
nginx:
  build:
    context: .
    dockerfile: docker/nginx.Dockerfile
```
**Warning signs:** Docker build error "COPY failed: file not found in build context".

### Pitfall 3: CORS_ORIGINS Not Including Production Domain
**What goes wrong:** API returns CORS errors when accessed from the production domain.
**Why it happens:** `api/config.py` has `CORS_ORIGINS` hardcoded to `["http://localhost:3000", "http://localhost:5173"]`.
**How to avoid:** This is NOT actually a problem. The frontend uses relative URLs (`/api/...`) and is served by the same nginx container that proxies to the API. All requests are same-origin from the browser's perspective. CORS headers are only needed for cross-origin requests (e.g., direct API access from a different domain). The hardcoded localhost values only matter for local development.
**Warning signs:** None expected in production. Only an issue if someone tries to call the API from a different domain.

### Pitfall 4: Docker CMD Shell Form vs Exec Form (Signal Handling)
**What goes wrong:** Worker container ignores SIGTERM on `docker stop`, waits 10 seconds, then gets SIGKILL.
**Why it happens:** Shell form `CMD python -m pipeline.worker` runs under `/bin/sh` as PID 1. Python process never receives SIGTERM.
**How to avoid:** Use exec form: `CMD ["python", "-m", "pipeline.worker"]`. Already correct in current docker-compose.yml.
**Warning signs:** `docker stop` takes exactly 10 seconds (default grace period).

### Pitfall 5: PostgreSQL Init Scripts Only Run on Empty Data Volume
**What goes wrong:** After modifying `sql/init.sql`, the changes don't take effect because `pgdata` volume already has data.
**Why it happens:** PostgreSQL only runs `docker-entrypoint-initdb.d` scripts when initializing a new data directory.
**How to avoid:** For fresh deployments (VPS), this is not an issue -- first `docker compose up` runs init.sql. For existing local dev environments, manually apply schema changes.
**Warning signs:** Tables or databases expected from init.sql don't exist.

### Pitfall 6: Entrypoint Seeding Race Condition
**What goes wrong:** API starts before worker seeds the volume, finds no model file.
**Why it happens:** Both api and worker start after postgres is healthy; api might check for the model before worker copies it.
**How to avoid:** The API already handles this gracefully in its lifespan handler -- if `load_best_model` raises `FileNotFoundError`, it sets `app_state["model"] = None`. The API returns 503 until the model is available. Additionally, both services run the entrypoint, so whichever starts first seeds the volume (worker has write access, api's attempt will succeed too since the volume is read-write at the filesystem level during the entrypoint, before the `:ro` mount takes effect... actually, `:ro` is enforced at mount time, so only the worker can seed). In practice, the worker seeds on first boot, and the API will either find the model or handle its absence.
**Warning signs:** API returns 503 on model endpoints immediately after deployment, resolves after worker starts.

### Pitfall 7: MLflow Import Left Behind in Tests
**What goes wrong:** Tests fail after MLflow removal because `tests/models/test_logging.py` still imports `mlflow` and `setup_mlflow`.
**Why it happens:** MLflow removal focuses on production code but tests also import MLflow directly.
**How to avoid:** The test file `tests/models/test_logging.py` must be updated: remove `import mlflow`, remove `from models.train import ... setup_mlflow`, remove the entire `TestMlflowLogging` class (3 tests), and update `TestJsonlLogging` tests to not call MLflow setup.
**Warning signs:** `pytest tests/models/test_logging.py` fails with `ModuleNotFoundError: No module named 'mlflow'` after removing mlflow from pyproject.toml.

### Pitfall 8: .dockerignore Missing frontend/node_modules
**What goes wrong:** Docker build copies `frontend/node_modules/` into the build context, making the build slow and bloated.
**Why it happens:** Current `.dockerignore` has `frontend/node_modules` but this only affects the Python app Dockerfile. The nginx.Dockerfile also needs this ignored.
**How to avoid:** Verify `.dockerignore` includes `frontend/node_modules` and `frontend/dist` -- it already has `frontend/node_modules`. Add `frontend/dist` if missing. Both Dockerfiles share the `.dockerignore` when using project root as build context.
**Warning signs:** Docker build takes unexpectedly long; image size is hundreds of MB larger than expected.

## Code Examples

### MLflow Removal: models/train.py -- Exact Surgery

**Lines to delete (verified against current file):**

1. **Line 20:** `import mlflow` -- delete entire line
2. **Lines 33-40:** `def setup_mlflow():` function -- delete entire function (8 lines)
3. **Lines 237-253:** MLflow logging block inside `log_experiment()` -- delete the `with mlflow.start_run(...)` block and all its contents. The function stays; it still writes to experiments.jsonl (lines 211-234).
4. **Line 375:** `setup_mlflow()` call in `run_experiment()` -- delete this line
5. **Docstrings:** Update function/module docstrings to remove references to "MLflow" and "dual logging"

**After removal, `log_experiment()` becomes:**
```python
def log_experiment(
    experiment_id, params, features_used, val_acc_2023, val_acc_2022, val_acc_2021,
    baseline_home, baseline_record, log_loss_val, brier_score_val, shap_top5,
    keep, hypothesis, prev_best_acc, model_path, jsonl_path="models/experiments.jsonl",
):
    entry = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # ... all existing fields ...
    }
    # Append to JSONL (append-only, CLAUDE.md rule)
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    # MLflow block REMOVED -- was here
```

**Exports affected:** `setup_mlflow` is no longer exported. Update any imports of it.

### MLflow Removal: pipeline/refresh.py -- Exact Surgery

**Lines to delete (verified against current file):**

1. **Line 8:** `import mlflow` -- delete entire line
2. **Lines 143-151:** Inside `retrain_and_stage()`, the import block:
   ```python
   from models.train import (
       DEFAULT_PARAMS,
       load_and_split,
       log_experiment,
       save_best_model,
       setup_mlflow,    # <-- REMOVE THIS LINE ONLY
       should_keep,
       train_and_evaluate,
   )
   ```
   Remove `setup_mlflow,` from the import list (line 148). Keep all other imports.
3. **Lines 154-159:** The MLflow setup block:
   ```python
   if os.environ.get("MLFLOW_TRACKING_URI"):
       mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
       mlflow.set_experiment("nfl-game-predictor")
   else:
       setup_mlflow()
   ```
   Delete these 5 lines entirely. Also remove the `import os` line ONLY IF no other code in the function uses `os` -- but `os.path.exists` is used at line 172, so keep `import os`.

### MLflow Removal: tests/models/test_logging.py -- Exact Surgery

**Changes needed (verified against current file):**

1. **Line 13:** `import mlflow` -- delete
2. **Line 16:** `from models.train import log_experiment, setup_mlflow` -- change to `from models.train import log_experiment`
3. **TestJsonlLogging class (lines 31-143):** Remove all `mlflow.set_tracking_uri(...)` and `mlflow.set_experiment(...)` calls from each test method. These were setup calls to prevent MLflow from polluting the project; after MLflow removal, they are unnecessary and will error.
4. **TestMlflowLogging class (lines 147-244):** Delete the entire class. All 3 test methods (`test_mlflow_logging`, `test_dual_logging_consistency`, and the MLflow-specific assertions) are no longer valid.

### MLflow Removal: pyproject.toml

**Line 17:** `"mlflow>=3.10.0",` -- delete this dependency. This reduces Docker image size significantly (mlflow pulls in many transitive dependencies).

### docker-compose.yml Rewrite (Target State)
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nflpredictor
      POSTGRES_USER: nfl
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-nfldev}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nfl"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: .
    command: ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    environment:
      DATABASE_URL: postgresql+psycopg://nfl:${POSTGRES_PASSWORD:-nfldev}@postgres:5432/nflpredictor
      MODEL_PATH: /app/models-vol/best_model.json
      EXPERIMENTS_PATH: /app/models-vol/experiments.jsonl
      RELOAD_TOKEN: ${RELOAD_TOKEN:-devtoken}
    volumes:
      - models:/app/models-vol:ro
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

  worker:
    build: .
    command: ["python", "-m", "pipeline.worker"]
    environment:
      DATABASE_URL: postgresql+psycopg://nfl:${POSTGRES_PASSWORD:-nfldev}@postgres:5432/nflpredictor
      MODEL_PATH: /app/models-vol/best_model.json
      EXPERIMENTS_PATH: /app/models-vol/experiments.jsonl
      REFRESH_CRON_HOUR: ${REFRESH_CRON_HOUR:-6}
    volumes:
      - models:/app/models-vol
    depends_on:
      postgres:
        condition: service_healthy

  nginx:
    build:
      context: .
      dockerfile: docker/nginx.Dockerfile
    ports:
      - "8080:80"
    depends_on:
      api:
        condition: service_healthy

volumes:
  pgdata:
  models:
```

**Changes from current docker-compose.yml:**
- REMOVED: `mlflow` service (entire block)
- REMOVED: `caddy` service (entire block)
- REMOVED: `mlartifacts` volume
- REMOVED: `caddy_data` volume
- REMOVED: `MLFLOW_TRACKING_URI` env var from `worker`
- ADDED: `nginx` service (build from `docker/nginx.Dockerfile`, port `8080:80`, depends_on api healthy)

### .dockerignore Updates
```
.git
.planning
data/cache
frontend/node_modules
frontend/dist
mlruns
__pycache__
*.pyc
.env
.claude
```
**Changes from current:** Add `frontend/dist`, `.claude` (currently has `frontend/node_modules` already).

### .env.example Update
```
# PostgreSQL (single source of truth for password)
POSTGRES_PASSWORD=changeme_generate_strong_password

# API model reload authorization token
RELOAD_TOKEN=changeme_generate_random_token

# Worker schedule (hour in UTC, default 6 = midnight Central)
REFRESH_CRON_HOUR=6
```
**Changes from current:** Remove `DOMAIN=localhost` line (was for Caddy, no longer needed).

### Docker Install on VPS (Ubuntu)
```sh
# Install Docker Engine via convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER
newgrp docker

# Verify docker-compose-plugin is installed (included with convenience script)
docker compose version
# If not present:
# sudo apt-get install -y docker-compose-plugin
```
Source: [Docker Engine Install - Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

### Dockerfile Modifications (Entrypoint Addition)
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install \
    $(python -c "import tomllib; print(' '.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))")

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
# Volume seeding entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
**Changes from current Dockerfile:** Added 3 lines (COPY entrypoint.sh, RUN chmod, ENTRYPOINT). Note that the `COPY . .` already copies `docker/entrypoint.sh` into the image at `/app/docker/entrypoint.sh`, but we also copy it to `/entrypoint.sh` for a clean path.

### Frontend API URL Configuration
The frontend already uses relative URLs correctly:
```typescript
// frontend/src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL ?? "";
// Empty string = relative URLs like /api/predictions/current
```
No changes needed. The nginx container serves both the frontend and proxies `/api/` to FastAPI, making all requests same-origin.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Caddy auto-SSL in container | VPS system nginx + Certbot | This phase (CONTEXT.md update) | VPS already runs nginx for other sites; consistent proxy layer |
| MLflow as tracking service | JSONL-only logging | This phase (CONTEXT.md update) | Simpler stack, fewer services, no psycopg2 issues |
| Pre-built frontend/dist/ in git | Multi-stage Docker build | This phase (CONTEXT.md update) | Cleaner repo, reproducible builds |
| 5 Docker services | 4 Docker services | This phase (CONTEXT.md update) | Reduced resource usage, simpler compose file |
| docker-compose v1 (Python) | docker compose v2 (built-in) | Docker Compose v2 (2022) | Built into Docker CLI, no separate install |

**Deprecated/outdated:**
- `docker-compose` (hyphenated, Python v1) is deprecated. Use `docker compose` (space, Go v2). All commands in the VPS bootstrap use the v2 syntax.
- MLflow as a service is being removed for this project. JSONL logging remains as the single experiment tracking mechanism.
- Caddy is being removed. The existing `Caddyfile` and references to Caddy should be deleted.

## Open Questions

1. **CORS_ORIGINS for Production**
   - What we know: `api/config.py` has CORS_ORIGINS hardcoded to localhost:3000 and localhost:5173. In production behind nginx, all requests are same-origin (relative URLs), so CORS is not needed.
   - What's unclear: Whether to add the production domain to CORS_ORIGINS for potential direct API access.
   - Recommendation: Leave as-is. Same-origin requests from the nginx-served frontend don't trigger CORS. If direct API access from other domains is needed in v2, add an env-var-based CORS_ORIGINS at that time.

2. **package-lock.json Existence**
   - What we know: `npm ci` requires `package-lock.json` to exist. The `frontend/package.json` exists.
   - What's unclear: Whether `package-lock.json` is committed to git.
   - Recommendation: Verify `package-lock.json` exists in `frontend/`. If not, generate it with `cd frontend && npm install` before the Docker build. This should be a Wave 0 check.

3. **Worker Volume Seeding with Read-Only API Mount**
   - What we know: API mounts the models volume as `:ro`. Worker mounts it as read-write. Both run the entrypoint.
   - What's unclear: Whether Docker's `:ro` mount prevents the entrypoint `cp` from writing (it should, since `:ro` is enforced at mount time, not after container start).
   - Recommendation: Only the worker can seed the volume. The API's entrypoint will fail the `cp` silently (due to `|| echo` guard). The API handles missing model files gracefully. This is the intended behavior.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configured in pyproject.toml) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ features/tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Weekly refresh ingests data + recomputes features | unit | `pytest tests/test_pipeline.py::test_ingest_new_data_calls_loaders_and_upserts -x` | Yes (existing) |
| PIPE-01 | APScheduler CronTrigger configuration | unit | `pytest tests/test_pipeline.py::test_worker_schedule_config -x` | Yes (existing) |
| PIPE-02 | Retrain stages candidate model, non-fatal failure | unit | `pytest tests/test_pipeline.py::test_retrain_nonfatal_in_run_pipeline -x` | Yes (existing) |
| PIPE-03 | Staged model not live until reload | integration | `pytest tests/api/test_model.py -x` | Yes (existing) |
| PIPE-04 | Docker Compose starts all 4 services | smoke | `docker compose up -d && docker compose ps` | Manual verification |
| PIPE-04 | Health checks pass for all services | smoke | `docker compose ps --format json` | Manual verification |
| N/A | MLflow removal -- log_experiment still writes JSONL | unit | `pytest tests/models/test_logging.py -x` | Yes (needs update) |
| N/A | MLflow removed from pipeline test | unit | `pytest tests/test_pipeline.py::test_mlflow_tracking_uri_override -x` | Yes (needs deletion or rewrite) |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q` (quick unit test pass)
- **Per wave merge:** `pytest tests/ features/tests/ -v` (full suite)
- **Phase gate:** Full suite green + `docker compose up -d` smoke test

### Wave 0 Gaps
- [ ] `tests/models/test_logging.py` -- needs MLflow removal: delete `TestMlflowLogging` class, remove mlflow imports/setup from `TestJsonlLogging`
- [ ] `tests/test_pipeline.py::test_mlflow_tracking_uri_override` -- needs deletion (tests MLflow URI override which no longer exists)
- [ ] Verify `frontend/package-lock.json` exists (required for `npm ci` in Docker build)

## Sources

### Primary (HIGH confidence)
- [Docker Engine Install - Ubuntu](https://docs.docker.com/engine/install/ubuntu/) - Convenience script and docker-compose-plugin installation
- [Docker Compose Install](https://docs.docker.com/compose/install/linux/) - Compose plugin installation via apt
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/) - ENTRYPOINT/CMD interaction, exec form behavior
- [Docker Volumes](https://docs.docker.com/engine/storage/volumes/) - Named volume behavior, first-boot initialization
- [nginx Docker Hub](https://hub.docker.com/_/nginx) - Official nginx:alpine image, version 1.29.6
- [node Docker Hub](https://hub.docker.com/_/node) - Official node:20-alpine image, version 20.20.1
- Project codebase: `docker-compose.yml`, `Dockerfile`, `models/train.py`, `pipeline/refresh.py`, `pipeline/worker.py`, `api/main.py`, `api/config.py`, `frontend/package.json`, `frontend/src/lib/api.ts`, `tests/models/test_logging.py`, `tests/test_pipeline.py`

### Secondary (MEDIUM confidence)
- [Serve SPA with API via nginx reverse proxy](https://dev.to/___bn___/serve-a-single-page-application-along-with-its-backend-api-thanks-to-nginx-reverse-proxy-2h5c) - nginx SPA + API proxy pattern
- [Containerizing SPA with Multi-Stage nginx Build](https://dev.to/it-wibrc/guide-to-containerizing-a-modern-javascript-spa-vuevitereact-with-a-multi-stage-nginx-build-1lma) - Multi-stage Dockerfile pattern for Vite/React
- [DigitalOcean: Nginx Reverse Proxy on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-configure-nginx-as-a-reverse-proxy-on-ubuntu-22-04) - VPS nginx reverse proxy + Certbot
- [Docker Blog: How to Dockerize React App](https://www.docker.com/blog/how-to-dockerize-react-app/) - Official Docker guide for React containerization

### Tertiary (LOW confidence)
- None -- all findings verified against official docs or project source code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components are stable, well-documented; versions verified against Docker Hub
- Architecture: HIGH - Patterns directly from nginx docs, Docker docs, and verified project code analysis
- MLflow removal: HIGH - Exact line numbers verified against current source files; all affected files identified
- Pitfalls: HIGH - Each pitfall verified by reading actual source code (e.g., CORS_ORIGINS, api.ts API_BASE, lifespan handler)
- VPS deployment: MEDIUM - Standard Docker install + nginx patterns; VPS-specific details depend on actual server state

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (30 days -- all components are stable releases)
