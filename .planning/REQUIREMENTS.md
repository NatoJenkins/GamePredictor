# Requirements: NFL Game Predictor

**Defined:** 2026-03-15
**Core Value:** Pre-game win/loss predictions with calibrated confidence scores that beat trivial baselines on the 2023 validation season

## v1 Requirements

### Data Ingestion

- [ ] **DATA-01**: System ingests all regular season play-by-play data (2005–2024) from nfl-data-py into PostgreSQL
- [ ] **DATA-02**: System ingests game schedule/metadata (dates, home/away, final scores, week numbers) for all seasons 2005–2024
- [ ] **DATA-03**: Team abbreviations are normalized at ingestion (OAK→LV, SD→LAC, etc.) via a defined constants mapping — not inline string replacements — so the mapping is auditable and testable; downstream code assumes clean abbreviations
- [ ] **DATA-04**: Ingestion validates row counts, season completeness, and schema drift — surfaces errors before feature computation proceeds

### Feature Engineering

- [ ] **FEAT-01**: System computes rolling EPA/play features (offensive and defensive) using only data prior to each game — strictly no leakage
- [ ] **FEAT-02**: System computes rolling basic game stats (point differential, turnover differential, win rate) using only prior-game data
- [ ] **FEAT-03**: System computes situational features per game: home/away flag, rest days, week of season, divisional game flag
- [ ] **FEAT-04**: Feature matrix is structured as one row per game from the home team perspective
- [ ] **FEAT-05**: Automated leakage validation tests run against the feature pipeline and must pass before any model training proceeds

### Model Training

- [ ] **MODL-01**: System trains an XGBoost win/loss classifier with temporal split: train 2005–2022, validate 2023, holdout 2024
- [ ] **MODL-02**: Every training run logs params, 2023 validation accuracy, and model artifact path to experiments.jsonl and MLflow
- [ ] **MODL-03**: Every training run logs trivial baseline accuracies (always-home-team wins, better-season-record wins) on the 2023 validation season alongside model accuracy — from experiment #1 onward
- [ ] **MODL-04**: Every training run logs validation accuracy on 2021 and 2022 seasons in addition to 2023 — for overfitting detection only; keep/revert decisions are based on 2023 accuracy exclusively
- [ ] **MODL-05**: Autoresearch experiment loop: agent reads models/program.md, selects next experiment, modifies only models/train.py, runs training, keeps if 2023 val accuracy improves over previous best, reverts otherwise
- [ ] **MODL-06**: Model must beat both trivial baselines (always-home ~57%, better-record ~60%) on the 2023 validation season before being considered production-ready
- [ ] **MODL-07**: TreeSHAP feature importance is computed post-training and logged as a summary to experiments.jsonl — not computed at inference time

### Prediction API

- [ ] **API-01**: GET /predictions/week/{week} returns predicted winner and confidence score per game for the specified week
- [ ] **API-02**: GET /predictions/history returns all past predictions with actual outcomes
- [ ] **API-03**: GET /model/info returns current model version, training date, and 2023 validation accuracy
- [ ] **API-04**: POST /model/reload hot-swaps the serving model after manual approval of a new version

### Dashboard

- [ ] **DASH-01**: Dashboard displays this week's games with predicted winner, win probability, and confidence tier (high/medium/low)
- [ ] **DASH-02**: Dashboard displays season accuracy summary: model record vs always-home and better-record baselines for the current season
- [ ] **DASH-03**: Dashboard displays experiment scoreboard: all logged experiments with 2023 val accuracy, key params, and keep/revert status
- [ ] **DASH-04**: Dashboard displays historical predictions log: all past predictions with actual outcome and correct/incorrect highlight

### Pipeline & Deployment

- [ ] **PIPE-01**: Weekly refresh automatically fetches new game data and recomputes features on a schedule (APScheduler)
- [ ] **PIPE-02**: Weekly refresh automatically retrains and stages a candidate model on updated data — staged only, not live until manual approval via PIPE-03
- [ ] **PIPE-03**: New model is staged but not live until POST /model/reload is called manually — human approval gate before deployment
- [ ] **PIPE-04**: Full stack runs under Docker Compose: postgres, api, mlflow, frontend, worker services

## v2 Requirements

### Model Enhancements

- **MODL-V2-01**: Probability calibration (Platt scaling or isotonic regression) on validation set
- **MODL-V2-02**: Advanced engineered features: CPOE, success rate, weighted rolling averages, opponent adjustments
- **MODL-V2-03**: QB consistency features (EPA standard deviation across games)

### Dashboard Enhancements

- **DASH-V2-01**: SHAP-based feature importance display per prediction in the dashboard
- **DASH-V2-02**: Calibration plot: predicted win probability vs actual win rate by probability bucket
- **DASH-V2-03**: Model performance over time chart (rolling accuracy by week)
- **DASH-V2-04**: Weekly recap view with correct/incorrect game highlights

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live / in-game predictions | Requires real-time data feed — entirely different architecture |
| Vegas spread/over-under integration | Out of scope for v1; confidence from model probability only |
| Player-level features (injuries, availability) | Team aggregates sufficient for v1; player data adds significant ingestion complexity |
| Mobile app | Web dashboard only |
| User accounts / authentication | Single-user or open read access |
| SHAP at inference time | Adds dependency, slows serving, requires dashboard design — deferred to v2 |
| Neural network models | Gradient boosting outperforms deep learning on small structured tabular data (~5K game rows) |
| Betting advice framing | Out of scope — predictions only, no wagering guidance |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| FEAT-01 | — | Pending |
| FEAT-02 | — | Pending |
| FEAT-03 | — | Pending |
| FEAT-04 | — | Pending |
| FEAT-05 | — | Pending |
| MODL-01 | — | Pending |
| MODL-02 | — | Pending |
| MODL-03 | — | Pending |
| MODL-04 | — | Pending |
| MODL-05 | — | Pending |
| MODL-06 | — | Pending |
| MODL-07 | — | Pending |
| API-01 | — | Pending |
| API-02 | — | Pending |
| API-03 | — | Pending |
| API-04 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |
| DASH-03 | — | Pending |
| DASH-04 | — | Pending |
| PIPE-01 | — | Pending |
| PIPE-02 | — | Pending |
| PIPE-03 | — | Pending |
| PIPE-04 | — | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 0
- Unmapped: 28 ⚠️

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after initial definition*
