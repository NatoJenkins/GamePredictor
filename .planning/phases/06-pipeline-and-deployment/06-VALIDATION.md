---
phase: 6
slug: pipeline-and-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured in pyproject.toml) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ features/tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ features/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_refresh_steps_1_2 -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | PIPE-01 | unit | `pytest tests/test_pipeline.py::test_worker_schedule -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | PIPE-02 | unit | `pytest tests/test_pipeline.py::test_retrain_nonfatal -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | PIPE-03 | integration | `pytest tests/api/test_model.py::test_reload_model -x` | ✅ | ⬜ pending |
| 06-02-02 | 02 | 2 | PIPE-04 | smoke | `docker compose up -d && docker compose ps` | Manual | ⬜ pending |
| 06-02-03 | 02 | 2 | PIPE-04 | smoke | `docker compose ps --format json` | Manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pipeline.py` — stubs for PIPE-01, PIPE-02 (pipeline step execution, failure modes, staleness check)
- [ ] `pipeline/__init__.py` — package init
- [ ] `pipeline/refresh.py` — pipeline orchestration module
- [ ] `pipeline/worker.py` — APScheduler entrypoint

*Existing test infrastructure (pytest, conftest.py) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose starts all 5 services | PIPE-04 | Requires Docker runtime | `docker compose up -d` then `docker compose ps` — all services show "running" |
| Health checks pass for all services | PIPE-04 | Requires Docker runtime | `docker compose ps` — all services show "(healthy)" |
| Named volumes persist across rebuilds | PIPE-04 | Requires Docker runtime | `docker compose down && docker compose up -d` — data still present |
| Caddy provisions SSL cert | PIPE-04 | Requires live DNS + VPS | Verify HTTPS works after deploy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
