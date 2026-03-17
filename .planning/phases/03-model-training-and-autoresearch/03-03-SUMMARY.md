---
phase: 03-model-training-and-autoresearch
plan: 03
subsystem: model
tags: [xgboost, autoresearch, experiment-loop, program-md, feature-ablation, hyperparameter-tuning]

# Dependency graph
requires:
  - phase: 03-model-training-and-autoresearch
    plan: 01
    provides: "models/ package with baselines.py, ML dependencies installed"
  - phase: 03-model-training-and-autoresearch
    plan: 02
    provides: "models/train.py with load_and_split, train_and_evaluate, log_experiment, should_keep"
provides:
  - "models/program.md with experiment queue, current best, dead ends, session log"
  - "5 experiments logged in models/experiments.jsonl (2 kept, 3 reverted)"
  - "Best model (Exp 5) at 62.89% on 2023 validation, beating both baselines"
  - "models/artifacts/best_model.json (XGBoost JSON format)"
  - "run_experiment() entry point in models/train.py for autoresearch orchestration"
affects: [04-calibration-and-evaluation]

# Tech tracking
tech-stack:
  added: []
  patterns: [autoresearch-loop, keep-revert-git, experiment-queue-program-md, feature-ablation-dead-end]

key-files:
  created: [models/program.md, models/experiments.jsonl, models/artifacts/best_model.json, models/artifacts/model_exp001.json, models/artifacts/model_exp005.json]
  modified: [models/train.py]

key-decisions:
  - "Full 17-feature set is near-optimal: all three ablation experiments hurt accuracy"
  - "Lower learning rate (0.1) + early stopping is the single biggest improvement lever"
  - "Experiment 1 always kept unconditionally as the initial baseline"

patterns-established:
  - "Autoresearch loop: read program.md, modify train.py config, run, keep/revert, log"
  - "Feature ablation dead end: dropping any feature group hurts accuracy on this dataset"
  - "Overfitting detection: in-sample 2021/2022 accuracy drops from 100% to 70% with regularization = healthy"

requirements-completed: [MODL-05, MODL-06]

# Metrics
duration: 9min
completed: 2026-03-17
---

# Phase 3 Plan 03: Autoresearch Experiment Loop Summary

**5 XGBoost experiments via autoresearch loop achieving 62.89% on 2023 validation, beating always-home (55.51%) and better-record (58.20%) baselines**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-17T01:13:17Z
- **Completed:** 2026-03-17T01:22:37Z
- **Tasks:** 3/3
- **Files modified:** 6

## Accomplishments
- Created experiment queue (program.md) with 10 planned experiments across 4 phases, computed baselines from real 2023 data
- Added run_experiment() entry point to train.py for autoresearch orchestration
- Executed 5 experiments: 2 kept (Exp 1 baseline, Exp 5 tuned), 3 reverted (Exp 2-4 ablations)
- Best model (Exp 5): 62.89% on 2023 with lr=0.1, 300 trees, early stopping -- beats both baselines
- Feature ablation confirmed all 17 features are net-positive (turnovers, EPA, situational all contribute)
- Overfitting dramatically reduced: in-sample accuracy dropped from 100%/99% to 70%/69% with slower learning

## Experiment Results

| Exp | Hypothesis | 2023 Acc | 2022 Acc | 2021 Acc | Log Loss | Decision |
|-----|-----------|----------|----------|----------|----------|----------|
| 1 | Default XGBoost baseline | 60.16% | 100.00% | 98.82% | 0.7521 | KEEP |
| 2 | Drop turnovers | 53.52% | 97.64% | 98.04% | 0.7890 | REVERT |
| 3 | Drop EPA | 57.42% | 99.61% | 97.25% | 0.7474 | REVERT |
| 4 | Drop situational | 58.59% | 99.61% | 98.04% | 0.7794 | REVERT |
| 5 | lr=0.1, 300 trees, early stopping | 62.89% | 69.69% | 69.02% | 0.6564 | KEEP |

## Task Commits

Each task was committed atomically:

1. **Task 1: Create program.md experiment queue and compute baselines** - `042fd9e` (feat)
2. **Task 2: Execute autoresearch loop** - multiple commits:
   - `865761c` (feat) - add experiment runner entry point to train.py
   - `91a9d54` (exp) - keep exp-1 baseline XGBoost defaults 60.16%
   - `407e81c` (exp) - keep exp-5 lr=0.1, 300 trees, early stopping 62.89%
   - `28fd07c` (exp) - update program.md with session 1 results

3. **Task 3: Verify autoresearch experiment results** - checkpoint:human-verify (approved)

**Plan metadata:** (pending final commit)

## Files Created/Modified
- `models/program.md` - Experiment queue with 10 planned experiments, baselines, current best, dead ends, session log
- `models/train.py` - Added run_experiment() entry point and __main__ block; config set to Exp 5 (best)
- `models/experiments.jsonl` - 5 experiment entries with full schema (params, accuracies, baselines, log_loss, brier_score, SHAP top-5, keep/revert)
- `models/artifacts/best_model.json` - Best XGBoost model (Exp 5) in native JSON format
- `models/artifacts/model_exp001.json` - Exp 1 baseline model artifact
- `models/artifacts/model_exp005.json` - Exp 5 best model artifact

## Decisions Made
- Full 17-feature set is near-optimal: all three ablation experiments (drop turnovers, drop EPA, drop situational) hurt 2023 accuracy by 1.6-6.6 percentage points
- Lower learning rate (0.1 vs 0.3) combined with early stopping is the single biggest improvement lever, boosting accuracy from 60.16% to 62.89% while dramatically reducing overfitting
- Experiment 1 always kept unconditionally as the initial baseline (no previous best to compare against)
- Feature ablation is a dead end for this dataset -- all features contribute positively

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- XGBoost `use_label_encoder` parameter triggers a UserWarning (known XGBoost 3.x change, does not affect functionality)
- MLflow `file:` tracking URI triggers a FutureWarning about database backend migration (file-based tracking sufficient for this project)
- Exp 1 showed extreme overfitting (2022=100%, 2021=99%) with default depth=6 -- expected behavior addressed by Exp 5

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Best model (Exp 5) saved as models/artifacts/best_model.json, ready for calibration in Phase 4
- program.md documents 5 remaining experiments (Exp 6-10) for potential future sessions
- SHAP top-5 features available in experiments.jsonl for Phase 4 feature importance analysis
- Full test suite green: 76 passed, 3 skipped

## Self-Check: PASSED

All 6 created files verified on disk. All 5 task commits (042fd9e, 865761c, 91a9d54, 407e81c, 28fd07c) verified in git log.

---
*Phase: 03-model-training-and-autoresearch*
*Completed: 2026-03-17*
