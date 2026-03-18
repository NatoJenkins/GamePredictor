# Roadmap: NFL Game Predictor

## Overview

This roadmap delivers an NFL game prediction system in six phases following a strict dependency chain. Each phase produces a verifiable capability that the next phase builds on: raw data in PostgreSQL, leakage-safe features, a trained model that beats trivial baselines, an API to serve predictions, a dashboard to display them, and a weekly pipeline with Docker deployment to keep everything running.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Foundation** - Ingest and validate 20 seasons of NFL data into PostgreSQL with normalized team abbreviations (completed 2026-03-16)
- [x] **Phase 2: Feature Engineering** - Compute leakage-safe game-level features with automated temporal validation (completed 2026-03-16)
- [x] **Phase 3: Model Training and Autoresearch** - Train XGBoost classifier via experiment loop, beating trivial baselines on 2023 validation (completed 2026-03-17)
- [x] **Phase 4: Prediction API** - Serve predictions and model metadata via FastAPI endpoints (completed 2026-03-17)
- [x] **Phase 5: Dashboard** - Display weekly picks, season accuracy, experiment scoreboard, and prediction history (completed 2026-03-17)
- [x] **Phase 6: Pipeline and Deployment** - Automate weekly refresh and deploy full stack via Docker Compose (completed 2026-03-18)

## Phase Details

### Phase 1: Data Foundation
**Goal**: NFL play-by-play and schedule data for 2005-2024 is reliably stored in PostgreSQL with clean, normalized team abbreviations and validated completeness
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. Running the ingestion script populates PostgreSQL with play-by-play data for all 20 seasons (2005-2024) and the row counts match expected totals
  2. Schedule/metadata table contains every regular season game with dates, home/away teams, final scores, and week numbers for all 20 seasons
  3. All team abbreviations in both tables use the current canonical form (e.g., LV not OAK, LAC not SD) via a single auditable mapping constant
  4. Ingestion surfaces clear errors when row counts, season completeness, or column schema deviate from expectations -- it does not silently proceed with bad data
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md — Project setup, Docker PostgreSQL, DB schema, constants, and test scaffolds
- [x] 01-02-PLAN.md — Ingestion pipeline with caching, upsert, validation, and integration tests

### Phase 2: Feature Engineering
**Goal**: A game_features table exists with one row per game (home perspective) containing rolling offensive, defensive, and situational features computed with zero data leakage
**Depends on**: Phase 1
**Requirements**: FEAT-01, FEAT-02, FEAT-03, FEAT-04, FEAT-05
**Success Criteria** (what must be TRUE):
  1. Game features table contains rolling EPA/play (offensive and defensive), point differential, turnover differential, and win rate -- all computed using only games prior to each row's game date
  2. Each row represents one game from the home team perspective with situational features (home/away flag, rest days, week number, divisional game flag) populated
  3. Automated leakage validation tests pass -- confirming no feature for game G uses data from game G or any later game -- and these tests block model training if they fail
  4. Feature matrix covers all seasons 2005-2024 with no gaps in coverage
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — Feature definitions, build pipeline, DB schema, and unit tests
- [x] 02-02-PLAN.md — Leakage validation tests and CLI entry point
- [x] 02-03-PLAN.md — Gap closure: fix game_features DDL column names to match pipeline output

### Phase 3: Model Training and Autoresearch
**Goal**: An XGBoost win/loss classifier achieves above 60% accuracy on the 2023 validation season, beating both trivial baselines, via a governed experiment loop with full logging
**Depends on**: Phase 2
**Requirements**: MODL-01, MODL-02, MODL-03, MODL-04, MODL-05, MODL-06, MODL-07
**Success Criteria** (what must be TRUE):
  1. Model is trained on 2005-2022 data, validated on 2023, with 2024 held out untouched -- temporal split is enforced and cannot be accidentally violated
  2. Every experiment is logged to both experiments.jsonl and MLflow with params, 2023 validation accuracy, trivial baseline comparisons (always-home, better-record), multi-season accuracy (2021/2022), and TreeSHAP feature importance
  3. The autoresearch loop reads models/program.md, modifies only models/train.py, runs training, and keeps the result only if 2023 validation accuracy improves over the previous best -- otherwise it reverts
  4. The best model beats the always-home baseline (~57%) and the better-record baseline (~60%) on the 2023 validation season specifically
  5. At least 5 logged experiments exist showing iterative improvement with keep/revert decisions recorded
**Plans:** 3/3 plans complete

Plans:
- [x] 03-01-PLAN.md — ML dependencies, baselines module, and baseline unit tests
- [x] 03-02-PLAN.md — Training pipeline with temporal split, dual logging, TreeSHAP, and multi-season eval
- [x] 03-03-PLAN.md — Experiment queue (program.md) and autoresearch loop execution with 5+ experiments

### Phase 4: Prediction API
**Goal**: Predictions and model metadata are accessible via stable FastAPI endpoints that the dashboard can consume
**Depends on**: Phase 3
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. GET /api/predictions/week/{week} returns the predicted winner and confidence score for each game in the specified week
  2. GET /api/predictions/history returns all past predictions paired with actual outcomes
  3. GET /api/model/info returns the current model version, training date, and 2023 validation accuracy
  4. POST /api/model/reload hot-swaps the serving model to a newly staged version without restarting the server
**Plans:** 2/2 plans complete

Plans:
- [x] 04-01-PLAN.md — Prediction pipeline (predict.py), DB schema (predictions table), and API contracts (schemas, config)
- [x] 04-02-PLAN.md — FastAPI application with all endpoints, test suite, and human verification

### Phase 5: Dashboard
**Goal**: Users can view this week's predictions, track model performance against baselines, compare experiments, and review prediction history through a React dashboard
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Dashboard shows this week's games with predicted winner, win probability percentage, and a confidence tier label (high/medium/low) for each game
  2. Dashboard shows season accuracy summary comparing model record against always-home and better-record baselines for the current season
  3. Dashboard shows experiment scoreboard listing all logged experiments with 2023 validation accuracy, key parameters, and keep/revert status
  4. Dashboard shows historical predictions log with actual outcomes and clear correct/incorrect visual indicators
**Plans:** 2/2 plans complete

Plans:
- [x] 05-01-PLAN.md — Scaffold React + Vite + shadcn/ui project, TypeScript types, API client, TanStack Query hooks, sidebar layout, and shared components
- [x] 05-02-PLAN.md — Build all 4 page views (This Week's Picks, Season Accuracy, Experiment Scoreboard, Prediction History) and visual verification

### Phase 6: Pipeline and Deployment
**Goal**: The full system runs in Docker Compose on a Linux VPS with automated weekly data refresh and a human approval gate before model deployment
**Depends on**: Phase 5
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):
  1. Running docker compose up starts all services (postgres, api, mlflow, frontend, worker) and the system is usable end-to-end
  2. Weekly refresh automatically fetches new game data, recomputes features, and stages a retrained candidate model without manual intervention
  3. A staged model does not go live until POST /api/model/reload is explicitly called -- the human approval gate prevents automatic deployment of untested models
  4. Data and model artifacts persist across container rebuilds via named Docker volumes
**Plans:** 2/2 plans complete

Plans:
- [x] 06-01-PLAN.md — Pipeline module (refresh.py + worker.py) with 4-step weekly refresh and APScheduler entrypoint
- [x] 06-02-PLAN.md — Docker infrastructure (Dockerfile, Caddyfile, docker-compose.yml) and full 5-service stack configuration

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 2/2 | Complete   | 2026-03-16 |
| 2. Feature Engineering | 3/3 | Complete | 2026-03-16 |
| 3. Model Training and Autoresearch | 3/3 | Complete   | 2026-03-17 |
| 4. Prediction API | 2/2 | Complete | 2026-03-17 |
| 5. Dashboard | 2/2 | Complete | 2026-03-17 |
| 6. Pipeline and Deployment | 2/2 | Complete   | 2026-03-18 |
