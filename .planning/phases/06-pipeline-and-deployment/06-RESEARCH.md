# Phase 6: Pipeline and Deployment - Research

**Researched:** 2026-03-17
**Domain:** Docker Compose orchestration, APScheduler-based worker pipeline, Caddy reverse proxy, MLflow server deployment
**Confidence:** HIGH

## Summary

Phase 6 transforms the existing NFL Game Predictor from a locally-run development project into a production-ready, Docker Compose-orchestrated system with five services (postgres, api, worker, mlflow, caddy). The project already has all application code in place -- data ingestion, feature engineering, model training, prediction generation, FastAPI API, and a React dashboard. This phase is purely infrastructure: containerization, orchestration, scheduling, and deployment automation.

The critical complexity lies in three areas: (1) the multi-service Docker Compose configuration with health checks, dependency ordering, and shared named volumes; (2) the APScheduler-based worker process that orchestrates a four-step weekly pipeline with mixed failure modes (steps 1-2 strict, step 3 non-fatal, step 4 always-runs); and (3) the MLflow server configuration requiring a custom Docker image since the official `ghcr.io/mlflow/mlflow` image lacks PostgreSQL drivers.

**Primary recommendation:** Build a single multi-stage Dockerfile for the Python app (shared by api and worker services), a minimal custom Dockerfile for MLflow (adding psycopg2-binary to the official image), and a Caddyfile that serves the pre-built `frontend/dist/` files at root while proxying `/api/*` to the FastAPI container.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Single Dockerfile for the Python app, run as two services: `api` (uvicorn) and `worker` (APScheduler)
- Different entrypoints: `api` runs uvicorn, `worker` runs the scheduler loop
- Separate manual entry point (`pipeline.refresh`) for one-shot runs via `docker compose exec`
- MLflow runs as a dedicated service using the official `ghcr.io/mlflow/mlflow` image
- Caddy replaces nginx as the edge proxy (auto-SSL)
- Caddy serves `frontend/dist/` static files and proxies `/api/*` to the FastAPI container
- MLflow server backed by PostgreSQL (separate `mlflow` database on the same postgres instance)
- `CREATE DATABASE mlflow;` added to `init.sql`
- MLflow backend URI: `postgresql://nfl:${POSTGRES_PASSWORD}@postgres:5432/mlflow`
- Artifacts stored on the `mlartifacts` named volume
- MLflow stays internal-only -- not publicly proxied through Caddy. Access via SSH tunnel
- Named volumes: `pgdata`, `mlartifacts`, `models`, `caddy_data`
- Single writer principle: only the worker process writes to experiments.jsonl
- Native Docker Compose health checks with `depends_on: condition: service_healthy`
- Postgres health check: `pg_isready -U nfl`
- API health check: Python-based (avoids curl dependency in slim images)
- Dependency chain: postgres -> api, postgres -> mlflow, postgres -> worker, api -> caddy
- APScheduler with CronTrigger inside the worker container
- Default schedule: Tuesday 6 AM UTC (midnight Central)
- Schedule configurable via `REFRESH_CRON_HOUR` env var
- Pipeline sequence: ingest -> recompute features -> retrain (non-fatal) -> generate predictions
- Staleness check: verify Monday night's game results are present before proceeding
- Step 3 (retrain) is non-fatal: if it fails, log error, skip, continue to step 4
- Step 4 always runs if steps 1-2 succeeded
- Staged model does NOT go live automatically -- human calls POST /model/reload
- Single `.env` file at project root (gitignored) with actual secrets
- `.env.example` committed with placeholder values as template
- `POSTGRES_PASSWORD` is the single source for password -- database URLs constructed in docker-compose.yml
- Caddy with automatic Let's Encrypt SSL certificate provisioning
- `caddy_data` volume persists certificates across container rebuilds
- VPS bootstrap: install Docker, git clone, cp .env.example .env, verify DNS, docker compose up -d, first run interactively

### Claude's Discretion
- Multi-stage Dockerfile optimization (build vs runtime layers)
- Exact Caddy container image version
- Log format and log rotation strategy
- Worker process management (signal handling, graceful shutdown)
- APScheduler job store configuration (in-memory vs PostgreSQL-backed)
- Exact tenacity retry parameters (count, backoff, jitter)

### Deferred Ideas (OUT OF SCOPE)
- Notification on pipeline failure (email, Slack, etc.)
- CI/CD pipeline with pre-built images on a registry
- Monitoring/alerting (Prometheus, Grafana)
- Automatic model comparison (staged vs current) with metrics diff before reload
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | Weekly refresh automatically fetches new game data and recomputes features on a schedule (APScheduler) | APScheduler 3.11.x BlockingScheduler with CronTrigger; worker container runs pipeline steps 1-2 (ingest + feature recompute) on Tuesday 6 AM UTC schedule |
| PIPE-02 | Weekly refresh automatically retrains and stages a candidate model on updated data -- staged only, not live until manual approval | Pipeline step 3 (retrain_and_stage) writes candidate model to shared `models` volume; non-fatal failure mode ensures predictions still run even if retraining fails |
| PIPE-03 | New model is staged but not live until POST /model/reload is called manually -- human approval gate | Already implemented in api/routes/model.py (Phase 4); worker writes to shared `models` volume, API reads on reload; no new code needed, just correct volume mounting |
| PIPE-04 | Full stack runs under Docker Compose: postgres, api, mlflow, frontend, worker services | Docker Compose with 5 services (postgres, api, mlflow, caddy, worker); health checks + depends_on ordering; named volumes for persistence |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docker Compose | v2 (built-in) | Service orchestration | Standard for multi-container apps on single host |
| APScheduler | 3.11.x | Cron-based job scheduling in worker | Mature, stable, BlockingScheduler ideal for dedicated process |
| Caddy | 2.11.x | Edge proxy with auto-SSL | Zero-config Let's Encrypt, simpler than nginx for single-site |
| MLflow | 3.10.x | Experiment tracking server | Already used locally; moving to server mode with PostgreSQL backend |
| PostgreSQL | 16-alpine | Primary database (+ MLflow backend) | Already in use; adding second database for MLflow |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg2-binary | latest | PostgreSQL driver for MLflow image | Required -- official MLflow image lacks PostgreSQL support |
| tenacity | (already installed) | Retry logic for data fetching | Already used in data/loaders.py; reuse for pipeline staleness checks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler | cron (system) | cron requires host-level config; APScheduler keeps everything in Python/Docker |
| Caddy | nginx | nginx requires manual cert management; Caddy auto-provisions SSL |
| BlockingScheduler | AsyncIOScheduler | AsyncIO unnecessary -- worker is a dedicated process, no web server |

**Installation:**
```bash
# Add to pyproject.toml dependencies
pip install "APScheduler>=3.10,<4.0"

# MLflow custom image installs psycopg2-binary at build time
```

**Version verification:**
- APScheduler: 3.11.2 on PyPI (confirmed via pypi.org, March 2026)
- Caddy: 2.11.2 on Docker Hub (confirmed via hub.docker.com, March 2026)
- MLflow: 3.10.1 on PyPI and ghcr.io (confirmed via pypi.org, March 2026)
- PostgreSQL: 16-alpine already in use in current docker-compose.yml

## Architecture Patterns

### Recommended Project Structure
```
project-root/
|-- docker-compose.yml          # Full 5-service orchestration
|-- Dockerfile                  # Multi-stage: Python app (api + worker)
|-- Caddyfile                   # Edge proxy configuration
|-- mlflow.Dockerfile           # Custom MLflow image with psycopg2
|-- .env.example                # Template (committed)
|-- .env                        # Real secrets (gitignored, already exists)
|-- sql/
|   +-- init.sql                # DDL + CREATE DATABASE mlflow
|-- pipeline/
|   |-- __init__.py
|   |-- refresh.py              # Pipeline steps (ingest, features, retrain, predict)
|   +-- worker.py               # APScheduler entrypoint (CronTrigger + signal handling)
|-- api/                        # (existing) FastAPI application
|-- models/                     # (existing) Training and prediction code
|-- data/                       # (existing) Ingestion and data loading
|-- features/                   # (existing) Feature engineering
+-- frontend/
    +-- dist/                   # (existing) Pre-built React dashboard
```

### Pattern 1: Single Dockerfile, Two Services
**What:** One multi-stage Dockerfile produces a single image; docker-compose runs it twice with different entrypoints.
**When to use:** When two services share the same codebase and dependencies (api and worker here).
**Example:**
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Entrypoint set in docker-compose.yml per service
```

```yaml
# docker-compose.yml (relevant sections)
services:
  api:
    build: .
    command: ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  worker:
    build: .
    command: ["python", "-m", "pipeline.worker"]
```

### Pattern 2: APScheduler BlockingScheduler with Graceful Shutdown
**What:** Dedicated worker process using BlockingScheduler with SIGTERM signal handler for clean Docker stop.
**When to use:** When the scheduler is the sole purpose of the container.
**Example:**
```python
import signal
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = BlockingScheduler()

def shutdown(signum, frame):
    logger.info("Received shutdown signal, stopping scheduler...")
    scheduler.shutdown(wait=True)

def weekly_refresh():
    """Four-step pipeline with mixed failure modes."""
    # Step 1: Ingest (strict)
    # Step 2: Recompute features (strict)
    # Step 3: Retrain and stage (non-fatal)
    # Step 4: Generate predictions (always if steps 1-2 OK)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

scheduler.add_job(
    weekly_refresh,
    CronTrigger(day_of_week="tue", hour=6, timezone="UTC"),
    id="weekly_refresh",
    max_instances=1,
    replace_existing=True,
)
scheduler.start()
```

### Pattern 3: Caddy SPA + API Proxy
**What:** Caddy serves pre-built React files with SPA fallback, proxies API requests to backend.
**When to use:** Single-domain deployment with frontend and backend.
**Example:**
```
{$DOMAIN:localhost} {
    encode

    handle /api/* {
        reverse_proxy api:8000
    }

    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

### Pattern 4: PostgreSQL Init Script for Multiple Databases
**What:** Use `docker-entrypoint-initdb.d` scripts to create both the application database and the MLflow database.
**When to use:** When a single PostgreSQL instance serves multiple databases.
**Example:**
```sql
-- At the TOP of init.sql (before table creation)
-- Create MLflow database (runs as superuser during init)
SELECT 'CREATE DATABASE mlflow OWNER nfl'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow')\gexec
```
**Important note:** PostgreSQL init scripts in `docker-entrypoint-initdb.d` run against the default database (`nflpredictor` in this case). Creating a second database requires explicit SQL. The `\gexec` approach or a separate shell script handles this. Alternatively, a simpler approach is a shell script:
```bash
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE mlflow OWNER nfl;
EOSQL
```

### Anti-Patterns to Avoid
- **Running cron on the host:** Breaks containerization; use APScheduler inside the worker container.
- **Installing curl in slim Python images just for health checks:** Use Python-based health checks instead (`python -c "import urllib.request; urllib.request.urlopen(...)"`).
- **Sharing a single database for app and MLflow without separate databases:** MLflow creates its own tables and migrations; mixing with app tables creates confusion.
- **Exposing MLflow to the internet:** MLflow has no authentication by default; keep it internal-only, access via SSH tunnel.
- **Writing to experiments.jsonl from multiple processes:** Single writer principle -- only worker writes, API reads. Prevents file corruption.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSL certificate management | Custom certbot scripts | Caddy auto-SSL | Caddy handles issuance, renewal, OCSP stapling automatically |
| Cron scheduling in Docker | Host crontab + docker exec | APScheduler in worker container | Self-contained, Python-native, configurable via env vars |
| Health check ordering | Custom wait-for scripts | Docker Compose `depends_on: condition: service_healthy` | Native Docker Compose feature, no extra tooling |
| PostgreSQL readiness | Custom TCP probes | `pg_isready -U nfl` | Purpose-built tool included in postgres image |
| Process signal handling | Custom PID management | `signal.signal(SIGTERM, handler)` + `CMD ["python", ...]` (exec form) | Python stdlib + Docker exec form ensures PID 1 receives signals |

**Key insight:** Every infrastructure concern in this phase has a standard solution. The only custom code needed is the pipeline orchestration logic (`pipeline/refresh.py`) which wires together existing functions from `data/`, `features/`, `models/`.

## Common Pitfalls

### Pitfall 1: MLflow Official Image Missing PostgreSQL Drivers
**What goes wrong:** `ghcr.io/mlflow/mlflow` does not include `psycopg2` or `psycopg2-binary`. MLflow server fails to start with a connection error to the PostgreSQL backend store.
**Why it happens:** The official image is designed to be minimal; database drivers are opt-in.
**How to avoid:** Create a `mlflow.Dockerfile` that extends the official image and adds `pip install psycopg2-binary`.
**Warning signs:** MLflow container exits immediately with "No module named 'psycopg2'" or connection refused errors.

### Pitfall 2: Docker CMD Shell Form vs Exec Form (Signal Handling)
**What goes wrong:** Worker container ignores SIGTERM on `docker stop`, waits 10 seconds, then gets SIGKILL. In-flight pipeline step is killed ungracefully.
**Why it happens:** `CMD python -m pipeline.worker` (shell form) runs under `/bin/sh`, which becomes PID 1. The Python process (PID 2+) never receives SIGTERM.
**How to avoid:** Use exec form: `CMD ["python", "-m", "pipeline.worker"]` so Python is PID 1 and receives SIGTERM directly. Register SIGTERM handler in worker code.
**Warning signs:** `docker stop` takes exactly 10 seconds (the default grace period) instead of stopping quickly.

### Pitfall 3: Cache Invalidation for Weekly Data Refresh
**What goes wrong:** `data/loaders.py` caches Parquet files in `data/cache/`. The pipeline ingests new data but the cache returns stale data on subsequent calls.
**Why it happens:** The loaders check if `data/cache/pbp_{season}.parquet` exists and return it without checking freshness.
**How to avoid:** The pipeline's ingest step must either (a) delete the current season's cache files before re-downloading, or (b) bypass the cache entirely for the current season. Since the worker is the only process that refreshes data, it can safely delete `data/cache/pbp_{current_season}.parquet` and `data/cache/schedules_{current_season}.parquet` before calling the loaders.
**Warning signs:** Pipeline reports success but features/predictions don't reflect new game results.

### Pitfall 4: PostgreSQL Init Scripts Only Run on Empty Data Volume
**What goes wrong:** After updating `init.sql` to add `CREATE DATABASE mlflow`, rebuilding containers doesn't run the init script because `pgdata` volume already has data.
**Why it happens:** PostgreSQL Docker image only runs `docker-entrypoint-initdb.d` scripts when initializing a new data directory.
**How to avoid:** For existing deployments, manually run `CREATE DATABASE mlflow;` via `docker compose exec postgres psql -U nfl -c "CREATE DATABASE mlflow;"`. For fresh deployments, init.sql handles it.
**Warning signs:** MLflow container fails to connect because the `mlflow` database doesn't exist.

### Pitfall 5: Volume Permissions Between Containers
**What goes wrong:** Worker writes model artifacts to the `models` volume as one UID; API container running as a different UID can't read them.
**Why it happens:** Default user differs between container configurations.
**How to avoid:** Both api and worker use the same Dockerfile, so they run as the same user. Don't introduce USER directives that differ between services.
**Warning signs:** API returns 500 on `/model/reload` with "Permission denied" reading model file.

### Pitfall 6: MLflow setup_mlflow() Hardcodes File-Based Tracking
**What goes wrong:** `models/train.py` calls `setup_mlflow()` which sets `mlflow.set_tracking_uri("file:./mlruns")`. When running in Docker, this creates a local mlruns directory inside the container instead of using the MLflow tracking server.
**Why it happens:** The current code was written for local development.
**How to avoid:** The worker's retrain step should set `MLFLOW_TRACKING_URI` environment variable to `http://mlflow:5000` before importing/calling training code, OR override the tracking URI in the pipeline's retrain wrapper. The `setup_mlflow()` function should respect the `MLFLOW_TRACKING_URI` env var if set.
**Warning signs:** MLflow server dashboard shows no runs while experiments.jsonl has entries.

### Pitfall 7: Frontend API URL Hardcoded to localhost
**What goes wrong:** React dashboard makes API calls to `http://localhost:5173/api/...` or similar dev URL in production.
**Why it happens:** Vite dev server proxy or hardcoded base URLs.
**How to avoid:** Frontend API client should use relative URLs (`/api/...`) which Caddy proxies. Verify the frontend build uses relative paths, not absolute localhost URLs.
**Warning signs:** Dashboard shows loading spinners indefinitely in production.

## Code Examples

### Pipeline Refresh Module Structure
```python
# pipeline/refresh.py
"""Weekly pipeline: ingest -> features -> retrain -> predict."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_pipeline():
    """Execute the four-step weekly refresh pipeline.

    Steps 1-2: Strict stop-on-failure (data must be fresh)
    Step 3: Non-fatal (retraining is opportunistic)
    Step 4: Always runs if steps 1-2 succeeded
    """
    logger.info("Pipeline started at %s", datetime.utcnow().isoformat())

    # Step 1: Ingest new data
    try:
        ingest_new_data()
    except Exception:
        logger.exception("Step 1 FAILED: ingest_new_data")
        return  # Hard stop

    # Step 2: Recompute features
    try:
        recompute_features()
    except Exception:
        logger.exception("Step 2 FAILED: recompute_features")
        return  # Hard stop

    # Step 3: Retrain and stage (NON-FATAL)
    try:
        retrain_and_stage()
    except Exception:
        logger.exception("Step 3 FAILED (non-fatal): retrain_and_stage -- continuing to predictions")

    # Step 4: Generate predictions (always runs if data is fresh)
    try:
        generate_current_predictions()
    except Exception:
        logger.exception("Step 4 FAILED: generate_predictions")

    logger.info("Pipeline completed at %s", datetime.utcnow().isoformat())
```

### Worker Entrypoint with Signal Handling
```python
# pipeline/worker.py
"""APScheduler-based worker entrypoint for Docker container."""
import os
import signal
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pipeline.refresh import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler()

def shutdown(signum, frame):
    logger.info("Received signal %s, shutting down scheduler...", signum)
    scheduler.shutdown(wait=True)

def main():
    cron_hour = int(os.environ.get("REFRESH_CRON_HOUR", "6"))

    scheduler.add_job(
        run_pipeline,
        CronTrigger(day_of_week="tue", hour=cron_hour, timezone="UTC"),
        id="weekly_refresh",
        max_instances=1,
        replace_existing=True,
    )

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info("Worker started. Next refresh: Tuesday %02d:00 UTC", cron_hour)
    scheduler.start()

if __name__ == "__main__":
    main()
```

### Docker Compose Service Definitions (Structural Pattern)
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nflpredictor
      POSTGRES_USER: nfl
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
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
      DATABASE_URL: postgresql+psycopg://nfl:${POSTGRES_PASSWORD}@postgres:5432/nflpredictor
      MODEL_PATH: /app/models-vol/best_model.json
      EXPERIMENTS_PATH: /app/models-vol/experiments.jsonl
      RELOAD_TOKEN: ${RELOAD_TOKEN}
    volumes:
      - models:/app/models-vol:ro  # Read-only for API
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
      DATABASE_URL: postgresql+psycopg://nfl:${POSTGRES_PASSWORD}@postgres:5432/nflpredictor
      MLFLOW_TRACKING_URI: http://mlflow:5000
      MODEL_PATH: /app/models-vol/best_model.json
      EXPERIMENTS_PATH: /app/models-vol/experiments.jsonl
      REFRESH_CRON_HOUR: ${REFRESH_CRON_HOUR:-6}
    volumes:
      - models:/app/models-vol    # Read-write for worker
    depends_on:
      postgres:
        condition: service_healthy

  mlflow:
    build:
      context: .
      dockerfile: mlflow.Dockerfile
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5000
      --backend-store-uri postgresql://nfl:${POSTGRES_PASSWORD}@postgres:5432/mlflow
      --default-artifact-root /mlartifacts
    volumes:
      - mlartifacts:/mlartifacts
    depends_on:
      postgres:
        condition: service_healthy

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./frontend/dist:/srv
      - caddy_data:/data
    depends_on:
      api:
        condition: service_healthy

volumes:
  pgdata:
  mlartifacts:
  models:
  caddy_data:
```

### Caddyfile Pattern
```
{$DOMAIN:localhost} {
    encode gzip

    handle /api/* {
        reverse_proxy api:8000
    }

    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

### MLflow Custom Dockerfile
```dockerfile
FROM ghcr.io/mlflow/mlflow:latest
RUN pip install --no-cache-dir psycopg2-binary
```

### Staleness Check Pattern
```python
def _check_data_staleness(engine, season, expected_week):
    """Verify Monday night's game results are in fetched data.

    Queries schedules table for the most recent completed week.
    If the latest completed week < expected_week, data hasn't updated yet.
    """
    query = """
    SELECT MAX(week) as latest_week
    FROM schedules
    WHERE season = %(season)s
      AND game_type = 'REG'
      AND home_score IS NOT NULL
    """
    result = pd.read_sql(query, engine, params={"season": season})
    latest = result["latest_week"].iloc[0]
    if latest is None or int(latest) < expected_week:
        raise ValueError(
            f"Data stale: latest completed week is {latest}, "
            f"expected at least week {expected_week}"
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| APScheduler 4.x alpha (async-first) | APScheduler 3.11.x (stable) | Ongoing | 4.x is alpha; 3.x is production-ready. Use 3.x for stability |
| nginx + certbot for SSL | Caddy with auto-SSL | Caddy v2 (2020+) | Zero cert management, simpler config, fewer files |
| MLflow file-based tracking | MLflow server with PostgreSQL | MLflow 2.x+ | Multi-process safe, queryable, proper production mode |
| docker-compose (v1 Python) | docker compose (v2 built-in) | Docker Compose v2 (2022) | Built into Docker CLI, no separate install |
| nfl-data-py | nflreadpy (recommended successor) | Sep 2025 | nfl-data-py archived; but project already uses it successfully and it still works |

**Deprecated/outdated:**
- APScheduler 4.0.0a3 exists but is alpha -- do NOT use. Stick with 3.11.x.
- `docker-compose` (hyphenated, Python-based v1) is deprecated. Use `docker compose` (space, Go-based v2). The Compose file format is the same.
- `nfl-data-py` was archived September 2025 but still functions. The project already uses it; no migration needed for v1.

## Open Questions

1. **nfl-data-py Archive Status**
   - What we know: nfl-data-py was archived Sept 2025; nflreadpy is the successor. The project already uses nfl-data-py successfully.
   - What's unclear: Whether the underlying nflverse data endpoints remain stable. The library still works as of March 2026.
   - Recommendation: Keep using nfl-data-py for v1. If it breaks during the 2026 season, migrate to nflreadpy. Not a deployment blocker.

2. **MLflow Image Tag Pinning**
   - What we know: `ghcr.io/mlflow/mlflow:latest` exists. The project pins `mlflow>=3.10.0` in pyproject.toml.
   - What's unclear: Whether the Docker image tag numbering matches PyPI versions exactly.
   - Recommendation: Use `ghcr.io/mlflow/mlflow:latest` in the custom Dockerfile. The tag is rebuilt regularly. Pin to a specific version tag if stability issues emerge.

3. **First-Run Data Volume Bootstrap**
   - What we know: First run ingests 20 seasons (~14M+ PBP rows, 30+ minutes). This runs interactively via `docker compose exec worker python -m pipeline.refresh`.
   - What's unclear: Whether the cache directory (`data/cache/`) should be a named volume or if data downloads happen fresh each time in Docker.
   - Recommendation: Do NOT volume-mount `data/cache/`. Let each container build download fresh. The cache is a development convenience; in Docker, the database is the source of truth. Alternatively, use a bind mount for the cache during initial setup to speed up debugging, then remove it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ features/tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Weekly refresh ingests data + recomputes features | unit | `pytest tests/test_pipeline.py::test_refresh_steps_1_2 -x` | No -- Wave 0 |
| PIPE-01 | APScheduler CronTrigger configuration | unit | `pytest tests/test_pipeline.py::test_worker_schedule -x` | No -- Wave 0 |
| PIPE-02 | Retrain stages candidate model, non-fatal failure | unit | `pytest tests/test_pipeline.py::test_retrain_nonfatal -x` | No -- Wave 0 |
| PIPE-03 | Staged model not live until reload | integration | `pytest tests/api/test_model.py::test_reload_model -x` | Yes (existing) |
| PIPE-04 | Docker Compose starts all services | smoke | `docker compose up -d && docker compose ps` | Manual verification |
| PIPE-04 | Health checks pass for all services | smoke | `docker compose ps --format json` | Manual verification |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q` (quick unit test pass)
- **Per wave merge:** `pytest tests/ features/tests/ -v` (full suite)
- **Phase gate:** Full suite green + manual `docker compose up -d` smoke test before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_pipeline.py` -- covers PIPE-01, PIPE-02 (pipeline step execution, failure modes, staleness check)
- [ ] `pipeline/__init__.py` -- package init
- [ ] `pipeline/refresh.py` -- pipeline orchestration module
- [ ] `pipeline/worker.py` -- APScheduler entrypoint

## Sources

### Primary (HIGH confidence)
- [APScheduler 3.x Documentation](https://apscheduler.readthedocs.io/en/3.x/userguide.html) - BlockingScheduler, CronTrigger, signal handling
- [Docker Compose Documentation](https://docs.docker.com/compose/how-tos/startup-order/) - Health checks, depends_on, service_healthy
- [Caddy Common Patterns](https://caddyserver.com/docs/caddyfile/patterns) - SPA + reverse proxy Caddyfile syntax
- [Docker Hub Caddy](https://hub.docker.com/_/caddy) - Official Caddy image tags, version 2.11.x
- [MLflow Docker Compose](https://github.com/mlflow/mlflow/tree/master/docker-compose) - Official MLflow Docker Compose example with PostgreSQL
- [MLflow GitHub Issue #9513](https://github.com/mlflow/mlflow/issues/9513) - Confirms official image lacks psycopg2 for PostgreSQL

### Secondary (MEDIUM confidence)
- [APScheduler Docker Graceful Shutdown](https://www.tooli.top/posts/apscheduler_docker_stop) - SIGTERM handler pattern verified against APScheduler docs
- [Python Docker Images Best Practices](https://pythonspeed.com/articles/base-image-python-docker-images/) - python:3.11-slim recommendation for data science workloads
- [Docker Multi-Stage Builds for Python](https://collabnix.com/docker-multi-stage-builds-for-python-developers-a-complete-guide/) - Build/runtime stage separation
- [MLflow PostgreSQL Setup](https://medium.com/@mahernaija/deploy-mlflow-3-2-0-with-postgresql-minio-in-docker-2025-edition-58ebb434751d) - psycopg2-binary installation pattern

### Tertiary (LOW confidence)
- MLflow Docker image tag alignment with PyPI versions -- not formally documented, inferred from release patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components are mature, well-documented, and verified against official sources
- Architecture: HIGH - Patterns directly from Docker Compose docs, Caddy docs, APScheduler docs; project already has all application code
- Pitfalls: HIGH - Each pitfall verified against official documentation or confirmed via GitHub issues (e.g., MLflow psycopg2 gap)
- Pipeline logic: HIGH - All four pipeline steps reuse existing, tested code (data/ingest.py, features/build.py, models/train.py, models/predict.py)

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (30 days -- all components are stable releases)
