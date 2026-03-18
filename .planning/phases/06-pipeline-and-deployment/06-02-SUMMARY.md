---
phase: 06-pipeline-and-deployment
plan: 02
subsystem: infra
tags: [docker, docker-compose, caddy, mlflow, postgres, dockerfile, reverse-proxy]

# Dependency graph
requires:
  - phase: 06-pipeline-and-deployment/plan-01
    provides: pipeline/worker.py entrypoint and pipeline/refresh.py orchestration
  - phase: 04-prediction-api
    provides: FastAPI app (api/main.py) with health check endpoint
  - phase: 05-dashboard
    provides: React frontend (frontend/dist) served by Caddy
provides:
  - Dockerfile (multi-stage Python image for api and worker services)
  - mlflow.Dockerfile (MLflow + psycopg2-binary for PostgreSQL backend)
  - Caddyfile (SPA static file server + API reverse proxy)
  - docker-compose.yml (5-service stack with health checks and dependency ordering)
  - .env.example (environment variable template)
  - sql/00-create-mlflow-db.sh (MLflow database creation on first postgres boot)
affects: []

# Tech tracking
tech-stack:
  added: [Docker, Caddy 2, docker-compose]
  patterns: [multi-stage Docker build, named volumes for persistence, health-check dependency ordering, read-only volume mounts for serving]

key-files:
  created: [Dockerfile, mlflow.Dockerfile, Caddyfile, .env.example, sql/00-create-mlflow-db.sh]
  modified: [docker-compose.yml, frontend/src/lib/api.ts, .gitignore]

key-decisions:
  - "Multi-stage Dockerfile copies source in both builder and runtime stages to avoid pip install failure"
  - "MLflow pinned to 2.21.3 instead of :latest to prevent surprise breakage"
  - "Postgres exposes 5432:5432 for local dev convenience -- should be removed for VPS hardening"
  - "Frontend API_BASE defaults to empty string for relative URLs behind Caddy proxy"
  - "Models volume mounted read-only in api, read-write in worker"
  - "MLflow internal-only (no host port mapping) -- access via SSH tunnel"

patterns-established:
  - "Services depend on postgres health check via service_healthy condition"
  - "Caddy handles TLS termination and SPA routing with try_files fallback"
  - "Environment variables centralized in .env with dev-safe defaults in docker-compose.yml"
  - "SQL init scripts run alphabetically in docker-entrypoint-initdb.d"

requirements-completed: [PIPE-04]

# Metrics
duration: 12min
completed: 2026-03-18
---

# Phase 6 Plan 2: Docker Infrastructure Summary

**Five-service Docker Compose stack (postgres, api, mlflow, worker, caddy) with multi-stage Dockerfile, health-check dependency ordering, and Caddy reverse proxy for SPA + API**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-18T04:26:00Z
- **Completed:** 2026-03-18T04:38:15Z
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 8

## Accomplishments
- Created multi-stage Dockerfile for Python api and worker services with slim runtime image
- Built 5-service docker-compose.yml with health checks, named volumes, and correct dependency ordering
- Caddy serves React SPA with fallback routing and proxies /api/* to FastAPI container
- MLflow gets custom image with psycopg2-binary for PostgreSQL backend store
- Frontend switched to relative API URLs for production deployment behind Caddy
- MLflow database auto-created on first postgres boot via init script

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Dockerfile, mlflow.Dockerfile, Caddyfile, and .env.example** - `4240a8e` (feat)
2. **Task 2: Expand docker-compose.yml to 5 services, create MLflow DB script, fix frontend API URL** - `8a06f87` (feat)
3. **Fix: Dockerfile build bug and pin MLflow version** - `c362756` (fix)
4. **Task 3: Verify Docker Compose stack configuration** - human-approved (no commit, checkpoint verification)

## Files Created/Modified
- `Dockerfile` - Multi-stage Python image (builder + runtime) for api and worker services
- `mlflow.Dockerfile` - MLflow 2.21.3 image with psycopg2-binary for PostgreSQL
- `Caddyfile` - Edge proxy: SPA static files at root, /api/* reverse proxy to api:8000
- `docker-compose.yml` - 5 services (postgres, api, worker, mlflow, caddy) with health checks and volumes
- `.env.example` - Template with POSTGRES_PASSWORD, RELOAD_TOKEN, DOMAIN, REFRESH_CRON_HOUR
- `sql/00-create-mlflow-db.sh` - Creates mlflow database during postgres initialization
- `frontend/src/lib/api.ts` - API_BASE defaults to empty string (relative URLs for production)
- `.gitignore` - Added mlruns/ entry

## Decisions Made
- Multi-stage Dockerfile copies source in both builder and runtime stages (required for pip install of local package)
- MLflow pinned to version 2.21.3 rather than :latest to prevent surprise breakage
- Postgres exposes 5432:5432 for local dev; should be removed or profiled for VPS deployment
- Frontend API_BASE changed from "http://localhost:8000" to "" (empty string) for Caddy proxy compatibility
- Models volume mounted :ro in api (read-only serving) and read-write in worker (staging candidates)
- MLflow service has no host port mapping (internal-only); accessible via SSH tunnel when needed
- Added default CMD to Dockerfile for standalone image use (overridden by docker-compose command)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Dockerfile builder stage lacked source code for pip install**
- **Found during:** Task 3 verification (checkpoint review)
- **Issue:** The Dockerfile builder stage only copied pyproject.toml but not the source code. Since pyproject.toml references the local package, pip install failed without the source.
- **Fix:** Applied Option C -- copy source in builder stage too. Also added a default CMD directive for standalone image use (overridden per-service in docker-compose.yml).
- **Files modified:** Dockerfile
- **Verification:** docker compose config validates; Dockerfile structure correct
- **Committed in:** c362756

**2. [Rule 2 - Missing Critical] MLflow image pinned to specific version**
- **Found during:** Task 3 verification (checkpoint review)
- **Issue:** mlflow.Dockerfile used :latest tag which could cause surprise breakage on deployments.
- **Fix:** Pinned MLflow to version 2.21.3 for reproducible builds.
- **Files modified:** mlflow.Dockerfile
- **Verification:** Image tag explicit in Dockerfile
- **Committed in:** c362756

**3. [Noted for future] Postgres port exposure for VPS hardening**
- **Found during:** Task 3 verification (checkpoint review)
- **Issue:** Postgres service exposes ports 5432:5432 which is fine for local dev but should be removed or profiled for VPS deployment.
- **Action:** Flagged for VPS hardening step. No code change needed for local dev configuration.
- **Deferred to:** VPS deployment setup

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical), 1 noted for future
**Impact on plan:** Both auto-fixes necessary for correctness and operational safety. No scope creep. Postgres port exposure is a deployment concern, not a local dev issue.

## Issues Encountered
- Dockerfile builder stage needed source code alongside pyproject.toml for pip install to resolve local package -- discovered during build verification
- MLflow :latest tag identified as deployment risk during review

## User Setup Required

None in this plan -- VPS deployment setup (DNS, .env creation, docker compose up) is a separate operational step documented in the plan's frontmatter user_setup section.

## Next Phase Readiness
- Full Docker Compose stack is configured and validated
- Stack can be started with `docker compose up -d` after creating .env from .env.example
- Frontend must be pre-built on host (`cd frontend && npm run build`) before caddy can serve it
- VPS deployment requires: DNS A record, strong POSTGRES_PASSWORD, RELOAD_TOKEN, DOMAIN in .env
- Postgres port exposure (5432:5432) should be reviewed before VPS deployment

## Self-Check: PASSED

All 8 created/modified files verified on disk. All 3 task commits (4240a8e, 8a06f87, c362756) verified in git log.

---
*Phase: 06-pipeline-and-deployment*
*Completed: 2026-03-18*
