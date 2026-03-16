# Project Research Summary

**Project:** NFL Game Predictor
**Domain:** Batch ML prediction system with experiment tracking, API serving, and dashboard
**Researched:** 2026-03-15
**Confidence:** MEDIUM

## Executive Summary

The NFL Game Predictor is a batch machine learning pipeline that predicts pre-kickoff game outcomes using historical play-by-play data. Experts in this domain build it as a classic offline pipeline — ingest raw data, engineer leakage-free game-level features, train a gradient boosting classifier, and serve predictions via a REST API consumed by a React dashboard. The architecture is intentionally batch-oriented: there is no real-time inference, no streaming, and predictions update once per week. This constraint dramatically simplifies the system and is the correct choice for this problem.

The recommended approach is to build in strict dependency order — data foundation before feature engineering before model training before API serving before the dashboard. Every phase has a hard dependency on the prior one, so attempting to parallelize or skip ahead will cause rework. The centerpiece of the project is the autoresearch experiment loop, where an AI agent iteratively modifies the training script and evaluates whether changes improve 2023 validation accuracy above the 53% benchmark. This loop requires careful governance to avoid overfitting to the validation season and infinite iteration cycles.

The single highest-risk element of the entire project is data leakage in feature engineering. Using any future game data to compute features for a prior game inflates validation accuracy to 70%+ and makes the model worthless in production. Every rolling computation must strictly exclude the current game using `.shift(1)` or explicit temporal SQL window filters, and this must be enforced with automated tests from the first day of feature engineering. Secondary risks include nfl-data-py schema inconsistencies across seasons, overfitting the autoresearch loop to the 2023 validation season, and the experiment loop degenerating without hard termination conditions.

## Key Findings

### Recommended Stack

The stack is cohesive and well-justified. Python 3.11 is specified in project constraints and is the safe choice — 3.11 offers 10-60% performance gains over 3.10 while maintaining broad ML library compatibility. The ML pipeline centers on XGBoost 2.0+ (project-specified, best-in-class for tabular data), with scikit-learn for preprocessing utilities and MLflow for experiment tracking. FastAPI serves predictions via an async REST API, and React 18 with TypeScript powers the dashboard. PostgreSQL 16 is the single data store — raw play-by-play, engineered features, predictions, and MLflow metadata all live in the same Postgres instance. The entire system runs in Docker Compose.

Notable stack decisions: use `psycopg3` (not psycopg2, which is maintenance-only), SQLAlchemy 2.0 style (DeclarativeBase, not legacy 1.x patterns), Vite (not Create React App, which is unmaintained), and APScheduler (not Celery — the project has exactly one scheduled task and does not need a message broker). Avoid neural networks for this problem; XGBoost consistently outperforms deep learning on tabular NFL data at this scale (~5,400 game-rows).

**Core technologies:**
- Python 3.11: Runtime — project-specified, best ML library compatibility, significant perf gains over 3.10
- XGBoost 2.0+: Primary classifier — project-specified, best-in-class for tabular structured data
- nfl-data-py: Data source — free, no API key, provides play-by-play and schedule data via nflverse
- pandas 2.1+ / pyarrow 14+: Data processing — required by nfl-data-py, Copy-on-Write perf, memory-efficient parquet I/O
- PostgreSQL 16: Data store — project-specified, handles raw PBP (~14M rows), features, predictions, MLflow metadata
- SQLAlchemy 2.0 + Alembic: ORM and migrations — type-safe, reproducible schema management
- MLflow 2.12+: Experiment tracking — project-specified, self-hosted in Docker Compose, zero-config XGBoost autolog
- FastAPI 0.110+: REST API — project-specified, async-native, automatic OpenAPI docs, Pydantic validation
- React 18 + TypeScript + Vite: Dashboard — project-specified, functional components + hooks, strict mode TypeScript
- TanStack Query 5+: Dashboard data fetching — handles caching, polling (5-min refetch), loading states
- Docker Compose 2.24+: Orchestration — project-specified, single file for all services

### Expected Features

**Must have (table stakes):**
- EPA per play (offensive + defensive, rolling 4-8 games) — the gold-standard NFL metric, available in nfl-data-py; highest predictive value
- Point differential rolling average — direct outcome proxy, strong signal
- Turnover differential rolling average — one of the top-5 predictors in published NFL models
- Home/away indicator — consistent ~2.5 point advantage, always available
- Rest days / bye week indicator — measurable performance effect for short-rest games
- Win/loss streak and season win percentage — team momentum and quality proxy
- Third-down conversion rate (off + def, rolling) — execution quality proxy
- Binary win/loss prediction with confidence score — the core product output
- Historical accuracy tracking vs. naive baselines — users cannot trust a model without seeing its track record and how it compares to "always pick the home team"
- This week's picks dashboard view — primary user-facing interface
- Experiment comparison scoreboard — required for the autoresearch loop workflow
- Per-experiment metrics logging (accuracy, log loss, AUC, Brier score) to experiments.jsonl

**Should have (competitive differentiators):**
- Calibrated probabilities (Platt scaling or isotonic regression) — raw XGBoost probabilities are often poorly calibrated; "70% confidence" should mean 70% win rate historically
- SHAP feature importance per prediction — explainability builds trust and helps debug leakage
- Confidence tiers (high/medium/low) — high UX value, low implementation cost
- Weekly recap view with correct/incorrect highlighting — engagement driver after game results
- Model performance over time chart — reveals drift and improvement trajectory
- Success rate (% positive EPA plays) — captures consistency beyond raw averages
- Weighted rolling averages with recency decay — recent games more predictive than Week 1

**Defer to v2+:**
- Player-level features (injury tracking, individual performance) — unreliable data, far higher complexity
- Vegas odds integration — data licensing complexity, conflates market signal with model signal
- Live in-game win probability — entirely different architecture (real-time streaming)
- Multi-model ensembles — premature until single-model behavior is deeply understood
- Team deep-dive pages — high frontend effort, not essential for v1
- Mobile app — responsive web covers this adequately for v1

### Architecture Approach

The system is a batch ML pipeline with an API serving layer — a well-understood architecture pattern. Six components are cleanly separated: (1) data ingestion writes raw data to PostgreSQL only; (2) feature engineering reads raw tables and writes a leakage-safe game_features table; (3) the model training + autoresearch loop reads game_features, modifies only models/train.py, and logs to both experiments.jsonl and MLflow; (4) the prediction API reads game_features and model artifacts, never writes features or trains; (5) the React dashboard is a pure presentation layer that hits the API only; (6) a weekly pipeline orchestrator calls the other components in sequence. The clean component boundaries exist specifically to protect the leakage guarantees — the autoresearch agent modifies only train.py and can never touch the feature engineering code.

**Major components:**
1. Data Ingestion (`data/ingest.py`) — fetches nfl-data-py data, upserts to raw_pbp and raw_schedules; raw data only, no feature computation
2. Feature Engineering (`features/build.py`) — computes game-level rolling features with strict temporal ordering; writes game_features table; home of the leakage tests
3. Model Training + Autoresearch Loop (`models/train.py` + `models/program.md`) — XGBoost training, experiment logging to experiments.jsonl + MLflow, agent-driven iteration
4. Prediction API (`api/main.py`) — FastAPI serving predictions from the deployed model; read-only, model loaded at startup
5. React Dashboard (`frontend/`) — four views: this week's picks, season record, experiment scoreboard, historical predictions
6. Weekly Pipeline (`pipeline/refresh.py`) — cron-triggered orchestrator; steps 1-4 automated, model deployment requires human approval

### Critical Pitfalls

1. **Future data leakage in rolling features** — The project killer. Apply `.shift(1)` to all rolling/expanding computations. Write a leakage test that verifies no feature value for game G uses data from game G or later. Run this test in CI from day one. Detection: suspiciously high accuracy (>65% on NFL games is a red flag).

2. **Overfitting to the 2023 validation season** — The experiment loop with 50+ iterations effectively overfits to 272 games of noise. Cap at 20-30 experiments. Track multi-season accuracy (2021 and 2022) alongside 2023 to detect overfitting. Monitor calibration metrics (Brier score, log loss) not just accuracy.

3. **nfl-data-py data quality** — Schema changes across seasons cause silent NaN propagation. Team abbreviation changes (OAK -> LV, SD -> LAC, STL -> LA, WSH -> WAS) corrupt rolling calculations. Playoff games contaminate regular-season features. Build a data validation step before feature engineering: check game counts per season, verify column presence across the full date range, normalize team abbreviations universally, filter to regular season only.

4. **Experiment loop degeneration** — Without termination conditions, the loop runs indefinitely or enters regression spirals. Define stop conditions in program.md before starting: "stop after 20 experiments OR 3 consecutive <0.3% improvements OR if accuracy exceeds 58%." Git commit before each experiment so revert is `git checkout -- models/train.py`, not manual undo.

5. **Ignoring trivial baselines** — "Always pick the home team" achieves ~57% on NFL games. If the ML model cannot beat that, it adds no value. Log trivial baselines (always-home, better-record) from experiment #1 and always display them alongside model accuracy.

## Implications for Roadmap

Based on the combined research, the system must be built in strict dependency order. There is no flexibility in phase sequencing — each phase has hard dependencies on the prior one.

### Phase 1: Data Foundation
**Rationale:** Everything depends on having NFL data in PostgreSQL. No feature engineering, model training, or serving is possible until this works correctly. This is also where the most insidious data quality issues (team abbreviation inconsistencies, schema changes, game count anomalies) must be caught before they corrupt downstream work.
**Delivers:** Populated raw_pbp and raw_schedules tables for 2005-2024 (~14M play-by-play rows, ~5,700 schedule rows). Data validation checks passing.
**Addresses:** Table stakes features — data ingestion pipeline, schedule access for rest/bye features.
**Avoids:** nfl-data-py schema and quality pitfalls (Pitfall 3). Team normalization mapping built here prevents corruption of all downstream rolling stats.
**Stack:** Python 3.11, nfl-data-py, pandas, pyarrow, PostgreSQL 16, SQLAlchemy 2.0, Alembic, tenacity (retry logic for flaky upstream data).

### Phase 2: Feature Engineering Pipeline
**Rationale:** The hardest phase to get right and the easiest to get catastrophically wrong. Feature engineering must be built and validated before any model training — discovering leakage after 30 experiments means rewriting this entire phase and invalidating all experiment results.
**Delivers:** Populated game_features table (one row per team-game) with leakage tests passing in CI. Includes Tier 1 features: EPA per play, point differential, turnover differential, home/away, rest days, win streak, season win percentage, third-down conversion rate.
**Addresses:** Must-have ML features (EPA, point differential, turnovers, home/away, rest days). Leakage prevention mechanisms.
**Avoids:** Future data leakage (Pitfall 1 — the #1 project killer), home/away asymmetry (Pitfall 7), early-season instability (Pitfall 8), target variable construction errors (Pitfall 10).
**Stack:** PostgreSQL SQL window functions, pandas, temporal config in config.py (single source of truth for train/val/test boundaries).
**Research flag:** This phase has well-documented patterns for the SQL temporal windowing and pandas shift operations, but the leakage test design is specific to this project's data model. May benefit from brief research into common NFL feature engineering approaches before implementation.

### Phase 3: Model Training + Autoresearch Infrastructure
**Rationale:** Requires game_features to exist. This phase establishes the experiment framework before running any experiments — governance rules, logging schema, MLflow setup, and the keep/revert logic must be in place before the loop starts. The 53% benchmark is the primary acceptance criterion.
**Delivers:** Working autoresearch loop achieving >53% validation accuracy on 2023 season. experiments.jsonl with ≥5 entries. MLflow tracking UI showing run history. Trivial baseline comparisons logged from experiment #1. Temporal split hardcoded (train 2005-2022, val 2023, test 2024 — never touched).
**Addresses:** Experiment tracking must-haves (per-experiment metrics, feature list, keep/revert log, validation accuracy as primary metric). Autoresearch loop (differentiator).
**Avoids:** Overfitting to 2023 validation (Pitfall 4 — cap at 20-30 experiments, track multi-season accuracy), experiment loop degeneration (Pitfall 5 — termination conditions in program.md before loop starts), MLflow drift (Pitfall 9 — single log_experiment() function writing to both sinks), ignoring baselines (Pitfall 11).
**Stack:** XGBoost 2.0+, scikit-learn (preprocessing + calibration), MLflow with xgboost.autolog(), SHAP.
**Research flag:** The autoresearch loop pattern is novel and not well-documented in standard references. The loop governance structure (program.md schema, termination conditions, deduplication logic) should be designed carefully before implementation.

### Phase 4: Prediction API
**Rationale:** Requires a trained model artifact. The API is the integration point between the ML pipeline and the dashboard. Model versioning and the reload endpoint must be designed before building the dashboard against it.
**Delivers:** FastAPI service at localhost:8000 with five endpoints: /api/predictions/current, /api/predictions/history, /api/model/info, /api/experiments, /api/health. Model loaded at startup in lifespan context. Reload endpoint for post-training model swaps.
**Addresses:** Dashboard must-haves (this week's picks, historical predictions, experiment scoreboard data).
**Avoids:** Cold start and stale model issues (Pitfall 6 — lifespan loading, /reload endpoint, model+feature version metadata).
**Stack:** FastAPI 0.110+, Uvicorn, Pydantic v2, psycopg3.
**Research flag:** Standard FastAPI patterns are well-documented. Skip research-phase for this component.

### Phase 5: React Dashboard
**Rationale:** Pure presentation layer with no business logic. Depends entirely on the API being stable. Building this before the API is finalized causes rework when endpoints change.
**Delivers:** Four dashboard views: This Week's Picks (game cards with predicted winner and confidence), Season Record (accuracy vs. baselines), Experiment Scoreboard (all experiments sorted by val_accuracy, current model highlighted), Historical Predictions (paginated with correct/incorrect badges).
**Addresses:** All dashboard must-haves and several differentiators (confidence tiers, calibration plot, model performance over time chart, weekly recap highlighting).
**Avoids:** Confusing accuracy metric presentation (Pitfall 14 — explicit labels: "2023 validation accuracy (272 games): 56.3%").
**Stack:** React 18, TypeScript strict mode, Vite, TanStack Query (5-min polling), Recharts, Tailwind CSS.
**Research flag:** Standard React + TypeScript dashboard patterns are well-documented. Skip research-phase.

### Phase 6: Weekly Pipeline + Docker Deployment
**Rationale:** All components must exist before orchestrating them. Docker Compose wraps the full system. The weekly refresh pipeline closes the loop from new data to updated predictions.
**Delivers:** docker compose up starts all services. Weekly pipeline runs automatically (cron Tuesday post-games) for steps 1-3 (ingest, features, predict). Model deployment requires human approval. Named volumes persist data across rebuilds.
**Addresses:** Operational continuity, seasonal data refresh, weekly prediction updates.
**Avoids:** Docker volume loss (Pitfall 12 — named volumes from day one), weekly refresh race conditions (Pitfall 13 — staging tables or maintenance window), auto-deployment of bad models (Architecture anti-pattern 4 — semi-automated with human approval gate).
**Stack:** Docker 24+, Docker Compose 2.24+, Nginx 1.25, APScheduler.
**Research flag:** Docker Compose with ML workloads has a few non-obvious patterns (health checks for service startup ordering, volume configuration for MLflow artifact store). Recommend brief review before implementation.

### Phase Ordering Rationale

- **Data before features:** You cannot compute rolling EPA without the play-by-play rows to roll over.
- **Features before training:** Discovering leakage after the experiment loop has run 20 iterations invalidates all results and requires restarting. The leakage tests must pass before any experiment begins.
- **Training before API:** The API loads a model artifact. Without a trained model, there is nothing to serve.
- **API before dashboard:** The dashboard is a consumer of stable API contracts. Building the dashboard against an unfinished API creates constant churn.
- **All components before deployment:** Docker Compose orchestrates existing services. Dockerizing components as they are built is fine, but the weekly pipeline and deployment validation is last.
- **Governance before the experiment loop:** Termination conditions, deduplication logic, and the experiments.jsonl schema must be defined before the first experiment runs. These cannot be retrofitted after 30 entries exist.

### Research Flags

Phases needing deeper research during planning:
- **Phase 2 (Feature Engineering):** The no-leakage SQL window function patterns for NFL data and the leakage test design are specific to this domain. Review nfl-data-py column documentation for exact field names before writing queries.
- **Phase 3 (Autoresearch Loop):** The program.md schema, loop governance rules, and agent handoff mechanics are novel. Design carefully before implementation — a poorly structured loop burns hours on degenerate experiments.
- **Phase 6 (Docker Deployment):** MLflow artifact store configuration and PostgreSQL health checks in Docker Compose have non-obvious setup requirements.

Phases with standard patterns (skip research-phase):
- **Phase 4 (FastAPI API):** Standard FastAPI patterns, lifespan model loading, and Pydantic v2 are extremely well-documented.
- **Phase 5 (React Dashboard):** React + TypeScript + TanStack Query + Tailwind is a well-documented, widely-used combination.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Core technology choices are well-established and project-specified. Version numbers (nfl-data-py 0.3.1+, specific psycopg3 version) based on training data; verify on PyPI before pinning. Web search was unavailable during research. |
| Features | MEDIUM | Feature prioritization and EPA as gold-standard metric are well-established in NFL analytics literature. Specific column availability in nfl-data-py across all seasons (2005-2024) needs verification by loading one season and inspecting the schema before committing to the full feature set. |
| Architecture | HIGH | Batch ML pipeline with temporal separation is a well-understood pattern. The autoresearch loop design is novel but the core pattern (read-modify-run-evaluate-keep/revert) is sound. Component boundaries and data flows are clearly defined. |
| Pitfalls | MEDIUM-HIGH | Data leakage patterns, NFL team abbreviation history, and XGBoost serving pitfalls are well-established. nfl-data-py-specific schema quirks and exact column behavior across seasons would benefit from live verification. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **nfl-data-py column schema across seasons:** Before writing feature engineering code, run `nfl.import_pbp_data([2024])` and inspect column names and types. Verify that EPA, WPA, and other advanced metrics exist in 2005 data or determine the earliest season they are available. This affects the training window start date.
- **Version pinning:** Verify exact latest stable versions of nfl-data-py, psycopg3, and MLflow on PyPI before writing pyproject.toml. Training-data version numbers may be stale.
- **53% baseline context:** Implement the always-home-team baseline in Phase 3 before any other experiment. If this baseline achieves 57%, the model only adds value if it clearly beats 57%, not 53%. This changes the interpretation of the benchmark.
- **2024 holdout access control:** Establish a hard policy before starting the experiment loop — no human or agent looks at 2024 holdout performance until the final evaluation. Log it to a separate file that is not surfaced in the dashboard during development.
- **Autoresearch loop agent interface:** The loop assumes an AI agent will read program.md and modify train.py. The exact interface (how the agent is invoked, how it reads experiment results, how revert is triggered) needs to be specified before Phase 3 implementation begins.

## Sources

### Primary (HIGH confidence)
- Project constraints from `.planning/PROJECT.md` — technology choices (Python 3.11, PostgreSQL, XGBoost, FastAPI, React, MLflow, Docker Compose)
- XGBoost documentation — classification patterns, predict_proba, autolog integration
- FastAPI documentation — lifespan pattern, Pydantic v2 integration, async/sync model serving
- MLflow documentation — experiment tracking, XGBoost autolog, artifact store configuration

### Secondary (MEDIUM confidence)
- nfl-data-py / nflverse ecosystem training knowledge — import_pbp_data() API, column schema, data update cadence
- NFL analytics community (nflfastR) — EPA as gold-standard metric, feature prioritization, typical model accuracy ranges
- scikit-learn documentation — calibration (Platt scaling, isotonic regression), preprocessing pipelines
- Docker Compose documentation — health checks, named volumes, service dependency ordering

### Tertiary (LOW confidence — verify before implementing)
- Specific nfl-data-py column names and availability across seasons 2005-2024 — schema changes between eras need live verification
- Exact package version numbers for nfl-data-py, psycopg3, APScheduler — based on training data cutoff ~May 2025, verify on PyPI
- nfl-data-py team abbreviation history — normalization mapping (OAK->LV, SD->LAC, STL->LA, WSH->WAS) should be verified against actual data before use

---
*Research completed: 2026-03-15*
*Ready for roadmap: yes*
