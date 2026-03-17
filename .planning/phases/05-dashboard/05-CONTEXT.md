# Phase 5: Dashboard - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

React dashboard consuming the 6 FastAPI endpoints from Phase 4 to display weekly picks, season accuracy vs baselines, experiment scoreboard, and prediction history. Four routed pages with a persistent sidebar. No authentication, no data mutation (read-only except model reload which is an admin action not exposed in the dashboard).

</domain>

<decisions>
## Implementation Decisions

### Page layout & navigation
- Multi-page with sidebar layout using React Router
- 4 routes with shareable URLs (important for portfolio use):
  - `/` — This Week's Picks (landing page)
  - `/accuracy` — Season Accuracy
  - `/experiments` — Experiment Scoreboard
  - `/history` — Prediction History
- Always-visible sidebar with icon + label for each nav item (no collapse)
- Sidebar includes model status bar showing current experiment ID and 2023 val accuracy (from GET /model/info)
- Active route highlighted in sidebar

### Tech stack
- React + Vite
- React Router for client-side routing
- Tailwind CSS + shadcn/ui components (tables, cards, badges)
- TanStack Query 5+ for data fetching — handles caching, loading states, error handling out of the box. No raw fetch/axios.

### Claude's Discretion
- Exact shadcn/ui component selection per view
- Color scheme and dark/light mode
- Loading skeleton design
- Error state handling
- Responsive breakpoints
- How weekly picks are displayed within the page (cards vs table)
- How experiments are compared (sortable table, chart, etc.)
- Correct/incorrect visual indicators in history view
- Baseline comparison format in accuracy view

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### API contracts (Phase 4)
- `api/schemas.py` — All Pydantic response models: PredictionResponse, WeekPredictionsResponse, PredictionHistoryResponse, ModelInfoResponse, ExperimentResponse, HealthResponse
- `api/routes/predictions.py` — GET /api/predictions/current, /api/predictions/week/{week}, /api/predictions/history endpoints
- `api/routes/experiments.py` — GET /api/experiments endpoint
- `api/routes/model.py` — GET /api/model/info endpoint
- `api/config.py` — CORS origins (localhost:3000, localhost:5173), confidence tier thresholds

### Phase 4 context
- `.planning/phases/04-prediction-api/04-CONTEXT.md` — API design decisions: confidence tiers, current week detection, history summary object, response schema details

### Project rules
- `CLAUDE.md` — Critical rules and constraints
- `.planning/REQUIREMENTS.md` — DASH-01 through DASH-04: dashboard requirements

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No frontend code exists — greenfield. Phase 5 creates the entire `frontend/` directory
- `api/schemas.py`: TypeScript types can be derived directly from the Pydantic models

### Established Patterns
- API base URL will be `http://localhost:8000` in development (FastAPI default)
- CORS already configured in Phase 4 for `localhost:3000` and `localhost:5173`
- All API routes prefixed with `/api/`
- Confidence tiers computed server-side (`high`/`medium`/`low` in responses)
- History endpoint includes summary object (`{correct, total, accuracy}`) — no client-side aggregation needed

### Integration Points
- GET /api/predictions/current — auto-resolves current week (landing page data)
- GET /api/predictions/week/{week}?season= — week-specific predictions
- GET /api/predictions/history?season=&team= — past predictions with outcomes
- GET /api/model/info — model metadata for sidebar status bar
- GET /api/experiments — experiment list for scoreboard
- GET /api/health — health check

</code_context>

<specifics>
## Specific Ideas

- Shareable URLs per view matter for portfolio use — visitors should be able to link directly to the experiments page or accuracy page
- Model status bar in sidebar gives at-a-glance context on every page without navigating to a specific view
- TanStack Query specifically chosen over raw fetch for its caching, loading states, and error handling — critical for dashboard UX

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-dashboard*
*Context gathered: 2026-03-17*
