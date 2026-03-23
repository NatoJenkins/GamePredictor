---
phase: 09-dashboard-integration
plan: 02
subsystem: ui
tags: [react, typescript, tailwindcss, spread-predictions, pick-cards]

# Dependency graph
requires:
  - phase: 09-dashboard-integration
    plan: 01
    provides: SpreadPredictionResponse/SpreadWeekResponse/SpreadHistoryResponse types, useSpreadPredictions/useSpreadHistory hooks, fetchSpreadPredictions/fetchSpreadHistory API functions
provides:
  - SpreadLabel component with pre-game/post-game spread display and color-coded error
  - PickCard accepting optional spread prop with graceful v1.0 degradation
  - PicksGrid accepting spreadByGameId lookup map
  - ThisWeekPage parallel spread fetch via useSpreadPredictions
  - HistoryTable conditional Spread column with formatted values
  - HistoryPage spread history fetch via useSpreadHistory
affects: [09-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: [game_id lookup map for client-side join, conditional column rendering, null-safe optional chaining for spread props]

key-files:
  created:
    - frontend/src/components/picks/SpreadLabel.tsx
  modified:
    - frontend/src/components/picks/PickCard.tsx
    - frontend/src/components/picks/PicksGrid.tsx
    - frontend/src/pages/ThisWeekPage.tsx
    - frontend/src/components/history/HistoryTable.tsx
    - frontend/src/pages/HistoryPage.tsx

key-decisions:
  - "SpreadLabel props accept number | null | undefined to match API type convention (actual_spread is null before game completes)"

patterns-established:
  - "Client-side join via game_id lookup map (Record<string, SpreadPredictionResponse>) for spread-to-classifier matching"
  - "Conditional table columns: render column header and cells only when data exists (spreadByGameId && ...)"
  - "Graceful degradation: SpreadLabel returns null when predictedSpread is null, preserving v1.0 card appearance"

requirements-completed: [DASH-01, DASH-03]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 9 Plan 02: PickCard Spread Display Summary

**SpreadLabel component with color-coded error thresholds, wired into PickCard/PicksGrid/ThisWeekPage/HistoryTable/HistoryPage with parallel spread data fetching and client-side game_id join**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T22:00:19Z
- **Completed:** 2026-03-23T22:03:43Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- SpreadLabel component renders pre-game spread ("+7.5 spread") and post-game spread with actual margin and color-coded error ("Actual +10 (off by 2.5)" in green/amber/red)
- PickCard accepts optional spread prop and renders SpreadLabel after ConfidenceBadge, degrades gracefully to v1.0 when no spread data
- ThisWeekPage fetches spread predictions in parallel with classifier via useSpreadPredictions, builds game_id lookup map with useMemo
- HistoryTable shows conditional Spread column between Confidence and Result, hidden when no spread data available
- HistoryPage fetches spread history via useSpreadHistory and passes lookup map to HistoryTable
- Full frontend TypeScript build passes cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SpreadLabel component and update PickCard** - `ae8415e` (feat)
2. **Task 2: Wire spread data into PicksGrid, ThisWeekPage, HistoryTable, HistoryPage** - `75d4868` (feat)

## Files Created/Modified
- `frontend/src/components/picks/SpreadLabel.tsx` - New component: spread prediction display with pre-game/post-game states, formatSpread helper, getSpreadErrorColor with green/amber/red thresholds
- `frontend/src/components/picks/PickCard.tsx` - Added SpreadLabel import, optional spread prop, SpreadLabel rendering after ConfidenceBadge
- `frontend/src/components/picks/PicksGrid.tsx` - Added spreadByGameId prop, passes spread from lookup map to each PickCard
- `frontend/src/pages/ThisWeekPage.tsx` - Added useSpreadPredictions parallel fetch, useMemo for game_id lookup map, passes spreadByGameId to PicksGrid
- `frontend/src/components/history/HistoryTable.tsx` - Added spreadByGameId prop, conditional Spread column header/cell, formatSpread helper
- `frontend/src/pages/HistoryPage.tsx` - Added useSpreadHistory fetch, useMemo for game_id lookup map, passes spreadByGameId to HistoryTable

## Decisions Made
- SpreadLabel props typed as `number | null | undefined` instead of just `number | undefined` to match API type convention where `actual_spread` is `null` (not `undefined`) before game completion

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SpreadLabel props type mismatch with API types**
- **Found during:** Task 2 (build verification)
- **Issue:** `SpreadPredictionResponse.actual_spread` is `number | null` from API, but SpreadLabel accepted `number | undefined` -- TypeScript rejected the `null` assignment
- **Fix:** Changed SpreadLabelProps to accept `number | null | undefined` for both predictedSpread and actualSpread
- **Files modified:** frontend/src/components/picks/SpreadLabel.tsx
- **Verification:** `npm run build` passes cleanly
- **Committed in:** `75d4868` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor type widening to match existing API convention. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Spread data is now visible on both This Week and History pages
- Ready for Plan 09-03 (Accuracy page spread metrics: SpreadSummaryCards with MAE, winner accuracy, agreement breakdown)
- SpreadLabel pattern established for consistent spread display across the UI

## Self-Check: PASSED

All 6 created/modified files verified on disk. Both task commits (ae8415e, 75d4868) verified in git log.

---
*Phase: 09-dashboard-integration*
*Completed: 2026-03-23*
