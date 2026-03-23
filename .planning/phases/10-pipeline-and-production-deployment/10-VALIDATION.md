---
phase: 10
slug: pipeline-and-production-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via pyproject.toml) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/test_pipeline.py -x` |
| **Full suite command** | `pytest tests/ features/tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_pipeline.py -x`
- **After every plan wave:** Run `pytest tests/ features/tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_step5_generates_spread_predictions -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_step5_nonfatal_in_run_pipeline -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_step5_offseason_skips -x` | ❌ W0 | ⬜ pending |
| 10-01-04 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_run_pipeline_reads_spread_env_vars -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | PIPE-02 | unit | `pytest tests/test_seed_spread.py::test_seed_spread_predictions -x` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 1 | PIPE-02 | unit | `pytest tests/test_seed_spread.py::test_seed_spread_backfills_actuals -x` | ❌ W0 | ⬜ pending |
| 10-02-03 | 02 | 1 | PIPE-02 | unit | `pytest tests/test_seed_spread.py::test_seed_spread_idempotent -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | PIPE-03 | manual | Inspect docker-compose.yml | N/A | ⬜ pending |
| 10-03-02 | 03 | 2 | PIPE-03 | manual | Inspect docker/entrypoint.sh | N/A | ⬜ pending |
| 10-03-03 | 03 | 2 | PIPE-03 | manual | Visit nostradamus.silverreyes.net | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pipeline.py` — extend with step 5 tests: non-fatal behavior, offseason skip, spread env var reading, spread prediction generation
- [ ] `tests/test_seed_spread.py` — new file covering PIPE-02: seed generation, actuals backfill, idempotency

*Existing pytest infrastructure covers framework needs — no new install required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker compose has spread env vars for worker | PIPE-03 | Infrastructure config inspection | Verify `SPREAD_MODEL_PATH` and `SPREAD_EXPERIMENTS_PATH` present in worker service |
| Entrypoint seeds spread artifacts | PIPE-03 | Docker runtime behavior | Check entrypoint.sh copies `best_spread_model.json` and `spread_experiments.jsonl` |
| Production deploy successful | PIPE-03 | External system verification | Visit nostradamus.silverreyes.net, verify spread predictions visible on dashboard |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
