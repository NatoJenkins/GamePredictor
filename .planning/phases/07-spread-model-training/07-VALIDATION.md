---
phase: 7
slug: spread-model-training
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest models/tests/ -x -q` |
| **Full suite command** | `python -m pytest models/tests/ features/tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest models/tests/ -x -q`
- **After every plan wave:** Run `python -m pytest models/tests/ features/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | TRAIN-01 | integration | `python models/train_spread.py && python -c "import xgboost; xgboost.Booster().load_model('models/artifacts/best_spread_model.json')"` | ✅ | ⬜ pending |
| 07-01-02 | 01 | 1 | TRAIN-02 | integration | `python models/train_spread.py 2>&1 \| grep -E "MAE\|RMSE\|win_accuracy"` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | TRAIN-03 | integration | `python models/train_spread.py 2>&1 \| grep -E "baseline\|naive"` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | TRAIN-04 | unit | `python -m pytest models/tests/test_spread_logging.py -v` | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 1 | TRAIN-05 | integration | `ls models/artifacts/best_spread_model.json` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `models/tests/test_spread_logging.py` — stubs for TRAIN-04 experiment logging
- [ ] `models/tests/test_spread_metrics.py` — stubs for TRAIN-02, TRAIN-03 metric reporting

*Existing infrastructure covers artifact saving (TRAIN-01, TRAIN-05).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Spread model beats naive baselines on MAE | TRAIN-03 | Requires full training run and metric comparison | Run `python models/train_spread.py`, verify output shows model MAE < baseline MAE |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
