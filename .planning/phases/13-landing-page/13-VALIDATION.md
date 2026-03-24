---
phase: 13
slug: landing-page
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no frontend test framework installed |
| **Config file** | None |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build` + manual browser inspection
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | LAND-01 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |
| 13-01-02 | 01 | 1 | LAND-02 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |
| 13-01-03 | 01 | 1 | LAND-03 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |
| 13-01-04 | 01 | 1 | LAND-04 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |
| 13-01-05 | 01 | 1 | LAND-05 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |
| 13-01-06 | 01 | 1 | LAND-07 | build + manual | `cd frontend && npm run build` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. `npm run build` provides type-check + Vite bundling as automated smoke test.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hero section renders with headline, subtitle, accuracy stat | LAND-01 | Visual/layout — no test framework | Navigate to `/`, verify "NFL Nostradamus" headline in Syne font, tagline subtitle, 62.9% stat in amber |
| How It Works 4-block grid renders | LAND-02 | Visual/layout — no test framework | Verify 2x2 card grid with Data, Features, Models, Pipeline blocks with Lucide icons |
| CTA button navigates to `/history`, secondary links work | LAND-03 | Navigation — requires browser | Click "Explore Prediction History" → `/history`, click Accuracy → `/accuracy`, click Experiments → `/experiments` |
| Footer links to silverreyes.net and GitHub | LAND-04 | External links — requires browser | Click "Built by Silver Reyes" → silverreyes.net, click GitHub → repo URL |
| Banner image renders between sections | LAND-05 | Visual — requires browser rendering | Verify banner image appears between How It Works and CTA, max-w-4xl |
| Responsive — headline + stat visible on mobile | LAND-07 | Responsive — requires DevTools | Open Chrome DevTools, set viewport to 375px width, verify headline and accuracy stat visible without scrolling |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
