# Roadmap: NFL Game Predictor

## Milestones

- **v1.0 MVP** -- Phases 1-6 (shipped 2026-03-18)
- **v1.1 Point Spread Model** -- Phases 7-10 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-6) -- SHIPPED 2026-03-18</summary>

- [x] Phase 1: Data Foundation (2/2 plans) -- completed 2026-03-16
- [x] Phase 2: Feature Engineering (3/3 plans) -- completed 2026-03-16
- [x] Phase 3: Model Training and Autoresearch (3/3 plans) -- completed 2026-03-17
- [x] Phase 4: Prediction API (2/2 plans) -- completed 2026-03-17
- [x] Phase 5: Dashboard (2/2 plans) -- completed 2026-03-17
- [x] Phase 6: Pipeline and Deployment (3/3 plans) -- completed 2026-03-22

Full details archived to `milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Point Spread Model

**Milestone Goal:** Add an XGBoost regression model that predicts point spread (margin of victory) alongside the existing win/loss classifier, integrated across API, dashboard, and pipeline.

- [x] **Phase 7: Spread Model Training** - Formalize prototype into production-grade training with validated metrics and experiment logging
- [x] **Phase 8: Database and API Integration** - Spread predictions table and API endpoints serving spread data alongside classifier
- [ ] **Phase 9: Dashboard Integration** - PickCards show spread predictions side-by-side with classifier, plus spread performance metrics
- [ ] **Phase 10: Pipeline and Production Deployment** - Weekly spread inference, historical seeding, and production deploy

## Phase Details

### Phase 7: Spread Model Training
**Goal**: A validated, production-ready spread model with reproducible training, proper evaluation against baselines, and experiment logging
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: TRAIN-01, TRAIN-02, TRAIN-03, TRAIN-04, TRAIN-05
**Success Criteria** (what must be TRUE):
  1. Running train_spread.py produces a best_spread_model.json artifact that loads successfully with XGBoost
  2. Training output reports MAE, RMSE, and derived win accuracy on 2023 validation, plus MAE/RMSE on 2021 and 2022 seasons
  3. Training output reports naive baselines (always +2.5 and always 0) and the spread model beats both on MAE
  4. Each training run appends a complete entry to spread_experiments.jsonl with model params, metrics, and timestamp
  5. Model artifact is saved alongside classifier artifacts in models/artifacts/
**Plans:** 3 plans
Plans:
- [x] 07-01-PLAN.md -- Production hardening: fix objective function, create spread_program.md, write test suite
- [x] 07-02-PLAN.md -- Run 3-5 experiment sweep, update program document with results
- [x] 07-03-PLAN.md -- Gap closure: fix Exp 2 JSONL missing objective field (TRAIN-04)

### Phase 8: Database and API Integration
**Goal**: Spread predictions are stored in the database and served via API endpoints alongside the existing classifier predictions
**Depends on**: Phase 7
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. A spread_predictions table exists with columns for predicted_spread, predicted_winner, model_id, and post-game actual values
  2. GET /api/predictions/spreads/week/{season}/{week} returns spread predictions for every game in that week
  3. GET /api/model/info returns spread model metadata (MAE, training date) alongside existing classifier info
  4. The spread model loads automatically at API startup via the lifespan handler without manual intervention
**Plans:** 2 plans
Plans:
- [x] 08-01-PLAN.md -- Spread prediction foundation: DDL, predict.py functions, schemas, config, tests
- [x] 08-02-PLAN.md -- API wiring: spreads route, lifespan loading, model info/reload extension, API tests

### Phase 9: Dashboard Integration
**Goal**: Users see spread predictions alongside classifier predictions on every game, with spread-specific performance metrics
**Depends on**: Phase 8
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Each PickCard displays the predicted point spread next to the classifier's win probability
  2. A performance summary shows the spread model's MAE on completed games
  3. After games complete, PickCards show the actual margin and how far off the spread prediction was
  4. Dashboard displays a comparison of how often the spread model vs the classifier correctly picks the winner
**Plans:** 3 plans
Plans:
- [x] 09-01-PLAN.md -- Data layer: TypeScript types, API functions, TanStack Query hooks, backend spread history endpoint
- [ ] 09-02-PLAN.md -- PickCard spread display: SpreadLabel component, PickCard/PicksGrid/ThisWeekPage/HistoryTable wiring
- [ ] 09-03-PLAN.md -- Accuracy page spread metrics: SpreadSummaryCards with MAE, winner accuracy, agreement breakdown

### Phase 10: Pipeline and Production Deployment
**Goal**: Spread predictions are generated automatically each week and the complete v1.1 system is deployed to production
**Depends on**: Phase 8, Phase 9
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
  1. The weekly pipeline generates spread predictions (inference only) for the current week alongside classifier predictions
  2. A seed script populates historical spread predictions for the 2023 validation season so the dashboard has data on first deploy
  3. All v1.1 changes are live at nostradamus.silverreyes.net with spread predictions visible on the dashboard
**Plans**: TBD

## Progress

**Execution Order:** Phase 7 -> 8 -> 9 -> 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 2/2 | Complete | 2026-03-16 |
| 2. Feature Engineering | v1.0 | 3/3 | Complete | 2026-03-16 |
| 3. Model Training and Autoresearch | v1.0 | 3/3 | Complete | 2026-03-17 |
| 4. Prediction API | v1.0 | 2/2 | Complete | 2026-03-17 |
| 5. Dashboard | v1.0 | 2/2 | Complete | 2026-03-17 |
| 6. Pipeline and Deployment | v1.0 | 3/3 | Complete | 2026-03-22 |
| 7. Spread Model Training | v1.1 | 3/3 | Complete | 2026-03-23 |
| 8. Database and API Integration | v1.1 | 2/2 | Complete | 2026-03-23 |
| 9. Dashboard Integration | v1.1 | 1/3 | In progress | - |
| 10. Pipeline and Production Deployment | v1.1 | 0/? | Not started | - |
