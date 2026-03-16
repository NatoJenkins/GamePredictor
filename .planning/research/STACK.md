# Technology Stack

**Project:** NFL Game Predictor
**Researched:** 2026-03-15
**Verification note:** WebSearch and WebFetch were unavailable during this research session. All version recommendations are based on training data (cutoff ~May 2025). Pin versions in `pyproject.toml` and verify with `pip install` before committing. Versions listed are the latest known-stable releases; newer versions may exist.

## Recommended Stack

### Runtime & Language

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.11 | Runtime | Specified in constraints. 3.11 has best balance of performance (10-60% faster than 3.10), library compatibility, and stability. Avoid 3.12+ for now -- some ML libraries lag on newest Python releases. | HIGH |
| Node.js | 20 LTS | Frontend build | LTS release for React tooling. Use only for frontend dev server and build. | HIGH |

### Data Ingestion

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| nfl-data-py | >=0.3.1 | NFL data source | The project-specified data source. Wraps nflfastR/nflverse data. Provides `import_pbp_data()` for play-by-play and `import_schedules()` for game results. Free, no API key needed. | MEDIUM |
| pandas | >=2.1 | Data manipulation | Required by nfl-data-py. Use 2.1+ for Copy-on-Write (performance), PyArrow backend support. nfl-data-py returns pandas DataFrames. | HIGH |
| pyarrow | >=14.0 | Parquet I/O | nfl-data-py downloads parquet files under the hood. Also enables pandas Arrow-backed dtypes for lower memory usage on large PBP datasets (~700K rows/season). | HIGH |

### Database

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PostgreSQL | 16 | Primary datastore | Project-specified. Handles structured game data, feature tables, prediction history. Use JSONB columns for flexible metadata (experiment configs). | HIGH |
| SQLAlchemy | >=2.0 | ORM / query builder | 2.0 style (not legacy 1.x patterns). Use mapped_column, DeclarativeBase. Provides type safety and migration support. Do NOT use raw SQL strings scattered through code. | HIGH |
| Alembic | >=1.13 | Schema migrations | Only viable migration tool for SQLAlchemy. Auto-generates migration scripts from model changes. Essential for reproducible database setup across dev/prod. | HIGH |
| psycopg | >=3.1 | PostgreSQL driver | psycopg3 (not psycopg2). Native async support, better performance, active development. Use `psycopg[binary]` for easy install, `psycopg[c]` for production performance. | MEDIUM |

### Machine Learning

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| XGBoost | >=2.0 | Primary classifier | Project-specified. Best-in-class for tabular data. Version 2.0+ has improved GPU support and better default hyperparameters. Use `XGBClassifier` with `objective='binary:logistic'` for win/loss. | HIGH |
| scikit-learn | >=1.4 | ML utilities | Feature preprocessing (StandardScaler, OneHotEncoder), train/test split utilities, classification metrics (accuracy_score, log_loss, calibration_curve). Do NOT use it as the primary model -- XGBoost handles that. | HIGH |
| MLflow | >=2.12 | Experiment tracking | Project-specified. Use `mlflow.xgboost.autolog()` for zero-config XGBoost logging. Tracks params, metrics, artifacts, and model versions. The tracking UI runs as a separate service in Docker Compose. | MEDIUM |
| SHAP | >=0.44 | Model explainability | XGBoost-native TreeExplainer is fast. Generates feature importance plots for the dashboard. Helps debug whether features are leaking future data. | MEDIUM |

### API Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | >=0.110 | REST API | Project-specified. Async-native, automatic OpenAPI docs, Pydantic validation. Use for serving predictions and exposing model metadata. | HIGH |
| Uvicorn | >=0.27 | ASGI server | Standard production server for FastAPI. Use `--workers 2` in Docker (prediction serving is CPU-bound, not I/O-bound, so modest worker count). | HIGH |
| Pydantic | >=2.6 | Data validation | Comes with FastAPI. Use Pydantic v2 (not v1). Define request/response schemas as Pydantic models. Use `model_validate` not `parse_obj`. | HIGH |
| httpx | >=0.27 | HTTP client | For async HTTP calls if needed (e.g., fetching schedule data). Preferred over `requests` in async FastAPI context. | HIGH |

### Frontend

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | 18 | Dashboard UI | Project-specified. Use functional components + hooks exclusively. No class components. | HIGH |
| Vite | >=5.0 | Build tool | Faster than Create React App (which is effectively dead). HMR, ESM-native, simple config. | HIGH |
| TypeScript | >=5.3 | Type safety | Catches bugs in prediction display logic. Use strict mode. Non-negotiable for any React project. | HIGH |
| Recharts | >=2.10 | Charts | Lightweight, React-native charting. Use for confidence score distributions, accuracy over time, calibration plots. Simpler than D3 for dashboard use cases. | MEDIUM |
| TanStack Query | >=5.0 | Data fetching | Handles caching, refetching, loading states for API calls. Replaces manual useEffect+fetch patterns. Use for polling prediction updates. | HIGH |
| Tailwind CSS | >=3.4 | Styling | Utility-first, fast iteration for dashboard layouts. No custom CSS files to manage. Works well with component libraries. | HIGH |

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker | >=24 | Containerization | Project-specified. One Dockerfile per service (api, frontend, mlflow, postgres, worker). | HIGH |
| Docker Compose | >=2.24 | Orchestration | Project-specified. Single `docker-compose.yml` for all services. Use profiles for dev vs prod. | HIGH |
| Nginx | >=1.25 | Reverse proxy | Serves React static build, proxies `/api` to FastAPI, proxies `/mlflow` to MLflow UI. Single entry point in production. | HIGH |

### Dev Tooling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| uv | >=0.4 | Python package manager | 10-100x faster than pip. Handles virtualenvs, lockfiles, Python version management. Use `uv pip compile` for deterministic lockfile. | MEDIUM |
| Ruff | >=0.3 | Linter + formatter | Replaces flake8, isort, black in one tool. 10-100x faster. Single config in pyproject.toml. | HIGH |
| pytest | >=8.0 | Testing | Standard Python test runner. Use `pytest-asyncio` for async FastAPI tests, `pytest-cov` for coverage. | HIGH |
| pre-commit | >=3.6 | Git hooks | Runs ruff, type checks before commit. Prevents broken code from entering repo. | HIGH |

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | >=1.3 | Model serialization | Fallback model save/load if not using MLflow's model registry. Also useful for caching expensive feature computations. |
| numpy | >=1.26 | Numerical ops | Underlying array operations. Pinned by pandas/scikit-learn -- don't install separately, let it resolve. |
| python-dotenv | >=1.0 | Env config | Load `.env` files for local dev. Docker Compose handles env in prod. |
| APScheduler | >=3.10 | Task scheduling | Weekly data refresh + retrain trigger. Lighter than Celery for this use case (single cron-like job, not a task queue). |
| tenacity | >=8.2 | Retry logic | Wrap nfl-data-py calls -- the upstream nflverse data can be flaky. Exponential backoff on download failures. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Python package mgr | uv | pip + pip-tools | uv is dramatically faster and handles lockfiles natively. pip-tools works but is slow. |
| Python package mgr | uv | Poetry | Poetry has slow resolution, opinionated project structure, and PEP 621 support came late. uv is simpler. |
| PostgreSQL driver | psycopg3 | psycopg2-binary | psycopg2 is maintenance-only. psycopg3 has native async, better typing, active development. |
| Data fetching (React) | TanStack Query | SWR | TanStack Query has better devtools, more features for mutation/invalidation. SWR is simpler but this project needs cache invalidation when new predictions arrive. |
| Charts | Recharts | Chart.js / react-chartjs-2 | Recharts is more React-idiomatic (JSX components vs imperative API). Sufficient for dashboard charts. |
| Charts | Recharts | D3 | D3 is overkill for standard bar/line/scatter charts. Only reach for D3 if building novel visualizations. |
| Task scheduling | APScheduler | Celery + Redis | Celery requires a message broker (Redis/RabbitMQ), adds 2 services to Docker Compose. This project has exactly one scheduled task (weekly refresh). APScheduler runs in-process. |
| Build tool | Vite | Create React App | CRA is unmaintained since 2023. React team no longer recommends it. |
| Build tool | Vite | Next.js | Next.js is a full framework with SSR/routing. This is a single-page dashboard -- Vite + React Router is lighter and simpler. |
| ML model | XGBoost | LightGBM | Both are excellent for tabular data. XGBoost is project-specified and has marginally better MLflow integration. LightGBM would also work. |
| ML model | XGBoost | Neural networks | Neural nets underperform gradient boosting on structured/tabular data with <100K samples. NFL game data is ~5K games/season. Do not use deep learning here. |
| Experiment tracking | MLflow | Weights & Biases | W&B requires an account and is cloud-dependent. MLflow is self-hosted, free, and runs in Docker Compose alongside everything else. |
| ORM | SQLAlchemy 2.0 | Django ORM | Django ORM requires Django. We are using FastAPI. SQLAlchemy 2.0 is the standard for non-Django Python. |
| API framework | FastAPI | Flask | FastAPI has async support, automatic OpenAPI docs, Pydantic integration, and better performance. Flask would require marshmallow + flask-restx for equivalent functionality. |

## Critical Integration Notes

### nfl-data-py Compatibility

- nfl-data-py depends on pandas and pyarrow internally. It downloads parquet files from GitHub (nflverse/nflverse-data).
- **Known issue:** nfl-data-py can be slow to update for the current season. The underlying nflverse data updates weekly on Tuesdays/Wednesdays during the season.
- **Fallback plan:** If nfl-data-py breaks or lags, you can fetch the parquet files directly from `https://github.com/nflverse/nflverse-data/releases` using httpx. The data format is the same.
- **Memory concern:** A single season of play-by-play data is ~700K rows x 350+ columns. Loading 20 seasons at once will consume 10-20GB RAM. Solution: load and process one season at a time, write features to PostgreSQL, then discard raw PBP data.

### MLflow + XGBoost Integration

- `mlflow.xgboost.autolog()` captures: training metrics per iteration, feature importance, model artifacts, hyperparameters.
- Store the MLflow tracking URI as an environment variable (`MLFLOW_TRACKING_URI=http://mlflow:5000` in Docker Compose).
- MLflow backend store: use PostgreSQL (same instance, different database) for metadata. Artifact store: local filesystem volume (`/mlflow/artifacts`).
- The dual-logging pattern (experiments.jsonl + MLflow) means: write to jsonl first (portable, git-trackable), then log to MLflow (visual UI). jsonl is the source of truth for the autoresearch loop.

### FastAPI Async Patterns for ML Serving

- **Do NOT load the model on every request.** Load once at startup using a lifespan context manager (`@asynccontextmanager async def lifespan(app)`). Store model in `app.state.model`.
- **Prediction is CPU-bound.** Use `run_in_executor` to avoid blocking the event loop: `await asyncio.get_event_loop().run_in_executor(None, model.predict, features)`.
- **Do NOT use async def for prediction endpoints if the prediction itself is synchronous.** Use `def predict(...)` (sync) and let FastAPI run it in a threadpool automatically, OR use explicit executor as above.
- Batch predictions for the week's games in a single call (16 games max) -- no need for streaming or websockets.

### React Dashboard Architecture

- **Two main views:** (1) This Week's Picks -- game cards with predicted winner, confidence %, team logos; (2) Model Scoreboard -- experiment comparison table, accuracy trend chart, calibration plot.
- **Polling, not WebSockets.** Predictions update once per week. Use TanStack Query with `refetchInterval: 300000` (5 min) during active weeks.
- **No state management library needed.** TanStack Query handles server state. Local UI state (filters, selected experiment) is fine with useState/useReducer. Do NOT add Redux or Zustand.

## Python Version Constraints

Use Python 3.11 specifically. Rationale:
- 3.11 has significant performance improvements (10-60% over 3.10)
- All specified libraries have stable 3.11 support
- 3.12+ changed some internals that caused issues with older versions of numpy/scikit-learn -- by March 2026 this is likely resolved, but 3.11 is the safe bet without verification
- The project constraints explicitly specify Python 3.11

## Installation

```bash
# Initialize project with uv
uv init --python 3.11
uv venv

# Core data pipeline
uv pip install nfl-data-py pandas pyarrow sqlalchemy "psycopg[binary]" alembic

# Machine learning
uv pip install xgboost scikit-learn mlflow shap

# API
uv pip install fastapi uvicorn pydantic httpx python-dotenv

# Scheduling
uv pip install apscheduler tenacity

# Dev dependencies
uv pip install -D pytest pytest-asyncio pytest-cov ruff pre-commit

# Frontend (separate directory)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install recharts @tanstack/react-query axios
npm install -D tailwindcss postcss autoprefixer @types/react @types/react-dom
```

## Docker Compose Services

```yaml
# docker-compose.yml service structure (not full config, just architecture)
services:
  postgres:     # PostgreSQL 16, persistent volume
  api:          # FastAPI + Uvicorn, depends on postgres
  mlflow:       # MLflow tracking server, depends on postgres
  frontend:     # Nginx serving React build, proxies /api and /mlflow
  worker:       # APScheduler for weekly refresh/retrain (optional: can run in api service)
```

## File Structure Convention

```
GamePredictor/
  pyproject.toml          # Python deps, ruff config, project metadata
  docker-compose.yml
  .env.example
  data/
    ingest.py             # nfl-data-py -> PostgreSQL
  features/
    engineer.py           # PBP -> game-level features (rolling stats)
  models/
    train.py              # XGBoost training (modified by autoresearch loop)
    predict.py            # Load model, generate predictions
    program.md            # Autoresearch experiment plan
  api/
    main.py               # FastAPI app
    routes/
    schemas/
  frontend/               # Vite + React + TypeScript
  mlflow/                 # MLflow config
  experiments.jsonl       # Flat-file experiment log
  alembic/                # Database migrations
```

## Sources

- Training data knowledge (cutoff ~May 2025) -- MEDIUM confidence on specific version numbers
- Project constraints from `.planning/PROJECT.md` -- HIGH confidence on technology choices
- **Verification needed:** Run `pip index versions <package>` or check PyPI for each package to confirm latest stable versions before pinning in pyproject.toml
