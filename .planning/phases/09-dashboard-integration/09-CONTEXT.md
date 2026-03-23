# Phase 9: Dashboard Integration - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Users see spread predictions alongside classifier predictions on every game, with spread-specific performance metrics. All spread data integrates into the existing dashboard pages (PickCards on This Week/History, metrics on Accuracy page). No new pages or navigation — spread data appears inline within existing views.

</domain>

<decisions>
## Implementation Decisions

### Spread display on PickCards
- Predicted spread appears **below the confidence percentage**, in smaller muted text
- Format: signed number with label — e.g., "+7.5 spread" or "-3.2 spread" (home team perspective)
- Positive = home team favored, negative = away team favored
- When spread model is not loaded or no spread data exists for a game, **hide the spread row entirely** — card looks exactly like v1.0
- Classifier confidence stays the primary visual element (large text); spread is supplementary

### Post-game card state
- After games complete, **show both the prediction and the result** (card grows slightly taller)
- Pre-game: "+7.5 spread" line only
- Post-game: "+7.5 spread" line PLUS "Actual +10 (off by 2.5)" line below it
- Spread prediction error is **color-coded**: green for close (off by <=3), amber for moderate (3-7), red for far off (>7)
- Existing checkmark/X result indicator stays based on **classifier prediction only** — spread accuracy shown via the error number, not a separate icon
- One result icon per card, no dual indicators

### Performance metrics placement
- **Separate spread section below** existing classifier SummaryCards on the Accuracy page
- Existing 3 classifier cards (Model record, vs Always-Home, vs Better-Record) remain untouched
- New "Spread Model" section with 3 cards:
  1. **Spread MAE** — model's mean absolute error on completed games (e.g., "10.68")
  2. **Spread Winner Accuracy** — how often the spread model correctly picks the winner (e.g., "60.2%")
  3. **Agreement/Disagreement Breakdown** — "Both correct: 142, Both wrong: 38, Only classifier: 15, Only spread: 10"
- When no spread data exists, **hide the entire spread section** — Accuracy page looks exactly like v1.0

### Claude's Discretion
- Data fetching strategy: whether to make two API calls (classifier + spread) and merge client-side, or create a combined endpoint
- TypeScript type definitions for spread prediction data
- Exact Tailwind styling, spacing, and typography for new spread elements
- How the agreement/disagreement breakdown is computed (client-side from both prediction sets, or via a new API endpoint)
- Loading skeleton design for spread sections
- Whether to add spread data to the History page as well (if straightforward)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — DASH-01 through DASH-04 define all Phase 9 requirements
- `.planning/ROADMAP.md` §Phase 9 — Success criteria (4 items)

### Existing dashboard (modify these)
- `frontend/src/components/picks/PickCard.tsx` — Current PickCard component (add spread display + post-game spread results)
- `frontend/src/components/picks/PicksGrid.tsx` — Grid layout for PickCards (may need to pass spread data)
- `frontend/src/components/accuracy/SummaryCards.tsx` — Current classifier summary cards (add spread section below)
- `frontend/src/pages/AccuracyPage.tsx` — Accuracy page (add spread metrics section)
- `frontend/src/pages/ThisWeekPage.tsx` — This Week page (needs to fetch spread data)

### Types and API layer
- `frontend/src/lib/types.ts` — TypeScript interfaces (add SpreadPredictionResponse, update ModelInfoResponse)
- `frontend/src/lib/api.ts` — API fetch functions (add fetchSpreadPredictions)
- `frontend/src/hooks/useModelInfo.ts` — Model info hook (spread_model data already in API response)
- `frontend/src/hooks/useCurrentPredictions.ts` — Current predictions hook (need parallel spread fetch)

### Backend API (read-only, already built in Phase 8)
- `api/routes/spreads.py` — GET /api/predictions/spreads/week/{season}/{week} endpoint
- `api/schemas.py` — SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo, ModelInfoResponse schemas
- `api/routes/model.py` — GET /api/model/info now includes spread_model nested object

### Phase 8 context
- `.planning/phases/08-database-and-api-integration/08-CONTEXT.md` — API design decisions, spread table schema, graceful degradation approach

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PickCard.tsx`: Current card structure with tierBorderColors, ResultIndicator, ConfidenceBadge — spread elements slot in below confidence
- `SummaryCards.tsx`: ComparisonBadge component (green/red badge for beating/behind baselines) — reusable for spread comparison
- `ResultIndicator.tsx`: Checkmark/X/Pending indicator — stays classifier-only
- `ConfidenceBadge.tsx`: Tier badge component — stays classifier-only
- `ErrorState.tsx`: Reusable error/empty state component
- `Skeleton` from shadcn/ui: Loading skeleton component used across all pages
- `Card`, `CardContent` from shadcn/ui: Card component used by both PickCard and SummaryCards
- `Badge` from shadcn/ui: Badge component used by SummaryCards for comparison

### Established Patterns
- TanStack Query (react-query) for data fetching with `useQuery` hooks
- API functions in `lib/api.ts` using `apiFetch<T>()` generic helper
- TypeScript interfaces in `lib/types.ts` matching backend Pydantic schemas
- Tailwind CSS with shadcn/ui components (Card, Badge, Table, Skeleton)
- Dark theme with zinc color palette, muted-foreground for secondary text
- `text-[28px] font-semibold leading-tight` pattern for large stat numbers
- `text-sm text-muted-foreground` pattern for secondary/label text

### Integration Points
- `PickCard` receives `PredictionResponse` — needs spread data joined to it (or passed separately)
- `AccuracyPage` calls `usePredictionHistory()` + `useModelInfo()` — spread metrics can come from `useModelInfo()` (MAE already in response) plus spread prediction history for the agreement breakdown
- `ThisWeekPage` calls `useCurrentPredictions()` — needs parallel spread data fetch for the same season/week

</code_context>

<specifics>
## Specific Ideas

- Spread section on Accuracy page follows the same 3-card layout pattern as classifier (flex row, gap-6, flex-1 per card)
- Color-coded spread error thresholds: green <=3, amber 3-7, red >7 (approximate NFL-relevant ranges — a field goal vs a touchdown)
- Agreement/disagreement breakdown provides genuine insight into when models diverge, not just who wins more

</specifics>

<deferred>
## Deferred Ideas

- Spread-specific history endpoint (deferred from Phase 8) — evaluate during planning if needed for the agreement breakdown
- Combined classifier+spread predictions endpoint (deferred from Phase 8) — evaluate during planning

</deferred>

---

*Phase: 09-dashboard-integration*
*Context gathered: 2026-03-23*
