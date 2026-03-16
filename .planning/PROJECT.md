# NFL Game Predictor

## What This Is

An NFL game outcome prediction system that ingests historical play-by-play data (2005–2024), engineers game-level features, and trains a win/loss classifier. Predictions are served via a FastAPI backend and displayed in a React dashboard showing this week's picks with confidence scores and model performance history. Serves as both a personal tool and portfolio project, with potential to open to others.

## Core Value

Pre-game win/loss predictions with calibrated confidence scores that beat the Vegas baseline (>53% accuracy on the 2023 validation season).

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Ingest and store historical NFL game and play-by-play data (2005–2024) in PostgreSQL via nfl-data-py
- [ ] Engineer game-level features from play-by-play data with no data leakage (rolling stats use only prior-game data)
- [ ] Train a win/loss classifier (XGBoost), log all experiments to experiments.jsonl and MLflow
- [ ] Temporal split: train 2005–2022, validate 2023, holdout test 2024
- [ ] Beat benchmark of 53% validation accuracy (approximate Vegas baseline)
- [ ] Expose predictions via FastAPI endpoints (current week picks + historical results)
- [ ] Display predictions dashboard: this week's games with predicted winner + confidence score
- [ ] Display model scoreboard: historical experiment accuracy and comparison
- [ ] Weekly data refresh + model retrain pipeline — automatic fetch/retrain, manual approval before deploy
- [ ] Support keep/revert on model updates based on validation results
- [ ] Deploy via Docker Compose on Linux VPS

### Out of Scope

- Live in-game predictions — pre-game only, no real-time scoring data
- Vegas spread/over-under ingestion — confidence from model probability, not odds comparison
- Player-level injury/availability data — team-level aggregate features only for v1
- Mobile app — web dashboard only
- User accounts / authentication — single-user or open read access

## Context

- Data source: nfl-data-py (free, covers play-by-play back to 1999 but targeting 2005+)
- Critical constraint: all rolling/aggregate features must be computed from data strictly prior to the game being predicted — no future leakage
- Experiment tracking: every training run logged to both experiments.jsonl (flat file, portable) and MLflow (visual UI)
- The keep/revert pattern means a new model only goes live after manual inspection of validation metrics
- Docker Compose deployment targets a Linux VPS; local dev should mirror prod environment

## Constraints

- **Data leakage**: All rolling features must use only data prior to the game being predicted — strictly enforced
- **Temporal split**: Train 2005–2022, validate 2023, holdout 2024 — no shuffling across time boundaries
- **Stack**: Python 3.11, PostgreSQL, nfl-data-py, pandas, scikit-learn, XGBoost, FastAPI, React, Docker Compose, MLflow
- **Benchmark**: Must beat 53% validation accuracy before considering model production-ready
- **Deployment**: Docker Compose on Linux VPS — services must be containerized

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| nfl-data-py as data source | Free, comprehensive, covers 2005+ play-by-play | — Pending |
| XGBoost as primary classifier | Strong tabular performance, interpretable feature importance | — Pending |
| experiments.jsonl + MLflow dual logging | Portable flat file for scripting + visual UI for comparison | — Pending |
| Semi-automated pipeline | Automatic fetch/retrain but manual approval prevents bad models from auto-deploying | — Pending |
| Temporal train/val/test split | Prevents data leakage across seasons, mirrors real-world deployment | — Pending |

---
*Last updated: 2026-03-15 after initialization*
