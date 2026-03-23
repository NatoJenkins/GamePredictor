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

No experiment beat Exp 1 by >= 0.1 MAE -- Exp 1 shipped as production model.

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
- [x] **Exp 2**: Pseudo-Huber loss for outlier robustness -> **MAE 10.68 (REVERT)**
  - Params: objective="reg:pseudohubererror", huber_slope=1.0
  - Negligible improvement (delta 0.002). RMSE improved slightly (13.74 vs 13.87) but MAE essentially unchanged. Derived win accuracy dropped to 57.81%.
- [x] **Exp 3**: L2 regularization (reg_lambda=5.0) -> **MAE 10.58 (REVERT)**
  - Params: reg_lambda=5.0
  - Closest to threshold (delta 0.098, needed 0.100). Best MAE of all experiments but fell 0.002 short of keep threshold. RMSE also improved (13.71 vs 13.87).
- [x] **Exp 4**: Lower learning rate + more trees + longer patience -> **MAE 10.67 (REVERT)**
  - Params: learning_rate=0.05, n_estimators=500, early_stopping_rounds=50
  - Minor improvement (delta 0.015). Slower learning did not find a significantly better optimum. In-sample 2022 MAE slightly worse (8.86 vs 8.71).
- [x] **Exp 5** (conditional): Skipped -- no experiments showed >= 0.1 MAE improvement over Exp 1

## Dead Ends (Do Not Retry)

- **Pseudo-Huber loss** (Exp 2): Switching from squared error to Pseudo-Huber with huber_slope=1.0 produced nearly identical MAE (10.681 vs 10.683). The outlier-robust loss function did not meaningfully improve predictions despite NFL margins having heavy tails. The model already converges quickly (early stopping at ~9 iterations), so the loss function has minimal influence on the final model.
- **Higher L2 regularization** (Exp 3): reg_lambda=5.0 improved MAE to 10.584 (delta 0.098) but fell just short of the 0.1 keep threshold. Marginally better but not enough to justify a different configuration. The default regularization is sufficient for this problem.
- **Lower learning rate** (Exp 4): lr=0.05 with n_estimators=500 and early_stopping_rounds=50 produced MAE 10.668 (delta 0.015). Slower learning did not unlock a better optimum -- the loss surface for this problem is relatively simple and converges quickly regardless of learning rate.

## Session Log

### Session 1 (2026-03-23)
- Experiments: 2-4 (3 new, 0 kept, 3 reverted). Exp 5 skipped (no improvement found).
- Strategy: Regression-specific parameter sweep (Pseudo-Huber loss, L2 regularization, learning rate tuning)
- Key finding: The Exp 1 baseline (classifier Exp 5 hyperparams with reg:squarederror) is effectively optimal for this problem. All three alternative configurations produced marginal improvements (0.002 to 0.098 MAE) but none crossed the 0.1 keep threshold. The low signal-to-noise ratio in NFL point spreads (SD ~14.7) limits how much any parameter tuning can improve predictions. Exp 3 (reg_lambda=5.0) came closest at delta 0.098.
- Best: Exp 1 at MAE 10.68 on 2023, beating both baselines (always +2.5: 11.02, always 0: 11.26)
- SHAP top-5: home_rolling_point_diff (1.74), away_rolling_point_diff (1.12), away_rolling_off_epa_per_play (0.90), home_rolling_off_epa_per_play (0.38), away_rolling_win (0.37)
