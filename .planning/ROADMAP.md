# Roadmap: NFL Game Predictor

## Milestones

- v1.0 MVP -- Phases 1-6 (shipped 2026-03-18)
- v1.1 Point Spread Model -- Phases 7-10 (shipped 2026-03-24)
- v1.2 Design & Landing Page -- Phases 11-14 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-6) -- SHIPPED 2026-03-18</summary>

- [x] Phase 1: Data Foundation (2/2 plans) -- completed 2026-03-16
- [x] Phase 2: Feature Engineering (3/3 plans) -- completed 2026-03-16
- [x] Phase 3: Model Training and Autoresearch (3/3 plans) -- completed 2026-03-17
- [x] Phase 4: Prediction API (2/2 plans) -- completed 2026-03-17
- [x] Phase 5: Dashboard (2/2 plans) -- completed 2026-03-17
- [x] Phase 6: Pipeline and Deployment (3/3 plans) -- completed 2026-03-22

Full details archived to `milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>v1.1 Point Spread Model (Phases 7-10) -- SHIPPED 2026-03-24</summary>

- [x] Phase 7: Spread Model Training (3/3 plans) -- completed 2026-03-23
- [x] Phase 8: Database and API Integration (2/2 plans) -- completed 2026-03-23
- [x] Phase 9: Dashboard Integration (3/3 plans) -- completed 2026-03-23
- [x] Phase 10: Pipeline and Production Deployment (2/2 plans) -- completed 2026-03-24

Full details archived to `milestones/v1.1-ROADMAP.md`

</details>

### v1.2 Design & Landing Page (In Progress)

**Milestone Goal:** Align the Nostradamus dashboard with the silverreyes.net design system, add a proper landing page as the new front door, and redesign the experiments view for readability.

- [x] **Phase 11: Design System Foundation** - Migrate dashboard to silverreyes.net warm amber palette, typography, and semantic tokens (completed 2026-03-24)
- [x] **Phase 12: Route Restructure and Navigation** - Move This Week to `/this-week`, add Home nav item, landing page route at `/` (completed 2026-03-24)
- [x] **Phase 13: Landing Page** - Hero section, how-it-works explainer, explore CTAs, and footer at `/` (completed 2026-03-24)
- [ ] **Phase 14: Experiments Redesign** - Fix column alignment and remove hypothesis truncation (EXPR-03/EXPR-04 deferred to v1.3)

## Phase Details

### Phase 11: Design System Foundation
**Goal**: Every dashboard component renders with the silverreyes.net visual identity -- warm amber palette, Syne + IBM Plex Mono typography, and semantic color tokens replacing all hardcoded Tailwind classes
**Depends on**: Phase 10 (v1.1 complete)
**Requirements**: DSGN-01, DSGN-02, DSGN-03, DSGN-04
**Success Criteria** (what must be TRUE):
  1. Dashboard background, text, and accent colors visually match the silverreyes.net warm amber palette (near-black background, amber accents, warm text tones)
  2. All headings render in Syne and all body/code text renders in IBM Plex Mono, with no flash of unstyled text on page load
  3. No hardcoded Tailwind color classes (zinc-*, blue-*, gray-*) remain in any component -- all colors reference semantic CSS custom properties
  4. All shadcn/ui components (buttons, cards, tooltips, dropdowns) display correctly with the remapped theme tokens -- no broken styles, missing borders, or invisible text
**Plans**: 2 plans

Plans:
- [x] 11-01-PLAN.md — Theme foundation: silverreyes.net palette, @fontsource fonts, tier/status tokens
- [x] 11-02-PLAN.md — Component migration: replace all hardcoded Tailwind color classes with semantic tokens

### Phase 12: Route Restructure and Navigation
**Goal**: The application routes are reorganized so `/` serves the landing page in a standalone layout while all dashboard pages live under their own routes with the sidebar, and navigation reflects the new structure
**Depends on**: Phase 11
**Requirements**: NAV-01, NAV-02, NAV-03
**Success Criteria** (what must be TRUE):
  1. Navigating to `/` renders a full-width page with no sidebar or dashboard chrome
  2. Navigating to `/this-week` renders the existing This Week page inside the dashboard layout with sidebar
  3. Sidebar displays a Home tab that links to `/`, and all other nav items point to their correct routes with proper active-state highlighting
  4. All previously bookmarkable dashboard routes (`/accuracy`, `/experiments`, `/history`) continue to work without changes
**Plans**: 1 plan

Plans:
- [x] 12-01-PLAN.md — Route restructure: two layout branches (LandingLayout + AppLayout), Home nav item, sidebar branding update

### Phase 13: Landing Page
**Goal**: Visitors arriving at `/` see a polished, informative landing page that communicates what Nostradamus does, how it works, and invites them to explore the dashboard
**Depends on**: Phase 11, Phase 12
**Requirements**: LAND-01, LAND-02, LAND-03, LAND-04, LAND-05, LAND-06, LAND-07
**Success Criteria** (what must be TRUE):
  1. Landing page displays a hero section with "NFL Nostradamus" headline in Syne display font, a tagline subtitle, and the validation accuracy stat (62.9%) with amber accent styling
  2. Landing page displays a "How It Works" section with four scannable blocks covering Data, Features, Models, and Pipeline
  3. Landing page displays explore CTAs -- a primary amber "Explore Prediction History" button and secondary links to Accuracy and Experiments -- that navigate to the correct dashboard routes
  4. Landing page displays a footer with "Built by Silver Reyes" linking to silverreyes.net and a GitHub link
  5. Landing page is responsive -- hero headline and accuracy stat are visible without scrolling on mobile viewports
**Plans**: 1 plan

Plans:
- [x] 13-01-PLAN.md — Full landing page content: hero, how-it-works, banner image, CTAs, footer, and visual verification

### Phase 14: Experiments Redesign
**Goal**: The experiments table has properly aligned columns and displays full hypothesis text without truncation, preserving existing expand/collapse and sorting functionality
**Depends on**: Phase 11
**Requirements**: EXPR-01, EXPR-02, EXPR-03, EXPR-04
**Note**: Scope narrowed per user decision. Only EXPR-01 (column alignment) and EXPR-02 (remove truncation) are implemented. EXPR-03 (hybrid layout) and EXPR-04 (kept visual distinction) are deferred to v1.3 backlog.
**Success Criteria** (what must be TRUE):
  1. Experiment table columns are properly aligned -- headers sit directly above their corresponding data columns with no visual drift
  2. Each experiment displays its full hypothesis text without truncation, with natural text wrapping
  3. Expand/collapse detail panel and column sorting functionality are preserved
**Plans**: 1 plan

Plans:
- [ ] 14-01-PLAN.md — Fix column alignment (remove Collapsible div wrappers) and remove hypothesis truncation

## Progress

**Execution Order:**
Phases execute in numeric order: 11 -> 12 -> 13 -> 14
Note: Phases 13 and 14 are independent and could execute in either order once 11 and 12 are complete.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 2/2 | Complete | 2026-03-16 |
| 2. Feature Engineering | v1.0 | 3/3 | Complete | 2026-03-16 |
| 3. Model Training and Autoresearch | v1.0 | 3/3 | Complete | 2026-03-17 |
| 4. Prediction API | v1.0 | 2/2 | Complete | 2026-03-17 |
| 5. Dashboard | v1.0 | 2/2 | Complete | 2026-03-17 |
| 6. Pipeline and Deployment | v1.0 | 3/3 | Complete | 2026-03-22 |
| 7. Spread Model Training | v1.1 | 3/3 | Complete | 2026-03-23 |
| 8. Database and API Integration | v1.1 | 2/2 | Complete | 2026-03-23 |
| 9. Dashboard Integration | v1.1 | 3/3 | Complete | 2026-03-23 |
| 10. Pipeline and Production Deployment | v1.1 | 2/2 | Complete | 2026-03-24 |
| 11. Design System Foundation | v1.2 | 2/2 | Complete | 2026-03-24 |
| 12. Route Restructure and Navigation | v1.2 | 1/1 | Complete | 2026-03-24 |
| 13. Landing Page | v1.2 | 1/1 | Complete | 2026-03-24 |
| 14. Experiments Redesign | v1.2 | 0/1 | Not started | - |
