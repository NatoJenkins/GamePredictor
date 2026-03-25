# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 -- MVP

**Shipped:** 2026-03-18
**Phases:** 6 | **Plans:** 14 | **Execution time:** 1.37 hours

### What Was Built
- Full NFL game prediction pipeline: ingestion, feature engineering, model training, API, dashboard, deployment
- XGBoost classifier at 62.89% accuracy on 2023 validation, beating both trivial baselines
- React dashboard with 4 views (picks, accuracy, experiments, history)
- Docker Compose deployment with 5 services and automated weekly refresh
- 126 commits, ~8,200 LOC (Python + TypeScript + SQL)

### What Worked
- Strict linear phase dependencies meant each phase built cleanly on verified output from the previous
- Autoresearch experiment loop (5 experiments, 2 kept / 3 reverted) efficiently explored the feature/hyperparameter space
- Leakage validation tests as a hard gate prevented data contamination throughout
- Per-phase verification caught the DDL column name mismatch before it became a runtime bug
- Average plan execution time of 5.9 minutes kept momentum high

### What Was Inefficient
- SUMMARY.md one_liner fields were never populated, requiring manual accomplishment extraction at milestone close
- Phase 2 needed an unplanned 02-03 gap closure plan for DDL column names -- could have been caught in plan review
- Nyquist validation files were generated but never fully executed (all 6 phases PARTIAL)
- SITUATIONAL_FEATURES constant in definitions.py drifted from actual column names -- unused but misleading

### Patterns Established
- shift(1) + expanding window as the canonical rolling feature pattern
- Lazy imports in pipeline functions to avoid circular dependencies
- TypeScript types mirroring Pydantic schemas field-for-field as the frontend/backend contract
- Models volume read-only for API, read-write for worker as the deployment access pattern
- Token-protected reload endpoint as the human approval gate

### Key Lessons
1. DDL-to-code column alignment should be verified in plan review, not discovered during verification -- a 2-minute check prevents a gap closure plan
2. Full 17-feature set proved near-optimal; ablation experiments all degraded accuracy -- start with everything and prune, rather than building up incrementally
3. Lower learning rate + early stopping was the single biggest accuracy improvement (Exp 5) -- try regularization before feature engineering
4. Per-season rolling reset is essential for NFL data -- rosters change year to year
5. Caddy + relative URLs eliminated CORS issues for production; hardcoded localhost CORS is fine behind a proxy

### Cost Observations
- Model mix: quality profile (opus for orchestration, sonnet for agents)
- Total execution: ~1.37 hours across 14 plans
- Notable: 3-day end-to-end from project init to shipped milestone is highly efficient for a full-stack ML system

---

## Milestone: v1.1 -- Point Spread Model

**Shipped:** 2026-03-24
**Phases:** 4 | **Plans:** 10 | **Execution time:** ~2 days

### What Was Built
- Ridge regression spread model (MAE 10.68, 60.2% derived winner accuracy)
- Spread predictions integrated across API, dashboard PickCards, accuracy page, and history
- Weekly pipeline step 5 for automated spread inference
- Season selector, info tooltips, spread summary cards on accuracy page

### What Worked
- Reusing the existing experiment loop pattern from v1.0 made spread model training straightforward
- Integrated dashboard approach (spreads on existing PickCards) avoided a separate page and kept the UI unified
- Non-fatal pipeline step design meant spread failures don't block Pick-Em predictions

### What Was Inefficient
- Sportsbook sign convention was corrected mid-milestone after initial implementation used the wrong direction
- Multiple small fix commits for sign display suggest the spec should have included explicit examples

### Patterns Established
- Sportsbook sign convention: negative = favorite, positive = underdog
- "Pick-Em" branding (hyphenated) as canonical term
- Non-fatal pipeline steps for secondary models

### Key Lessons
1. Define display conventions (sign direction, formatting) explicitly in requirements before implementation
2. Ridge regression can be competitive with XGBoost for regression tasks on small datasets
3. Integrating into existing UI components is faster than building new pages

---

## Milestone: v1.2 -- Design & Landing Page

**Shipped:** 2026-03-25
**Phases:** 4 | **Plans:** 5 | **Execution time:** ~1 day

### What Was Built
- silverreyes.net design system: amber palette, Syne + IBM Plex Mono self-hosted fonts, semantic color tokens
- Replaced 36 hardcoded Tailwind color classes across 14 components with theme tokens
- Two-branch route structure: LandingLayout (full-width) and AppLayout (sidebar)
- Landing page with hero, how-it-works, explore CTAs, and footer
- Fixed experiment table column alignment and full hypothesis display

### What Worked
- Two-plan split for Phase 11 (foundation + migration) kept each plan focused and reviewable
- Self-hosted fonts via @fontsource eliminated FOUT and external CDN dependency
- Removing Collapsible component entirely (instead of patching) was the right call -- the underlying HTML invalidity couldn't be fixed with wrapper hacks

### What Was Inefficient
- DSGN-01 through DSGN-04 requirements were completed but never marked in the traceability table -- bookkeeping gap
- Phase 14 research step was skipped (has_research: false) -- the root cause analysis was done during discuss-phase instead, which worked fine but broke the expected artifact chain

### Patterns Established
- Semantic token strategy: tier-high/medium/low for confidence, status-success/error/warning for outcomes
- Two-layout route branching for marketing vs app pages
- Plain state-driven expand/collapse instead of third-party collapsible components for HTML tables

### Key Lessons
1. Update requirement traceability as part of plan completion, not at milestone close -- stale checkboxes create false alarms during readiness checks
2. When a third-party component renders invalid HTML (div inside tbody), remove it entirely rather than trying to work around it
3. Design system migration is most efficient as foundation + sweep -- first lay tokens, then grep-replace all hardcoded classes

### Cost Observations
- Model mix: quality profile (opus orchestration, sonnet verification)
- 4 phases completed in a single day
- Notable: smallest milestone yet (5 plans) but highest visual impact

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Execution Time | Phases | Key Change |
|-----------|---------------|--------|------------|
| v1.0 | 1.37 hours | 6 | Initial project -- established all patterns |
| v1.1 | ~2 days | 4 | Added second model type (regression) |
| v1.2 | ~1 day | 4 | Design system + landing page -- UI-focused milestone |

### Cumulative Quality

| Milestone | Tests | Verification Score | Tech Debt Items |
|-----------|-------|--------------------|-----------------|
| v1.0 | 102+ passing | 28/28 requirements | 3 (all minor) |
| v1.1 | 110+ passing | 13/13 requirements | 2 (Postgres test, stale predictions) |
| v1.2 | N/A (UI-only) | 12/14 shipped + 2 deferred | 0 |

### Top Lessons (Verified Across Milestones)

1. Verify DDL-to-code alignment during planning, not after execution
2. Start with the full feature set and prune -- ablation is cheaper than incremental feature addition
3. Regularization (learning rate, early stopping) before feature engineering for accuracy gains
4. Define display conventions explicitly in specs before implementation (v1.1 sign convention fix)
5. Update requirement traceability during plan execution, not at milestone close (v1.2 stale checkboxes)
6. When third-party components generate invalid HTML, remove entirely rather than patch (v1.2 Collapsible removal)
