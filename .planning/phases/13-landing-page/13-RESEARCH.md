# Phase 13: Landing Page - Research

**Researched:** 2026-03-24
**Domain:** React landing page with Tailwind CSS v4, design system tokens, responsive layout
**Confidence:** HIGH

## Summary

Phase 13 is a content-only implementation phase. The infrastructure (route structure, layout shell, design tokens, fonts) is fully established by Phases 11 and 12. The work is replacing the placeholder `LandingPage.tsx` with a complete landing page and potentially adding a footer to `LandingLayout.tsx`. No new dependencies are needed -- everything required (lucide-react, react-router Link, shadcn/ui Button, Syne/IBM Plex Mono fonts, semantic color tokens) is already installed and configured.

The primary risk is the banner image: CONTEXT.md references `frontend/src/assets/banner.png` but only `hero.png` exists in assets (and it is a generic Vite starter icon, not a crystal ball image). The implementation should use whatever banner image file exists or handle the missing image gracefully. All other technical aspects are straightforward -- the design system provides all the tokens, the route structure is set, and the component patterns are well-established in the codebase.

**Primary recommendation:** Implement as a single-file replacement of `LandingPage.tsx` with a minor update to `LandingLayout.tsx` for footer placement. No new packages, no new components -- just well-structured JSX using existing design tokens and utilities.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Hero section: ~60-70vh compact height, "NFL Nostradamus" in Syne, subtitle tagline ("20 seasons of play-by-play data. 17 engineered features. One question: who wins Sunday?"), validation accuracy stat 62.9% as large amber number, subtle gradient background, text only (no image)
- How It Works: 2x2 card grid (2 cols desktop, 1 col mobile), Lucide icons, numbers + one-liner per block (Data/Features/Models/Pipeline), borderless cards with subtle background
- Banner image: Full-width between How It Works and CTA, from `frontend/src/assets/banner.png`, stretches to max-w-4xl
- CTA section: Standalone section below banner, primary amber "Explore Prediction History" button, secondary links to Accuracy and Experiments
- Page structure: max-w-4xl content width centered, subtle border lines between sections, generous vertical padding
- Footer: Two-line with separator, "Built by Silver Reyes" linking to silverreyes.net, GitHub link, centered
- Responsive: Hero headline + accuracy stat visible without scrolling on mobile, 2x2 grid collapses to single column

### Claude's Discretion
- Exact gradient treatment (direction, opacity, color stops)
- Specific lucide icon choices for each How It Works block
- Exact spacing/padding values between sections
- Banner image aspect ratio and any overlay treatment
- CTA section heading text (if any)
- Footer link styling

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LAND-01 | Hero section with "NFL Nostradamus" in Syne, subtitle tagline, validation accuracy stat (62.9%) with amber accent | Font system (`font-display` class + `h1` base rule), `text-primary` for amber accent, gradient background via TW4 `bg-linear-to-*` or `bg-radial` utilities |
| LAND-02 | "How It Works" section with 4 scannable blocks (Data, Features, Models, Pipeline) | Lucide icons confirmed available (Database, Layers, Brain, RefreshCw), grid layout with `grid-cols-2` / `grid-cols-1` responsive |
| LAND-03 | Explore CTAs -- primary amber button + secondary links to Accuracy and Experiments | shadcn/ui `Button` component (default variant = amber primary), `Link` from react-router for navigation |
| LAND-04 | Footer with "Built by Silver Reyes" linking to silverreyes.net and GitHub link | External `<a>` tags with `target="_blank"` and `rel="noopener noreferrer"` |
| LAND-05 | Placeholder image containers for hero graphic and optional visuals | CONTEXT.md specifies banner image (`banner.png`) between How It Works and CTAs; `hero.png` in assets is a Vite default, not the intended image -- **banner.png does not yet exist, implementation must handle gracefully** |
| LAND-06 | Standalone full-width layout (no sidebar) | Already satisfied by `LandingLayout.tsx` + route tree in `App.tsx` -- no work needed |
| LAND-07 | Responsive -- hero headline + stat visible without scrolling on mobile | Compact hero height (~60-70vh), responsive typography sizing, mobile-first approach |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| react | 19.2.4 | Component framework | Installed |
| react-router | 7.13.1 | Navigation (Link component) | Installed |
| tailwindcss | 4.2.x (installed 4.2.1, registry 4.2.2) | Utility CSS with TW4 gradient support | Installed |
| lucide-react | 0.577.0 (installed, registry 1.6.0) | Icons for How It Works blocks | Installed |
| shadcn (Button) | 4.0.8 | CTA button component | Installed |
| @fontsource/syne | 5.2.7 | Display font (headings) | Installed |
| @fontsource/ibm-plex-mono | 5.2.7 | Body font | Installed |

### No New Dependencies Required
This phase requires zero new npm packages. Everything is already available.

## Architecture Patterns

### File Structure (Minimal)
```
frontend/src/
├── pages/
│   └── LandingPage.tsx          # REPLACE placeholder with full content
├── components/
│   └── layout/
│       └── LandingLayout.tsx    # MINOR UPDATE: may add footer wrapper
└── assets/
    └── banner.png               # USER-PROVIDED (does not exist yet)
```

### Pattern 1: Single-File Page Component
**What:** The entire landing page lives in `LandingPage.tsx` as a single component. No need for separate sub-components given the page is static content with no data fetching or state.
**When to use:** Static content pages with no shared components.
**Example:**
```typescript
// Source: existing codebase pattern (AccuracyPage.tsx, LandingPage.tsx)
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Database, Layers, Brain, RefreshCw } from "lucide-react";

export function LandingPage() {
  return (
    <div className="mx-auto max-w-4xl px-6">
      {/* Hero Section */}
      <section className="relative flex min-h-[65vh] flex-col items-center justify-center text-center">
        ...
      </section>
      {/* Separator */}
      <div className="border-t border-border" />
      {/* How It Works */}
      <section className="py-16">
        ...
      </section>
      ...
    </div>
  );
}
```

### Pattern 2: Semantic Color Tokens (Established)
**What:** All colors reference CSS custom properties via Tailwind utility classes. No hex/rgb values in JSX.
**Tokens available:**
- `text-primary` / `bg-primary` -- amber accent (oklch 0.767 0.157 71.7)
- `text-foreground` / `bg-background` -- warm text on near-black
- `text-muted-foreground` -- subdued text for labels
- `border-border` -- section dividers
- `bg-card` -- card backgrounds (slightly lighter than background)
- `bg-secondary` -- subtle card background alternative

### Pattern 3: Tailwind v4 Gradient Utilities
**What:** TW4 replaced `bg-gradient-to-*` with `bg-linear-to-*` and added `bg-radial` and arbitrary angle support.
**Key syntax:**
```html
<!-- Linear gradient -->
<div class="bg-linear-to-b from-background via-background to-transparent">

<!-- Radial gradient (for amber glow behind stat) -->
<div class="bg-radial-[at_50%_60%] from-primary/10 to-transparent">

<!-- Arbitrary angle -->
<div class="bg-linear-180 from-background to-card">
```
**Color space:** TW4 defaults to oklab interpolation. Use `/oklch` modifier if needed for the amber palette.

### Pattern 4: Typography Setup
**What:** Syne for display headings, IBM Plex Mono for body. Already configured.
**How it works:**
- `h1`, `h2`, `h3` tags automatically render in Syne via `@layer base` rule in `index.css`
- `font-display` Tailwind utility class available (maps to `--font-display: 'Syne'`)
- `font-sans` maps to IBM Plex Mono (the body font)
- Font weights imported: Syne 400 + 700, IBM Plex Mono 400 + 600

### Pattern 5: Button Component Usage
**What:** shadcn/ui Button with variant system.
**CTA usage:**
```typescript
// Primary amber button (default variant)
<Button asChild size="lg">
  <Link to="/history">Explore Prediction History</Link>
</Button>

// Note: Button uses @base-ui/react primitive, supports `asChild` pattern
// Default variant = bg-primary text-primary-foreground (amber on dark)
```
**Important:** The Button component uses `@base-ui/react/button` as its primitive. The `asChild` pattern (if supported) or wrapping a Link inside Button should be verified. Alternative: style a Link directly with `buttonVariants()`.

### Pattern 6: Link-as-Button Alternative
**What:** Using `buttonVariants` for styled navigation links without the Button component.
```typescript
import { Link } from "react-router";
import { buttonVariants } from "@/components/ui/button";

<Link to="/history" className={buttonVariants({ size: "lg" })}>
  Explore Prediction History
</Link>
```
This is the safer pattern since `@base-ui/react` Button may not support `asChild` the same way Radix does.

### Anti-Patterns to Avoid
- **Hardcoded colors:** Never use hex values, rgb, or oklch directly in className. Always use token classes (`text-primary`, `bg-background`, etc.)
- **Using Card component for How It Works blocks:** CONTEXT.md explicitly says "borderless cards with subtle background -- lighter visual weight than dashboard cards." Use plain `div` elements with `bg-secondary` or `bg-card/50`, not the full `Card` component which has `ring-1 ring-foreground/10`.
- **Complex component hierarchy:** This is a static content page. Don't over-engineer with separate components for each section. A single file with clearly commented sections is the right approach.
- **Importing hero.png as the banner:** `hero.png` is a Vite starter icon, not the intended banner image. The banner image file (`banner.png`) does not exist yet.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CTA button styling | Custom styled `<a>` tag | `buttonVariants()` from shadcn/ui | Consistent with rest of app, hover/focus states handled |
| Section dividers | Custom `<hr>` elements | `<div className="border-t border-border" />` | Uses semantic token, matches separator pattern |
| Responsive grid | Custom media queries in CSS | TW4 `grid-cols-1 md:grid-cols-2` | Standard responsive pattern |
| Icon rendering | SVG inline or custom icon component | `lucide-react` imports | Already used throughout codebase |
| Navigation | `window.location` or custom routing | `react-router` `Link` component | SPA navigation, no page reload |

## Common Pitfalls

### Pitfall 1: Missing Banner Image
**What goes wrong:** CONTEXT.md references `banner.png` but only `hero.png` exists (a Vite starter icon).
**Why it happens:** The user mentioned providing the image but it hasn't been added to the repo yet.
**How to avoid:** Import the banner image with a standard Vite static import. If the file doesn't exist at build time, TypeScript/Vite will throw a compilation error -- this is actually desirable as it signals the missing asset. The planner should note that the user needs to provide `banner.png` before the banner section can render.
**Warning signs:** Build failure on missing import, or rendering a broken image if using a string path.

### Pitfall 2: Hero Height Too Tall on Mobile
**What goes wrong:** Using `min-h-[65vh]` makes the hero section push "How It Works" completely off screen on mobile, violating LAND-07.
**Why it happens:** Mobile viewports are shorter. 65vh on a 667px mobile screen is 433px, which may be fine, but combined with padding and large text could push content down.
**How to avoid:** Use responsive height: `min-h-[50vh] md:min-h-[65vh]` or test that the hero headline + stat fit within viewport on 375px width.
**Warning signs:** "How It Works" not peeking in on mobile.

### Pitfall 3: TW4 Gradient Syntax (Not TW3)
**What goes wrong:** Using `bg-gradient-to-b` (TW3 syntax) instead of `bg-linear-to-b` (TW4 syntax).
**Why it happens:** Most examples online and training data use TW3 syntax.
**How to avoid:** Always use `bg-linear-to-*` for linear gradients and `bg-radial` for radial gradients in TW4.
**Warning signs:** Gradient not rendering, no compilation error (TW4 silently ignores unknown classes).

### Pitfall 4: Button asChild with @base-ui
**What goes wrong:** Using `<Button asChild><Link to="...">` expecting Radix-like composition, but @base-ui/react Button may not support `asChild`.
**Why it happens:** Confusion between Radix UI (older shadcn) and @base-ui/react (newer shadcn).
**How to avoid:** Use `buttonVariants()` to style a Link directly: `<Link className={buttonVariants({ size: "lg" })}>`. This is guaranteed to work.
**Warning signs:** Button renders but Link navigation doesn't work, or renders nested `<button><a>` elements.

### Pitfall 5: Footer Placement
**What goes wrong:** Putting the footer inside `LandingPage.tsx` means it only appears on the landing page. If it should be part of the landing layout, it belongs in `LandingLayout.tsx`.
**Why it happens:** Ambiguity about whether footer is page-level or layout-level.
**How to avoid:** Since LAND-04 specifies it as part of the "home page," and the LandingLayout only serves the landing page, either location works. Putting it in `LandingPage.tsx` keeps things simple and contained. However, if a future page uses LandingLayout, `LandingLayout.tsx` would be more reusable.
**Recommendation:** Put the footer in `LandingPage.tsx` for simplicity -- there is only one page using LandingLayout.

## Code Examples

### Hero Section with Gradient Background
```typescript
// Amber radial glow behind the stat
<section className="relative flex min-h-[50vh] md:min-h-[65vh] flex-col items-center justify-center px-6 text-center">
  {/* Subtle radial glow */}
  <div className="pointer-events-none absolute inset-0 bg-radial-[at_50%_65%] from-primary/8 to-transparent" />

  <h1 className="relative text-4xl md:text-5xl font-bold tracking-tight text-foreground">
    NFL Nostradamus
  </h1>
  <p className="relative mt-4 max-w-xl text-base md:text-lg text-muted-foreground">
    20 seasons of play-by-play data. 17 engineered features. One question: who wins Sunday?
  </p>
  <p className="relative mt-8 text-5xl md:text-7xl font-bold text-primary">
    62.9%
  </p>
  <p className="relative mt-2 text-sm text-muted-foreground uppercase tracking-widest">
    validation accuracy
  </p>
</section>
```

### How It Works 2x2 Grid
```typescript
const blocks = [
  { icon: Database, stat: "20 seasons, ~1.2M plays", label: "Data" },
  { icon: Layers, stat: "17 game-level features", label: "Features" },
  { icon: Brain, stat: "Pick-em 63.7% + spreads ~10pt MAE", label: "Models" },
  { icon: RefreshCw, stat: "Automated weekly refresh", label: "Pipeline" },
];

<section className="py-16">
  <h2 className="mb-10 text-center text-2xl font-semibold text-foreground">
    How It Works
  </h2>
  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
    {blocks.map((block) => (
      <div key={block.label} className="rounded-lg bg-secondary/50 p-6">
        <block.icon className="mb-3 h-6 w-6 text-primary" />
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {block.label}
        </p>
        <p className="mt-1 text-base text-foreground">
          {block.stat}
        </p>
      </div>
    ))}
  </div>
</section>
```

### CTA Section with Button and Links
```typescript
import { Link } from "react-router";
import { buttonVariants } from "@/components/ui/button";

<section className="py-16 text-center">
  <Link
    to="/history"
    className={buttonVariants({ size: "lg", className: "px-8 py-3 text-base" })}
  >
    Explore Prediction History
  </Link>
  <div className="mt-6 flex items-center justify-center gap-6">
    <Link to="/accuracy" className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
      Accuracy
    </Link>
    <Link to="/experiments" className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
      Experiments
    </Link>
  </div>
</section>
```

### Banner Image Import
```typescript
import bannerImg from "@/assets/banner.png";

<section className="py-8">
  <img
    src={bannerImg}
    alt="Crystal ball on football field with holographic data visualizations"
    className="w-full rounded-lg object-cover"
  />
</section>
```

### Footer
```typescript
<footer className="border-t border-border py-8 text-center">
  <p className="text-sm text-muted-foreground">
    Built by{" "}
    <a
      href="https://silverreyes.net"
      target="_blank"
      rel="noopener noreferrer"
      className="text-foreground underline-offset-4 hover:underline"
    >
      Silver Reyes
    </a>
  </p>
  <a
    href="https://github.com/YOUR_REPO"
    target="_blank"
    rel="noopener noreferrer"
    className="mt-2 inline-block text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
  >
    GitHub
  </a>
</footer>
```

### Section Separator Pattern
```typescript
// Consistent section dividers using border-border token
<div className="border-t border-border" />
```

## State of the Art

| Old Approach (TW3) | Current Approach (TW4) | When Changed | Impact |
|---------------------|------------------------|--------------|--------|
| `bg-gradient-to-b` | `bg-linear-to-b` | TW4 (Jan 2025) | Gradient class names changed |
| No radial gradient utility | `bg-radial` / `bg-radial-[at_X_Y]` | TW4 (Jan 2025) | Radial gradients now native |
| sRGB interpolation default | oklab interpolation default | TW4 (Jan 2025) | Smoother gradient transitions |
| `@apply bg-gradient-to-r` | `bg-linear-to-r` inline | TW4 | Inline utilities preferred |

## Open Questions

1. **Banner Image File**
   - What we know: CONTEXT.md references `banner.png`, but only `hero.png` exists (a Vite default icon, not the intended crystal ball image).
   - What's unclear: When/if the user will provide the actual banner image.
   - Recommendation: Implement the banner section with the import path `@/assets/banner.png`. If the file doesn't exist, the build will fail with a clear error. The planner should note this dependency and flag it for the user. Alternatively, the implementation can conditionally render or use a fallback until the image is provided.

2. **GitHub Repository URL**
   - What we know: LAND-04 requires a GitHub link in the footer.
   - What's unclear: The exact GitHub URL for this project.
   - Recommendation: Use a placeholder URL or derive it from git remote config. The planner should include a step to fill in the correct URL.

3. **Button asChild Compatibility**
   - What we know: The Button component uses `@base-ui/react/button` (not Radix).
   - What's unclear: Whether `asChild` prop is supported for Link composition.
   - Recommendation: Use `buttonVariants()` applied directly to `Link` elements. This is guaranteed to work and avoids the question entirely.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None -- no frontend test framework installed |
| Config file | None |
| Quick run command | `cd frontend && npm run build` (type-check + build) |
| Full suite command | `cd frontend && npm run build` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-01 | Hero section renders with headline, subtitle, stat | manual-only | Visual inspection at `/` | N/A |
| LAND-02 | How It Works 4-block grid renders | manual-only | Visual inspection at `/` | N/A |
| LAND-03 | CTA button navigates to `/history`, secondary links work | manual-only | Click test in browser | N/A |
| LAND-04 | Footer links to silverreyes.net and GitHub | manual-only | Click test in browser | N/A |
| LAND-05 | Banner image renders between sections | manual-only | Visual inspection at `/` | N/A |
| LAND-06 | Full-width layout (no sidebar) | manual-only | Already satisfied by Phase 12 | N/A |
| LAND-07 | Responsive -- headline + stat visible on mobile | manual-only | Chrome DevTools responsive mode at 375px | N/A |

**Justification for manual-only:** No frontend test framework (vitest, jest, playwright) is installed. All requirements are visual/layout behaviors that require browser rendering to verify. The build command (`npm run build`) serves as the automated smoke test -- it verifies TypeScript compilation, import resolution, and Vite bundling. Visual requirements must be manually verified.

### Sampling Rate
- **Per task commit:** `cd frontend && npm run build`
- **Per wave merge:** `cd frontend && npm run build` + manual browser inspection
- **Phase gate:** Build green + all 7 requirements visually verified

### Wave 0 Gaps
- None -- no test infrastructure to set up for this phase. Build validation is sufficient for a static content page. The existing `npm run build` catches import errors, type errors, and missing files.

## Sources

### Primary (HIGH confidence)
- Codebase files: `LandingPage.tsx`, `LandingLayout.tsx`, `App.tsx`, `index.css`, `button.tsx`, `card.tsx`, `Sidebar.tsx`, `main.tsx`, `package.json`, `vite.config.ts` -- all read directly
- Tailwind CSS v4 official docs: https://tailwindcss.com/docs/background-image -- gradient syntax verified
- lucide-react icons verified via `require('lucide-react')` -- Database, Layers, Brain, RefreshCw all confirmed available

### Secondary (MEDIUM confidence)
- Tailwind CSS v4 blog post: https://tailwindcss.com/blog/tailwindcss-v4 -- release notes and syntax changes

### Tertiary (LOW confidence)
- None -- all findings verified against codebase or official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified in package.json and node_modules
- Architecture: HIGH -- patterns derived directly from existing codebase
- Pitfalls: HIGH -- identified from codebase analysis (missing banner.png, TW4 syntax differences, @base-ui Button)
- Gradient syntax: HIGH -- verified against official TW4 docs
- Banner image: LOW -- file does not exist yet, user must provide

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable -- no fast-moving dependencies)
