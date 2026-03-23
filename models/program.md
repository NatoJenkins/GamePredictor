# Experiment Program

## Baselines (Fixed Reference)
- Always-home accuracy (2023): 55.51%
- Better-record accuracy (2023): 58.20%
- Always-home game count (2023): 272
- Better-record game count (2023, excl. ties + NaN week-1): 256

## Current Best
| Metric      | Value  |
|-------------|--------|
| 2021        | 69.02% |
| 2022        | 69.69% |
| 2023        | 62.89% |
| Log Loss    | 0.6564 |
| Brier Score | 0.2323 |

Best experiment: **Exp 5** (lr=0.1, n_estimators=300, early_stopping_rounds=20, all 17 features)

## Termination Conditions
1. Stop after 20 experiments total
2. Stop if 3 consecutive experiments show <0.3% improvement
3. Stop if 2021/2022 accuracy degrades while 2023 improves (overfitting signal)

## Experiment Queue

Queue order: vary the signal first, then tune the noise.

### Phase 1: Baseline (Experiment 1)
- [x] **Exp 1**: XGBoost with all 17 features, default hyperparameters -> **60.16% (KEEP)**
  - n_estimators=100, max_depth=6, learning_rate=0.3, subsample=1.0, colsample_bytree=1.0, reg_alpha=0, reg_lambda=1, min_child_weight=1, gamma=0
  - Hypothesis: Establish baseline accuracy with default XGBoost on full feature set
  - Result: 60.16% accuracy, but massive overfitting (2022=100%, 2021=98.8%)

### Phase 2: Feature Ablation (Experiments 2-4)
NOTE: These are all drop experiments (one-directional ablation). They test whether removing features improves accuracy, but don't test whether adding features (e.g., different rolling windows, feature interactions) would help. If all ablations hurt accuracy, the conclusion is that the full feature set is already near-optimal -- worth noting but not a flaw in the queue.
- [x] **Exp 2**: Drop turnover features (turnovers_committed, turnovers_forced, turnover_diff -- 6 columns removed) -> **53.52% (REVERT)**
  - Hypothesis: Turnovers may be noisy game-to-game; removing may reduce overfitting
  - Result: Accuracy dropped to 53.52% -- turnovers are important predictive features
- [x] **Exp 3**: Drop EPA features (off_epa_per_play, def_epa_per_play -- 4 columns removed) -> **57.42% (REVERT)**
  - Hypothesis: EPA may overlap with point_diff; simpler model may generalize better
  - Result: Accuracy dropped to 57.42% -- EPA provides signal beyond point_diff
- [x] **Exp 4**: Drop situational features (home_rest, away_rest, div_game -- 3 columns removed) -> **58.59% (REVERT)**
  - Hypothesis: Rest days and divisional flag may add noise without predictive value
  - Result: Accuracy dropped to 58.59% -- situational features contribute marginal signal

### Phase 3: Hyperparameter Tuning (Experiments 5-10)
- [x] **Exp 5**: Reduce learning_rate to 0.1, increase n_estimators to 300, add early_stopping_rounds=20 -> **62.89% (KEEP)**
  - Hypothesis: Slower learning with more trees and early stopping prevents overfitting on small dataset
  - Result: Best so far. 62.89% accuracy (+2.73% over baseline), overfitting dramatically reduced (2022=69.7%, 2021=69.0%), log_loss=0.6564
- [x] **Exp 6**: SHAP-guided feature selection -- drop bottom 4 features (away_rolling_turnover_diff, div_game, away_rest, home_rest) -> **60.16% (REVERT)**
  - Hypothesis: Dropping lowest-importance SHAP features removes noise and improves generalization
  - Result: Accuracy dropped to 60.16% -- confirms all 17 features contribute, even low-SHAP ones
- [x] **Exp 7**: max_depth tuning [3,4,5,6,7,8] -> **62.89% at depth=6 (REVERT, no change)**
  - Hypothesis: Tuning max_depth optimizes bias-variance tradeoff
  - Result: depth=6 already optimal. Shallower (3-5) underfit, deeper (7-8) overfit. Sweep: 3=60.9%, 4=60.9%, 5=62.1%, 6=62.9%, 7=59.0%, 8=60.2%
- [x] **Exp 8**: learning_rate tuning [0.01,0.03,0.05,0.1,0.2] with n_estimators=1000 -> **63.28% at lr=0.01 (REVERT)**
  - Hypothesis: Lower learning rate with more rounds and early stopping finds a better optimum
  - Result: lr=0.01 gave 63.28% (+0.39pp) but log_loss worsened (0.6568 vs 0.6564). Below keep threshold (<0.5% AND no log_loss gain)
- [x] **Exp 9**: subsample=0.8 + colsample_bytree=0.8 -> **60.16% (REVERT)**
  - Hypothesis: Stochastic gradient boosting acts as regularization
  - Result: Accuracy dropped to 60.16% -- stochastic sampling hurt out-of-sample performance
- [x] **Exp 10**: min_child_weight tuning [1,3,5,7,10] -> **62.89% at mcw=1 (REVERT, no change)**
  - Hypothesis: Increasing min_child_weight prevents overly specific leaf nodes
  - Result: mcw=1 (default) already optimal. Sweep: 1=62.9%, 3=61.3%, 5=61.7%, 7=59.0%, 10=62.1%. Note: mcw=10 had best log_loss (0.6490) but worse accuracy

## Dead Ends (Do Not Retry)
- **Dropping turnover features** (Exp 2): Accuracy dropped 6.6pp. Turnovers are a core signal.
- **Dropping EPA features** (Exp 3): Accuracy dropped 2.7pp. EPA provides signal beyond point_diff.
- **Dropping situational features** (Exp 4): Accuracy dropped 1.6pp. Rest days and div_game contribute marginally but positively.
- **SHAP-guided feature selection** (Exp 6): Dropping bottom 4 SHAP features dropped accuracy 2.7pp. All 17 features contribute.
- **Stochastic sampling** (Exp 9): subsample=0.8 + colsample_bytree=0.8 dropped accuracy 2.7pp.
- **Conclusion**: All 17 features are net-positive. Feature ablation is a dead end for this feature set. The Exp 5 hyperparameters (lr=0.1, max_depth=6, n_estimators=300, early_stopping=20, min_child_weight=1) are already near-optimal -- individual hyperparameter sweeps found no improvement beyond noise.

## Session Log

### Session 1 (2026-03-17)
- Experiments: 1-5 (5 total, 2 kept, 3 reverted)
- Started: Exp 1 baseline with all defaults
- Key finding: Full feature set is near-optimal -- all ablations hurt accuracy
- Key improvement: Slower learning rate (0.1) + early stopping dramatically reduced overfitting and improved generalization
- Best: Exp 5 at 62.89% on 2023, beating both baselines (always-home 55.51%, better-record 58.20%)
- SHAP top-5: home_rolling_point_diff, away_rolling_off_epa_per_play, away_rolling_point_diff, away_rolling_win, home_rolling_off_epa_per_play

### Session 2 (2026-03-22)
- Experiments: 6-10 (5 total, 0 kept, 5 reverted)
- Strategy: SHAP-guided feature selection, then systematic hyperparameter tuning
- Key finding: Exp 5's configuration is already at a local optimum. All five experiments either matched or degraded performance.
- Closest challenger: Exp 8 (lr=0.01, n_estimators=1000) at 63.28% (+0.39pp) but failed keep threshold due to slightly worse log_loss
- Overfitting monitor: No overfitting signals detected (2021/2022 never degraded while 2023 improved)
- Termination note: 5 consecutive experiments with <0.5% improvement suggests hyperparameter optimization is exhausted for this model architecture and feature set
- Best remains: Exp 5 at 62.89%
- Suggested next directions (for future sessions):
  1. New feature engineering (different rolling windows, interaction features, strength-of-schedule)
  2. Alternative model architectures (logistic regression, random forest, neural net)
  3. Ensemble methods (blending XGBoost with a simpler model)
