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

### Phase 3: Hyperparameter Tuning (Experiments 5-7)
- [x] **Exp 5**: Reduce learning_rate to 0.1, increase n_estimators to 300, add early_stopping_rounds=20 -> **62.89% (KEEP)**
  - Hypothesis: Slower learning with more trees and early stopping prevents overfitting on small dataset
  - Result: Best so far. 62.89% accuracy (+2.73% over baseline), overfitting dramatically reduced (2022=69.7%, 2021=69.0%), log_loss=0.6564
- [ ] **Exp 6**: Reduce max_depth to 3 (from 6)
  - Hypothesis: Shallower trees generalize better on 4000-row dataset
- [ ] **Exp 7**: Set subsample=0.8, colsample_bytree=0.8
  - Hypothesis: Stochastic boosting reduces overfitting via ensemble diversity

### Phase 4: Regularization (Experiments 8-10)
- [ ] **Exp 8**: Increase reg_lambda to 5
  - Hypothesis: L2 regularization constrains leaf weights on small dataset
- [ ] **Exp 9**: Add reg_alpha=0.1 (L1 regularization)
  - Hypothesis: L1 sparsity may zero out noise features
- [ ] **Exp 10**: Set min_child_weight=5
  - Hypothesis: Larger minimum leaf size prevents learning from rare patterns

## Dead Ends (Do Not Retry)
- **Dropping turnover features** (Exp 2): Accuracy dropped 6.6pp. Turnovers are a core signal.
- **Dropping EPA features** (Exp 3): Accuracy dropped 2.7pp. EPA provides signal beyond point_diff.
- **Dropping situational features** (Exp 4): Accuracy dropped 1.6pp. Rest days and div_game contribute marginally but positively.
- **Conclusion**: All 17 features are net-positive. Feature ablation is a dead end for this feature set.

## Session Log

### Session 1 (2026-03-17)
- Experiments: 1-5 (5 total, 2 kept, 3 reverted)
- Started: Exp 1 baseline with all defaults
- Key finding: Full feature set is near-optimal -- all ablations hurt accuracy
- Key improvement: Slower learning rate (0.1) + early stopping dramatically reduced overfitting and improved generalization
- Best: Exp 5 at 62.89% on 2023, beating both baselines (always-home 55.51%, better-record 58.20%)
- SHAP top-5: home_rolling_point_diff, away_rolling_off_epa_per_play, away_rolling_point_diff, away_rolling_win, home_rolling_off_epa_per_play
- Suggested next 5 experiments:
  1. Exp 6: Reduce max_depth to 3 (shallow trees may generalize even better)
  2. Exp 7: Add subsample=0.8, colsample_bytree=0.8 (stochastic regularization)
  3. Exp 8: Increase reg_lambda to 5 (L2 regularization on top of slower learning)
  4. Exp 9: Combine max_depth=3 + subsample=0.8 + reg_lambda=5 (compound tuning)
  5. Exp 10: Set min_child_weight=5 (prevent fitting rare patterns)
