---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Point Spread Model
status: in-progress
stopped_at: Completed 09-02-PLAN.md
last_updated: "2026-03-23T22:03:43Z"
last_activity: 2026-03-23 -- Completed 09-02 PickCard spread display
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 8
  completed_plans: 7
  percent: 88
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-22)

**Core value:** Pre-game win/loss predictions with calibrated confidence scores that beat trivial baselines on the 2023 validation season
**Current focus:** v1.1 Point Spread Model -- Phase 9 in progress

## Current Position

Phase: 9 of 10 (Dashboard Integration)
Plan: 3 of 3 (Phase 9) -- next up
Status: Completed 09-02, ready for 09-03
Last activity: 2026-03-23 -- Completed 09-02 PickCard spread display (SpreadLabel, wiring, HistoryTable)

Progress: [████████░░] 88% (7/8 v1.1 plans complete)

## Performance Metrics

**Velocity (from v1.0):**
- Total plans completed: 17
- Average duration: 5.6min
- Total execution time: 1.58 hours

**v1.1 Execution:**

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 07 | 01 | 36min | 2 | 3 |
| 07 | 02 | 6min | 2 | 4 |
| 07 | 03 | 2min | 2 | 2 |
| 08 | 01 | 5min | 2 | 5 |
| 08 | 02 | 11min | 2 | 7 |
| 09 | 01 | 3min | 2 | 6 |
| 09 | 02 | 3min | 2 | 6 |

## Accumulated Context

### Decisions

Full decision log in PROJECT.md Key Decisions table.

**From v1.0:**
- 06-01: Preserved log_experiment() with JSONL-only logging, removed MLflow side-effect entirely
- 06-01: Removed setup_mlflow() function entirely rather than leaving as no-op
- 06-02: Added .gitattributes for LF enforcement on shell scripts (prevents CRLF Docker breakage on Windows)

**v1.1 prototyping:**
- Spread training script (train_spread.py) mirrors classifier structure, loads target from parquet cache (no DB needed for training)
- Spread Exp 1 baseline: MAE 10.68, RMSE 13.87, derived win accuracy 60.16% (vs classifier 62.89%)

**v1.1 Phase 8:**
- 08-01: Mirrored classifier function patterns for spread (load/select/generate) for consistency
- 08-01: Home-team convention for zero spread (predicted_spread == 0.0 -> home wins)
- 08-02: Spread endpoint uses path params {season}/{week} matching URL hierarchy convention
- 08-02: Spread reload generates predictions only when both current week and spread info available

**v1.1 Phase 9:**
- 09-02: SpreadLabel props accept null | undefined to match API type convention (actual_spread is null before game completes)

**v1.1 Phase 7:**
- 07-01: Used params.pop() to extract objective from hyperparams dict, enabling alternative loss functions
- 07-01: Created spread_program.md with Exp 1 baselines and experiment queue (Exps 2-5)
- 07-01: 14-test suite covering all 5 TRAIN requirements (temporal split, metrics, baselines, logging, model save)
- 07-02: Ship Exp 1 as production model -- no experiment beat baseline by >= 0.1 MAE (Exp 3 closest at 0.098)
- 07-02: Skip Exp 5 -- none of Exps 2-4 showed sufficient improvement to warrant combination
- 07-02: Fixed params.pop() mutation bug -- pass dict copy to preserve objective in JSONL log
- 07-03: Patched existing Exp 2 JSONL entry in-place rather than appending duplicate re-run entry

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-23T22:03:43Z
Stopped at: Completed 09-02-PLAN.md
Resume file: None
