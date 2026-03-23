# Requirements: NFL Game Predictor

**Defined:** 2026-03-22
**Core Value:** Pre-game win/loss predictions with calibrated confidence scores that beat trivial baselines on the 2023 validation season

## v1.1 Requirements

Requirements for the Point Spread Model milestone. Each maps to roadmap phases.

### Spread Model Training

- [x] **TRAIN-01**: Training script produces XGBRegressor model predicting home point differential using same 17 features and temporal split as classifier
- [x] **TRAIN-02**: Training evaluates MAE, RMSE, and derived win accuracy on 2023 validation, plus MAE/RMSE on 2021 and 2022 for overfitting monitoring
- [x] **TRAIN-03**: Training computes and logs naive baselines (always +2.5 and always 0) for comparison
- [x] **TRAIN-04**: Experiments are logged to spread_experiments.jsonl (append-only) with full metadata
- [x] **TRAIN-05**: Best spread model is saved as best_spread_model.json alongside classifier artifacts

### Database & API

- [x] **API-01**: spread_predictions table stores per-game spread predictions with predicted_spread, predicted_winner, model_id, and post-game actuals
- [x] **API-02**: GET /api/predictions/spreads/week/{season}/{week} returns spread predictions per game for a given week
- [x] **API-03**: GET /api/model/info includes spread model metadata (MAE, training date) alongside classifier info
- [x] **API-04**: Spread model is loaded at API startup alongside the classifier via the lifespan handler

### Dashboard

- [x] **DASH-01**: Existing PickCards display predicted spread alongside classifier win probability per game
- [ ] **DASH-02**: Dashboard shows spread model MAE on a performance summary
- [x] **DASH-03**: After games complete, PickCards show actual result and spread prediction error
- [x] **DASH-04**: Dashboard shows how often spread model picks the correct winner vs the classifier

### Pipeline & Deployment

- [ ] **PIPE-01**: Weekly pipeline generates spread predictions (inference only, no retrain) for current week alongside classifier predictions
- [ ] **PIPE-02**: Seed script generates historical spread predictions for completed games (2023 validation season)
- [ ] **PIPE-03**: All changes deployed to production VPS at nostradamus.silverreyes.net

## Future Requirements

Deferred to v1.2+. Tracked but not in current roadmap.

### Totals Model

- **TOTAL-01**: XGBRegressor model predicting total combined score (over/under)
- **TOTAL-02**: API endpoint serving total predictions alongside spread and classifier
- **TOTAL-03**: Dashboard integration for over/under predictions

### Model Improvements

- **IMPR-01**: Probability calibration (Platt scaling or isotonic regression) on validation set
- **IMPR-02**: Advanced engineered features: CPOE, success rate, weighted rolling averages, opponent adjustments
- **IMPR-03**: QB consistency features (EPA standard deviation across games)
- **IMPR-04**: SHAP-based feature importance display per prediction in dashboard
- **IMPR-05**: Calibration plot: predicted win probability vs actual win rate by bucket
- **IMPR-06**: Model performance over time chart (rolling accuracy by week)
- **IMPR-07**: Weekly recap view with correct/incorrect game highlights

## Out of Scope

| Feature | Reason |
|---------|--------|
| Over/under totals model | Requires separate third model, deferred to v1.2 |
| Spread model auto-retraining in pipeline | Keeps v1.1 pipeline simple, manual retrain via train_spread.py |
| Vegas odds comparison | Model generates its own spreads, no external odds integration |
| Separate spreads dashboard page | Integrated into existing PickCards for unified view |
| Live in-game predictions | Pre-game only, no real-time scoring data |
| Player-level injury data | Team-level aggregate features only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRAIN-01 | Phase 7 | Complete |
| TRAIN-02 | Phase 7 | Complete |
| TRAIN-03 | Phase 7 | Complete |
| TRAIN-04 | Phase 7 | Complete |
| TRAIN-05 | Phase 7 | Complete |
| API-01 | Phase 8 | Complete |
| API-02 | Phase 8 | Complete |
| API-03 | Phase 8 | Complete |
| API-04 | Phase 8 | Complete |
| DASH-01 | Phase 9 | Complete |
| DASH-02 | Phase 9 | Pending |
| DASH-03 | Phase 9 | Complete |
| DASH-04 | Phase 9 | Complete |
| PIPE-01 | Phase 10 | Pending |
| PIPE-02 | Phase 10 | Pending |
| PIPE-03 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after roadmap creation*
