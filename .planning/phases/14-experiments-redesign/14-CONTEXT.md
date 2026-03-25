# Phase 14: Experiments Redesign - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the experiments page so column headers align with their data columns and experiment descriptions are fully readable without truncation. This is a targeted fix, not a full redesign — the hybrid layout and visual distinction enhancements are deferred to v1.3.

</domain>

<decisions>
## Implementation Decisions

### Column alignment (EXPR-01)
- Table column headers must sit directly above their corresponding data columns with no visual drift
- Current misalignment between header row and data rows needs diagnosis and fix

### Hypothesis readability (EXPR-02 partial)
- Remove the 60-character truncation on hypothesis text in summary rows
- Let text wrap naturally within the cell — no min-width override needed
- The `truncate max-w-[300px] block` class and `.slice(0, 60)` logic in ExperimentTable.tsx must be removed

### Scope reduction
- Phase 14 is narrowed to EXPR-01 and the readability portion of EXPR-02
- EXPR-03 (hybrid summary+detail layout) deferred to v1.3 backlog
- EXPR-04 (kept experiment visual distinction beyond badge) deferred to v1.3 backlog
- Layman-friendly explanations (rest of EXPR-02) deferred to v1.3 backlog

### Claude's Discretion
- Exact fix for column alignment (may involve table layout, column width adjustments, or structural changes)
- Any minor cleanup needed to make the table render cleanly with longer hypothesis text

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` EXPR-01 and EXPR-02 — Column alignment fix and hypothesis display (only readability portion for this phase)

### Current implementation
- `frontend/src/components/experiments/ExperimentTable.tsx` — Table with 7 columns, Collapsible rows, truncation logic at line 98-101
- `frontend/src/components/experiments/ExperimentDetail.tsx` — Expandable detail panel (unchanged in this phase)
- `frontend/src/lib/types.ts` lines 50-65 — ExperimentResponse type definition

### Design system
- `.planning/phases/11-design-system-foundation/11-CONTEXT.md` — Semantic tokens, amber palette (table must use existing token system)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ExperimentTable.tsx`: shadcn/ui Table with Collapsible — structure stays, just fix alignment and remove truncation
- `ExperimentDetail.tsx`: Expandable detail panel — no changes needed this phase
- shadcn/ui Table components already handle semantic styling

### Established Patterns
- shadcn/ui Table with TableHeader/TableBody/TableRow/TableCell
- Collapsible wrapping TableRow for expand/collapse
- Semantic color tokens (bg-secondary/50, text-muted-foreground) already applied

### Integration Points
- `ExperimentTable.tsx` lines 98-101: Truncation logic (`truncate max-w-[300px] block` + `.slice(0, 60)`) — remove
- `ExperimentTable.tsx` lines 61-77: Column width classes (`w-12`, `w-[100px]`, `w-20`) — may need adjustment for alignment
- Column alignment issue likely related to Collapsible wrapping around TableRow affecting cell layout

</code_context>

<specifics>
## Specific Ideas

- User wants a quick, focused fix — not a full redesign
- Natural text wrapping preferred over enforced column widths
- Current expandable detail panel functionality should remain unchanged

</specifics>

<deferred>
## Deferred Ideas

- EXPR-03: Hybrid summary+detail layout with sortable summary rows — deferred to v1.3 backlog
- EXPR-04: Kept experiment visually distinguishable via accent border/background — deferred to v1.3 backlog
- EXPR-02 (full): Layman-friendly explanations of what each experiment tested — deferred to v1.3 backlog

</deferred>

---

*Phase: 14-experiments-redesign*
*Context gathered: 2026-03-24*
