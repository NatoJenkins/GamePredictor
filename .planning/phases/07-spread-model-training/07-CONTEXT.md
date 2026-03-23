# Phase 7: Spread Model Training - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Formalize the spread regression prototype (`models/train_spread.py`) into production-grade training with a targeted experiment loop, validated metrics, and experiment logging. The prototype already meets all 5 success criteria — this phase runs regression-specific experiments to optimize the model and establishes formal tracking.

</domain>

<decisions>
## Implementation Decisions

### Experiment loop scope
- Targeted sweep of 3-5 experiments focused on regression-specific parameters
- Not a full autoresearch loop — classifier already proved all 17 features and Exp 5 hyperparams are near-optimal
- Focus areas: objective function variants (e.g., pseudohuberloss for outlier robustness), reg_alpha/reg_lambda tuning for regression, early stopping patience
- Fixed experiment budget — run the planned sweep and stop, no dynamic stopping conditions
- If no experiment beats Exp 1 baseline (MAE 10.68), ship Exp 1 as the production model

### Primary optimization metric
- MAE is the primary metric — this is a regression model, MAE directly measures spread prediction quality
- Derived win accuracy and RMSE are reported but secondary
- SHAP top-5 features continue to be logged per experiment

### Keep/revert threshold
- Keep if MAE improves by >= 0.1 points (current threshold, ~1% relative improvement)
- MAE-only gating — no secondary metric guards on the keep decision
- All metrics still logged for analysis (derived win accuracy, RMSE, overfitting monitoring on 2021/2022)

### Experiment tracking
- Create a separate `models/spread_program.md` for spread experiment program
- Tracks experiment queue, hypotheses, dead ends, and session logs
- Separate from classifier's `models/program.md` — different metrics, baselines, and dead ends
- `spread_experiments.jsonl` continues as the machine-readable append-only log

### Claude's Discretion
- Specific experiments in the 3-5 experiment queue (which regression params to try)
- spread_program.md structure and format
- Code cleanup/refactoring of train_spread.py if needed for production readiness
- Whether to add spread-specific tests

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Training pipeline
- `.planning/REQUIREMENTS.md` — TRAIN-01 through TRAIN-05 define all spread training requirements
- `.planning/ROADMAP.md` §Phase 7 — Success criteria (5 items, all currently met by prototype)

### Existing prototype
- `models/train_spread.py` — Full working prototype: data loading, splitting, training, evaluation, SHAP, JSONL logging, model saving
- `models/spread_experiments.jsonl` — Exp 1 baseline results (MAE 10.68, RMSE 13.87, derived win accuracy 60.16%)
- `models/artifacts/best_spread_model.json` — Current best spread model artifact

### Classifier reference (patterns to follow)
- `models/train.py` — Classifier training pipeline (spread mirrors this structure)
- `models/program.md` — Classifier experiment program (template for spread_program.md)

### Constraints
- `CLAUDE.md` — Critical rules: never modify features/build.py or definitions.py, experiments.jsonl is append-only, temporal split hardcoded
- `features/definitions.py` — FORBIDDEN_FEATURES list (result, home_score, away_score)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `models/train_spread.py`: Complete prototype — load_and_split_spread(), train_and_evaluate_spread(), compute_spread_baselines(), log_spread_experiment(), save_spread_model(), save_best_spread_model(), run_spread_experiment()
- `models/train.py`: Classifier pipeline with should_keep() logic — pattern for keep/revert decisions
- `features/build.py`: build_game_features() — shared feature builder used by both models
- `features/definitions.py`: FORBIDDEN_FEATURES, TARGET, META_COLS constants

### Established Patterns
- Module-level experiment config (EXPERIMENT_ID, EXPERIMENT_PARAMS, EXPERIMENT_HYPOTHESIS, DROP_FEATURES) — modified per experiment, not via CLI args
- XGBoost native JSON format for model artifacts (`model.save_model()`)
- TreeSHAP for feature importance (top 5 by mean absolute SHAP value)
- Multi-season evaluation (2023 held-out + 2021/2022 in-sample overfitting monitoring)

### Integration Points
- `models/artifacts/` — Model artifacts directory (both classifier and spread live here)
- `models/spread_experiments.jsonl` — Append-only log (1 entry exists from Exp 1)
- `data/loaders.py` — load_schedules_cached() for spread target (schedules.result)
- `data/sources.py` — TEAM_ABBREV_MAP and TEAM_COLUMNS_SCHEDULE constants

</code_context>

<specifics>
## Specific Ideas

- Classifier's experience showed that Exp 5 hyperparams survived 5 additional optimization experiments unchanged — spread may converge similarly quickly
- Spread Exp 1 already mirrors classifier Exp 5 hyperparams (lr=0.1, n_estimators=300, early_stopping=20)
- Naive baselines for spread: always +2.5 (MAE 11.02) and always 0 (MAE 11.26) — current model beats both
- SHAP top-5 for spread match classifier: rolling_point_diff dominant, then off_epa_per_play

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-spread-model-training*
*Context gathered: 2026-03-23*
