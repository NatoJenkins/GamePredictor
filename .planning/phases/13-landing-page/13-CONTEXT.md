# Phase 13: Landing Page - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the landing page content at `/`. Hero section, How It Works explainer, explore CTAs, banner image, and footer. The route structure and layout shell (LandingLayout) already exist from Phase 12. This phase fills in the page content. LAND-06 (standalone full-width layout) is already satisfied.

</domain>

<decisions>
## Implementation Decisions

### Hero section
- Compact height (~60-70vh) so top of How It Works peeks in below, signaling more content
- "NFL Nostradamus" headline in Syne display font
- Subtitle tagline: "20 seasons of play-by-play data. 17 engineered features. One question: who wins Sunday?"
- Validation accuracy stat (62.9%) as a large standalone amber number with small label underneath ("validation accuracy")
- Subtle gradient background (dark-to-slightly-lighter or faint amber radial glow behind the stat)
- Text only in hero -- no image placeholder in this section

### How It Works section
- 2x2 card grid (2 columns on desktop, 1 on mobile)
- Lucide icons for each block (e.g., Database, Layers, Brain, RefreshCw)
- Numbers + one-liner per block: bold stat with a single sentence explanation
  - Data: "20 seasons, ~1.2M plays"
  - Features: "17 game-level features, temporal boundaries"
  - Models: "Pick-em 63.7% + spreads ~10pt MAE"
  - Pipeline: "Automated weekly refresh + human approval gate"
- Borderless cards with subtle background (no Card component border) -- lighter visual weight than dashboard cards

### Banner image
- Full-width banner image between How It Works and CTA section
- Image: `frontend/src/assets/banner.png` -- crystal ball on football field with holographic data visualizations
- Stretches to content width (max-w-4xl)
- Acts as a visual break between the explainer and call-to-action

### CTA section
- Standalone section below the banner image (distinct from How It Works)
- Primary amber "Explore Prediction History" button
- Secondary links to Accuracy and Experiments pages

### Page structure
- Constrained max-w-4xl content width (centered)
- Subtle border lines between major sections (Hero / How It Works / Banner / CTAs / Footer)
- Generous vertical padding within sections

### Footer
- Two-line layout with separator line above
- "Built by Silver Reyes" linking to silverreyes.net
- GitHub link
- Centered alignment

### Responsive
- Hero headline + accuracy stat visible without scrolling on mobile (LAND-07)
- 2x2 grid collapses to single column on mobile

### Claude's Discretion
- Exact gradient treatment (direction, opacity, color stops)
- Specific lucide icon choices for each How It Works block
- Exact spacing/padding values between sections
- Banner image aspect ratio and any overlay treatment
- CTA section heading text (if any)
- Footer link styling

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` LAND-01 through LAND-07 -- Hero content, How It Works blocks, explore CTAs, footer, placeholder images, standalone layout, responsive

### Design system (Phase 11)
- `.planning/phases/11-design-system-foundation/11-CONTEXT.md` -- Amber palette, Syne + IBM Plex Mono, semantic tokens, traffic-light tiers
- `frontend/src/index.css` -- CSS custom properties, @theme inline block, font-display utility class

### Route structure (Phase 12)
- `frontend/src/pages/LandingPage.tsx` -- Current placeholder to be replaced with full landing page content
- `frontend/src/components/layout/LandingLayout.tsx` -- Layout shell (already set up)
- `frontend/src/App.tsx` -- Route tree with LandingLayout branch at `/`

### Assets
- `frontend/src/assets/banner.png` -- Crystal ball stadium banner image (provided by user)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LandingPage.tsx`: Placeholder page exists -- replace content entirely
- `LandingLayout.tsx`: Layout wrapper with `bg-background text-foreground` -- already styled
- `frontend/src/components/ui/button.tsx`: shadcn/ui Button component for CTAs
- `lucide-react`: Already installed and used throughout dashboard -- use for How It Works icons
- `react-router` Link component: Already used in placeholder for navigation

### Established Patterns
- Syne for h1/h2/h3 via `font-family: var(--font-display)` in `@layer base`
- IBM Plex Mono for body via `--font-sans` mapping
- Semantic color tokens: `bg-background`, `text-foreground`, `bg-primary`, `text-primary-foreground`, `text-muted-foreground`, `border-border`
- Amber accent via `--primary` token (oklch 0.767 0.157 71.7)
- `@custom-variant dark` -- app is always in dark mode

### Integration Points
- `LandingPage.tsx` is the only file that needs major changes -- replace placeholder with full content
- `LandingLayout.tsx` may need minor updates if footer is part of the layout vs. part of the page
- Banner image imported from `frontend/src/assets/banner.png`

</code_context>

<specifics>
## Specific Ideas

- Hero stat should be a visually prominent amber number that draws the eye immediately
- How It Works cards should feel lighter than dashboard cards -- borderless with subtle bg, not the full Card component
- Banner image (crystal ball + stadium + holographic data) serves as the emotional centerpiece between the rational explainer and the action-oriented CTAs
- Footer links to silverreyes.net (the user's portfolio site) and GitHub repo

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 13-landing-page*
*Context gathered: 2026-03-24*
