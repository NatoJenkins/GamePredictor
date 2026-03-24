# Requirements: NFL Game Predictor

**Defined:** 2026-03-24
**Core Value:** Pre-game win/loss and point spread predictions that beat trivial baselines, with a polished dashboard for tracking accuracy over time.

## v1.2 Requirements

Requirements for Design & Landing Page milestone. Each maps to roadmap phases.

### Design System

- [ ] **DSGN-01**: Dashboard uses silverreyes.net color palette (amber #f0a020 accent, near-black #080807 background, warm text tones) via CSS custom properties
- [ ] **DSGN-02**: Dashboard uses Syne (display/headings) and IBM Plex Mono (body/code) fonts, self-hosted via @fontsource
- [ ] **DSGN-03**: All hardcoded Tailwind color classes (zinc-*, blue-*, gray-*) are replaced with semantic theme tokens across all components
- [ ] **DSGN-04**: shadcn/ui component tokens (@theme inline block) are remapped to silverreyes.net-aligned values without breaking component functionality

### Landing Page

- [ ] **LAND-01**: Home page at `/` displays hero section with "NFL Nostradamus" in Syne display font, subtitle tagline ("20 seasons of play-by-play data. 17 engineered features. One question: who wins Sunday?"), and validation accuracy stat (62.9%) with amber accent on the number
- [ ] **LAND-02**: Home page displays "How It Works" section with 4 scannable blocks: Data (20 seasons, ~1.2M plays), Features (17 game-level features, temporal boundaries), Models (XGBoost 63.7% + Ridge ~10pt MAE), Pipeline (automated weekly refresh + human approval gate)
- [ ] **LAND-03**: Home page displays explore section with primary CTA "Explore Prediction History" (amber accent button) and secondary links to Accuracy and Experiments pages
- [ ] **LAND-04**: Home page displays footer area with "Built by Silver Reyes" linking to silverreyes.net and a GitHub link
- [ ] **LAND-05**: Home page includes placeholder image containers (amber accent border) for hero graphic and optional feature block visuals
- [ ] **LAND-06**: Home page uses a standalone full-width layout (no sidebar), distinct from the dashboard AppLayout
- [ ] **LAND-07**: Home page is responsive — hero headline + stat visible without scrolling on mobile

### Navigation

- [ ] **NAV-01**: Sidebar includes a Home tab linking to `/`
- [ ] **NAV-02**: This Week page moves from `/` to `/this-week` route
- [ ] **NAV-03**: All existing internal links and routes continue to work after restructure

### Experiments Redesign

- [ ] **EXPR-01**: Experiment table columns align properly with their data (fix current misalignment)
- [ ] **EXPR-02**: Each experiment displays a full title (not truncated) and a layman-friendly explanation of what was tested, while preserving technical detail (parameters, features, SHAP)
- [ ] **EXPR-03**: Experiments use a hybrid layout: sortable summary row with expandable detail panel per experiment
- [ ] **EXPR-04**: Kept vs reverted experiments are visually distinguishable beyond just the badge (e.g., accent border or background treatment)

## v1.3 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Over/Under Model

- **OU-01**: Over/under total points model trained alongside existing classifier and spread models
- **OU-02**: Over/under predictions displayed on dashboard with game totals

### Design Enhancements

- **DSGN-05**: Light mode toggle matching silverreyes.net data-theme="light" support
- **DSGN-06**: Grid background patterns and corner tick decorative elements from silverreyes.net

## Out of Scope

| Feature | Reason |
|---------|--------|
| Light mode toggle | Dark-only for v1.2; silverreyes.net light mode support deferred to v1.3 |
| Grid backgrounds / corner ticks / section dividers | Decorative elements deferred to v1.3 design enhancements |
| Spread experiments on Experiments page | Requires new API endpoint + different metric types; better scoped in v1.3 |
| Off-season conditional CTA swap | Landing page uses static validation stat for now; dynamic season-aware CTA is future work |
| Image generation or sourcing | User provides graphics; placeholders only in v1.2 |
| 404 catch-all route | Nice-to-have but not core to this milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DSGN-01 | TBD | Pending |
| DSGN-02 | TBD | Pending |
| DSGN-03 | TBD | Pending |
| DSGN-04 | TBD | Pending |
| LAND-01 | TBD | Pending |
| LAND-02 | TBD | Pending |
| LAND-03 | TBD | Pending |
| LAND-04 | TBD | Pending |
| LAND-05 | TBD | Pending |
| LAND-06 | TBD | Pending |
| LAND-07 | TBD | Pending |
| NAV-01 | TBD | Pending |
| NAV-02 | TBD | Pending |
| NAV-03 | TBD | Pending |
| EXPR-01 | TBD | Pending |
| EXPR-02 | TBD | Pending |
| EXPR-03 | TBD | Pending |
| EXPR-04 | TBD | Pending |

**Coverage:**
- v1.2 requirements: 18 total
- Mapped to phases: 0
- Unmapped: 18 (pending roadmap creation)

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after initial definition*
