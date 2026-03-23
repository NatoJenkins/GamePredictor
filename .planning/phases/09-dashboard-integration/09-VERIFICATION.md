---
phase: 09-dashboard-integration
verified: 2026-03-23T22:30:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 9: Dashboard Integration Verification Report

**Phase Goal:** Users see spread predictions alongside classifier predictions on every game, with spread-specific performance metrics
**Verified:** 2026-03-23
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each PickCard displays the predicted point spread next to the classifier's win probability | VERIFIED | SpreadLabel.tsx renders `{formatSpread(predictedSpread)} spread` after ConfidenceBadge in PickCard.tsx |
| 2 | A performance summary shows the spread model's MAE on completed games | VERIFIED | SpreadSummaryCards.tsx renders "Spread MAE" card with `spreadModel.mae.toFixed(2)` |
| 3 | After games complete, PickCards show the actual margin and how far off the spread prediction was | VERIFIED | SpreadLabel.tsx renders `Actual {formatSpread(actualSpread)} (off by {error.toFixed(1)})` with color-coded error when `actualSpread != null` |
| 4 | Dashboard displays a comparison of how often the spread model vs the classifier correctly picks the winner | VERIFIED | SpreadSummaryCards.tsx renders "Classifier vs Spread" agreement breakdown with 4 counts; AccuracyPage.tsx calls `computeAgreement()` |

**Score:** 4/4 success criteria verified

### Must-Haves Across All Three Plans

#### Plan 09-01: Data Layer

| Truth | Status | Evidence |
|-------|--------|----------|
| SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo types exist and mirror backend Pydantic schemas | VERIFIED | types.ts lines 68-100: all four interfaces present, field-for-field match to api/schemas.py |
| ModelInfoResponse includes spread_model field typed as SpreadModelInfo \| null | VERIFIED | types.ts line 41: `spread_model: SpreadModelInfo \| null` |
| fetchSpreadPredictions and fetchSpreadHistory API functions exist and call correct backend endpoints | VERIFIED | api.ts lines 67-82: both functions target `/api/predictions/spreads/week/${season}/${week}` and `/api/predictions/spreads/history` |
| useSpreadPredictions hook uses TanStack Query with enabled guard on season/week | VERIFIED | useSpreadPredictions.ts line 9: `enabled: season != null && week != null` |
| useSpreadHistory hook fetches all completed spread predictions for a season | VERIFIED | useSpreadHistory.ts: `useQuery` with `queryFn: () => fetchSpreadHistory(season)` |
| Backend spread history endpoint returns all completed spread predictions for a season | VERIFIED | spreads.py lines 81-154: `get_spread_history` filters `actual_winner IS NOT NULL`, returns `SpreadHistoryResponse` |

#### Plan 09-02: PickCard Spread Display

| Truth | Status | Evidence |
|-------|--------|----------|
| Each PickCard displays the predicted point spread below the confidence percentage | VERIFIED | PickCard.tsx lines 59-62: `<SpreadLabel predictedSpread={spread?.predicted_spread} actualSpread={spread?.actual_spread} />` after ConfidenceBadge |
| Pre-game PickCards show spread in format '+7.5 spread' | VERIFIED | SpreadLabel.tsx line 26: `{formatSpread(predictedSpread)} spread` |
| Post-game PickCards show 'Actual +10 (off by 2.5)' with color-coded error | VERIFIED | SpreadLabel.tsx lines 28-35: conditional render when `actualSpread != null && error != null` |
| Spread error color coding: green (<=3), amber (3-7), red (>7) | VERIFIED | SpreadLabel.tsx lines 11-15: `getSpreadErrorColor` function with exact thresholds |
| When no spread data exists, card looks like v1.0 | VERIFIED | SpreadLabel.tsx line 18: `if (predictedSpread == null) return null` |
| ThisWeekPage fetches spread predictions in parallel with classifier predictions | VERIFIED | ThisWeekPage.tsx line 14: `useSpreadPredictions(data?.season, data?.week)` after `useCurrentPredictions()` |
| History table shows a Spread column with predicted spread per game | VERIFIED | HistoryTable.tsx lines 43, 66-72: conditional Spread column header and cell |

#### Plan 09-03: Accuracy Page Spread Metrics

| Truth | Status | Evidence |
|-------|--------|----------|
| Accuracy page shows Spread MAE card | VERIFIED | SpreadSummaryCards.tsx lines 83-95: "Spread MAE" card with `spreadModel.mae.toFixed(2)` |
| Accuracy page shows Spread Winner Accuracy card with comparison badge | VERIFIED | SpreadSummaryCards.tsx lines 97-113: "Spread Winner Accuracy" card with SpreadComparisonBadge |
| Accuracy page shows Agreement Breakdown card with 4 counts | VERIFIED | SpreadSummaryCards.tsx lines 115-141: "Classifier vs Spread" card with bothCorrect, bothWrong, onlyClassifier, onlySpread |
| Spread section appears BELOW existing classifier SummaryCards | VERIFIED | AccuracyPage.tsx lines 126-192: SummaryCards renders first, spread section at bottom with `mt-8` |
| When spread_model is null, spread section is hidden | VERIFIED | AccuracyPage.tsx line 166: `{modelQuery.data.spread_model && (` |
| Existing classifier SummaryCards remain completely untouched | VERIFIED | git log shows no modifications to SummaryCards.tsx during phase 9 commit range |
| Agreement breakdown only counts games where BOTH classifier and spread have correct !== null | VERIFIED | SpreadSummaryCards.tsx lines 32-34: `if (cp.correct == null) continue` and `if (!sp \|\| sp.correct == null) continue` |

**Score:** 10/10 must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/lib/types.ts` | SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo, SpreadHistoryResponse, updated ModelInfoResponse | VERIFIED | All 4 spread interfaces present; ModelInfoResponse has `spread_model: SpreadModelInfo \| null` |
| `frontend/src/lib/api.ts` | fetchSpreadPredictions, fetchSpreadHistory functions | VERIFIED | Both functions present, call correct endpoints |
| `frontend/src/hooks/useSpreadPredictions.ts` | TanStack Query hook with conditional enabling | VERIFIED | 11 lines, substantive — queryKey, queryFn, enabled guard all present |
| `frontend/src/hooks/useSpreadHistory.ts` | TanStack Query hook for spread history | VERIFIED | 10 lines, substantive — queryKey and queryFn present |
| `api/routes/spreads.py` | GET /api/predictions/spreads/history endpoint | VERIFIED | `get_spread_history` function at lines 81-154, real DB query with `actual_winner IS NOT NULL` filter |
| `api/schemas.py` | SpreadHistoryResponse Pydantic model | VERIFIED | Lines 71-75: `class SpreadHistoryResponse(BaseModel)` with season and predictions fields |
| `frontend/src/components/picks/SpreadLabel.tsx` | Spread display with pre/post-game states and color-coded error | VERIFIED | 38 lines — formatSpread, getSpreadErrorColor, conditional post-game rendering all present |
| `frontend/src/components/picks/PickCard.tsx` | Accepts optional spread prop, renders SpreadLabel | VERIFIED | Lines 4-5: SpreadLabel imported; line 15: `spread?: SpreadPredictionResponse`; lines 59-62: SpreadLabel rendered |
| `frontend/src/components/picks/PicksGrid.tsx` | Accepts spreadByGameId lookup map, passes to PickCard | VERIFIED | Lines 6, 16: `spreadByGameId?: Record<string, SpreadPredictionResponse>` and `spread={spreadByGameId?.[prediction.game_id]}` |
| `frontend/src/pages/ThisWeekPage.tsx` | Parallel spread query fetch and client-side join | VERIFIED | Lines 4, 14-23: useSpreadPredictions import, parallel fetch, useMemo lookup map, spreadByGameId passed to PicksGrid |
| `frontend/src/components/history/HistoryTable.tsx` | Spread column showing predicted spread per game | VERIFIED | Lines 43, 66-72: conditional Spread column header and cell with formatSpread helper |
| `frontend/src/pages/HistoryPage.tsx` | Spread history fetch and pass to HistoryTable | VERIFIED | Lines 4, 25-34: useSpreadHistory import, fetch, useMemo lookup map, spreadByGameId passed to HistoryTable |
| `frontend/src/components/accuracy/SpreadSummaryCards.tsx` | 3-card spread metrics row with computeAgreement | VERIFIED | 143 lines — SpreadSummaryCards, computeAgreement, SpreadComparisonBadge, AgreementData all present |
| `frontend/src/pages/AccuracyPage.tsx` | Spread section rendering conditionally below classifier section | VERIFIED | Lines 3-9, 32, 61-68, 165-192: useSpreadHistory imported and called, agreement useMemo, conditional spread section |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `api.ts` | `/api/predictions/spreads/week/{season}/{week}` | `apiFetch` in fetchSpreadPredictions | WIRED | api.ts line 72: `` `/api/predictions/spreads/week/${season}/${week}` `` |
| `api.ts` | `/api/predictions/spreads/history` | `apiFetch` in fetchSpreadHistory | WIRED | api.ts line 80: `` `/api/predictions/spreads/history${params}` `` |
| `useSpreadPredictions.ts` | `api.ts` | imports fetchSpreadPredictions | WIRED | useSpreadPredictions.ts line 2: `import { fetchSpreadPredictions } from "@/lib/api"` |
| `useSpreadHistory.ts` | `api.ts` | imports fetchSpreadHistory | WIRED | useSpreadHistory.ts line 2: `import { fetchSpreadHistory } from "@/lib/api"` |
| `ThisWeekPage.tsx` | `useSpreadPredictions.ts` | import and call useSpreadPredictions(season, week) | WIRED | ThisWeekPage.tsx lines 4, 14: imported and called with `data?.season, data?.week` |
| `ThisWeekPage.tsx` | `PicksGrid.tsx` | passes spreadByGameId prop | WIRED | ThisWeekPage.tsx line 86: `<PicksGrid predictions={data.predictions} spreadByGameId={spreadByGameId} />` |
| `PicksGrid.tsx` | `PickCard.tsx` | passes spread prop from lookup map | WIRED | PicksGrid.tsx line 16: `spread={spreadByGameId?.[prediction.game_id]}` |
| `PickCard.tsx` | `SpreadLabel.tsx` | renders SpreadLabel with predictedSpread and actualSpread | WIRED | PickCard.tsx lines 59-62: `<SpreadLabel predictedSpread={spread?.predicted_spread} actualSpread={spread?.actual_spread} />` |
| `AccuracyPage.tsx` | `SpreadSummaryCards.tsx` | renders SpreadSummaryCards with spread model info and agreement data | WIRED | AccuracyPage.tsx lines 7-9, 178: imported and rendered with `spreadModel={modelQuery.data.spread_model}` |
| `AccuracyPage.tsx` | `useSpreadHistory.ts` | fetches spread history for agreement computation | WIRED | AccuracyPage.tsx lines 3, 32, 62-67: imported, called, used in computeAgreement |
| `AccuracyPage.tsx` | `useModelInfo.ts` | reads spread_model.mae and spread_model.derived_win_accuracy | WIRED | AccuracyPage.tsx line 166: `modelQuery.data.spread_model &&`; line 179: `spreadModel={modelQuery.data.spread_model}` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DASH-01 | 09-01, 09-02 | Existing PickCards display predicted spread alongside classifier win probability per game | SATISFIED | SpreadLabel in PickCard renders predicted spread; ThisWeekPage wires spread data to PicksGrid |
| DASH-02 | 09-03 | Dashboard shows spread model MAE on a performance summary | SATISFIED | SpreadSummaryCards "Spread MAE" card renders `spreadModel.mae.toFixed(2)` on AccuracyPage |
| DASH-03 | 09-02 | After games complete, PickCards show actual result and spread prediction error | SATISFIED | SpreadLabel renders post-game line "Actual +X.X (off by Y.Y)" with color-coded error when actualSpread != null |
| DASH-04 | 09-01, 09-03 | Dashboard shows how often spread model picks correct winner vs the classifier | SATISFIED | computeAgreement in SpreadSummaryCards joins classifier and spread predictions by game_id, agreement counts rendered in "Classifier vs Spread" card |

All 4 DASH requirements fully covered. No orphaned requirements for Phase 9.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `SpreadLabel.tsx` | 18 | `return null` | Info | Intentional graceful degradation — correct behavior when predictedSpread is null |

No stub implementations, unimplemented handlers, placeholder comments, or console.log-only functions found. The single `return null` in SpreadLabel is the documented graceful degradation behavior per CONTEXT.md requirements.

### Human Verification Required

#### 1. Spread display visual layout

**Test:** Load the dashboard This Week page when spread predictions exist. Examine each PickCard.
**Expected:** Predicted spread appears below the confidence badge in muted text (e.g., "+7.5 spread"). For completed games, a second line shows "Actual +X.X (off by Y.Y)" in green/amber/red depending on error magnitude.
**Why human:** Color-coded visual output and layout cannot be verified programmatically.

#### 2. Graceful degradation when no spread model loaded

**Test:** Load the dashboard when the spread model is not loaded (or before any spread predictions exist).
**Expected:** PickCards render identically to v1.0 (no spread lines), History table has no Spread column, Accuracy page has no "Spread Model" section.
**Why human:** Conditional absence of UI elements requires visual inspection.

#### 3. Spread MAE comparison badge direction

**Test:** Load the Accuracy page when spread model is loaded with completed games.
**Expected:** "Spread Winner Accuracy" card shows a green badge ("Beating +X.X%") if spread accuracy exceeds classifier accuracy, red badge ("Behind X.X%") otherwise.
**Why human:** Badge color depends on runtime data comparison; cannot verify badge direction without live data.

#### 4. Agreement breakdown counts accuracy

**Test:** On the Accuracy page, compare the "Both correct / Both wrong / Only classifier / Only spread" counts against manually counted game outcomes.
**Expected:** Counts match the actual game results for games where both models have a definitive correct/incorrect outcome.
**Why human:** Requires live data to verify the join computation is correct end-to-end.

### Gaps Summary

No gaps. All 10 must-haves verified, all 4 DASH requirements satisfied, all 14 required artifacts exist and are substantively implemented, all 11 key links are wired. The 4 human verification items above are standard visual/behavioral checks that cannot be verified statically — they do not indicate any implementation gap.

---

_Verified: 2026-03-23_
_Verifier: Claude (gsd-verifier)_
