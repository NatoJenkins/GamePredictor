# Spread Experiment Program

## Baselines (Fixed Reference)
- Always +2.5 MAE (2023): 11.02
- Always 0 MAE (2023): 11.26
- Classifier-derived win accuracy (2023): 62.89%

## Current Best
| Metric | Value |
|--------|-------|
| MAE 2023 | 10.68 |
| RMSE 2023 | 13.87 |
| Derived Win Acc 2023 | 60.16% |
| MAE 2022 | 8.71 |
| MAE 2021 | 10.61 |

Best experiment: **Exp 1** (baseline, reg:squarederror, lr=0.1, max_depth=6, n_estimators=300, early_stopping=20)

## Keep/Revert Threshold
- Keep if MAE improves by >= 0.1 points (~1% relative improvement)
- MAE-only gating -- no secondary metric guards
- All metrics logged regardless of keep decision

## Experiment Queue

Targeted sweep of 3-5 regression-specific experiments. Not a full autoresearch loop -- classifier already proved all 17 features and Exp 5 hyperparams are near-optimal.

### Phase 1: Baseline (Complete)
- [x] **Exp 1**: Baseline XGBRegressor(reg:squarederror), lr=0.1, n_estimators=300, early_stopping=20 -> **MAE 10.68 (KEEP)**
  - Mirrors classifier Exp 5 hyperparameters
  - Early stopping at iteration 9 (fast convergence)

### Phase 2: Regression-Specific Tuning (Experiments 2-5)
- [ ] **Exp 2**: Pseudo-Huber loss for outlier robustness
  - Params: objective="reg:pseudohubererror", huber_slope=1.0
  - Hypothesis: NFL margins have heavy tails (SD ~14.7). Pseudo-Huber reduces blowout influence, may improve MAE on typical games.
- [ ] **Exp 3**: L2 regularization (reg_lambda)
  - Params: reg_lambda=5.0
  - Hypothesis: Spread target is noisier than binary win/loss. Higher L2 regularization constrains leaf weights.
- [ ] **Exp 4**: Lower learning rate + more trees + longer patience
  - Params: learning_rate=0.05, n_estimators=500, early_stopping_rounds=50
  - Hypothesis: Model stops at iteration 9. Slower learning may find better optimum.
- [ ] **Exp 5** (conditional): Combined best from Exps 2-4
  - Only run if any of Exps 2-4 show improvement or promising direction

## Dead Ends (Do Not Retry)
(Updated after experiments)

## Session Log
(Updated after experiments)
