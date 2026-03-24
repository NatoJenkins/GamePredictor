# Phase 11: Design System Foundation - Research

**Researched:** 2026-03-24
**Domain:** CSS theming, typography, design token migration (Tailwind v4 + shadcn/ui)
**Confidence:** HIGH

## Summary

Phase 11 migrates the NFL Predictor dashboard from its current generic dark theme (Inter + JetBrains Mono, zinc/blue Tailwind palette) to the silverreyes.net visual identity (Syne + IBM Plex Mono, warm amber palette). The existing codebase already uses the correct architecture for this migration: oklch-based CSS custom properties in `:root`/`.dark` blocks with a Tailwind v4 `@theme inline` mapping. The work is primarily about changing **values**, not restructuring.

The silverreyes.net live site was successfully inspected and all design token values were extracted (see Verified Palette below). The site uses hex-based CSS custom properties in `:root` with a `[data-theme=light]` override. Since the Nostradamus dashboard is dark-only for v1.2, only the `:root` (dark) values need translation to oklch for the shadcn/ui token system.

**Primary recommendation:** Replace CSS custom property values in `index.css` to match the silverreyes.net palette (converted to oklch), swap font imports from Google CDN to @fontsource packages, add custom confidence tier tokens (green/amber/red), then systematically replace ~25 hardcoded Tailwind color classes with semantic token references.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Traffic-light color scheme for confidence tiers: green (high), amber (medium), desaturated red (low)
- Replaces current blue-based confidence tiers
- PickCard left border uses the 3px left border pattern (existing pattern preserved), with colors swapped to green/amber/red
- ConfidenceBadge text and background also use the traffic-light colors (badge matches border color) with subtle bg tint per tier
- Consistent signal: card border and badge reinforce the same tier color

### Claude's Discretion
- Exact oklch values for the silverreyes.net palette tokens (background, card, accent, muted, border, etc.) -- verify against live site
- Syne + IBM Plex Mono font setup and weight selection
- Which heading levels use Syne vs which elements use IBM Plex Mono
- Strategy for replacing ~25 hardcoded zinc-*/blue-* Tailwind classes with semantic tokens
- shadcn/ui @theme inline block remapping approach
- Font hosting method (@fontsource or self-hosted)
- Exact green, amber, and desaturated red oklch values for confidence tiers

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DSGN-01 | Dashboard uses silverreyes.net color palette (amber accent, near-black background, warm text tones) via CSS custom properties | Verified palette section provides exact oklch values extracted from live site; Architecture Patterns section maps them to shadcn token names |
| DSGN-02 | Dashboard uses Syne (display/headings) and IBM Plex Mono (body/code) fonts, self-hosted via @fontsource | Standard Stack section confirms @fontsource packages + versions; Font Architecture section details import strategy and weight selection |
| DSGN-03 | All hardcoded Tailwind color classes replaced with semantic theme tokens | Complete Hardcoded Color Audit section catalogs every instance across 12 files with replacement strategy |
| DSGN-04 | shadcn/ui component tokens (@theme inline block) remapped to silverreyes.net-aligned values | Architecture Patterns section provides exact @theme inline remapping; existing structure is preserved (values change, not shape) |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tailwindcss | 4.2.1 | Utility-first CSS framework | Already installed; v4 native CSS variable theming via @theme inline |
| shadcn (CLI + components) | 4.0.8 | Component primitives | Already installed; 9 components use semantic token system |
| @fontsource/syne | 5.2.7 | Syne display font (self-hosted) | Eliminates Google Fonts CDN dependency; supports weights 400-800 |
| @fontsource/ibm-plex-mono | 5.2.7 | IBM Plex Mono body font (self-hosted) | Eliminates Google Fonts CDN dependency; supports weights 300-600 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fontsource-variable/syne | 5.2.7 | Variable font version of Syne | Optional: smaller bundle, single file for all weights |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @fontsource packages | Google Fonts CDN | CDN has FOUT risk, third-party dependency; @fontsource bundles with app |
| @fontsource-variable/syne | @fontsource/syne (static) | Variable font is smaller total bundle but has slightly less browser support; static is safer |
| oklch colors | hex colors in CSS vars | oklch is already in use by shadcn/ui setup; consistent with existing pattern |

**Recommendation:** Use static @fontsource packages (not variable) for maximum compatibility. The silverreyes.net site itself uses fonts.bunny.net CDN, but DSGN-02 explicitly requires self-hosted via @fontsource.

**Installation:**
```bash
cd frontend && npm install @fontsource/syne @fontsource/ibm-plex-mono
```

## Architecture Patterns

### Verified silverreyes.net Palette (from live site)

Source: Direct extraction from `https://silverreyes.net` CSS on 2026-03-24.

| Token | Hex Value | oklch Equivalent | Purpose |
|-------|-----------|------------------|---------|
| --color-bg | #080807 | oklch(0.134 0.003 106.7) | Page background |
| --color-surface | #111110 | oklch(0.177 0.002 106.6) | Card/panel background |
| --color-surface-2 | #1a1917 | oklch(0.214 0.004 84.6) | Elevated surface / hover |
| --color-border | #252420 | oklch(0.260 0.007 95.3) | Borders, dividers |
| --color-accent | #f0a020 | oklch(0.767 0.157 71.7) | Primary amber accent |
| --color-accent-dim | rgba(240,160,32,0.12) | oklch(0.767 0.157 71.7 / 12%) | Accent background tint |
| --color-accent-glow | rgba(240,160,32,0.06) | oklch(0.767 0.157 71.7 / 6%) | Subtle accent hover |
| --color-text | #ddd8ce | oklch(0.883 0.015 84.6) | Primary text |
| --color-text-muted | #7a7468 | oklch(0.561 0.019 84.6) | Secondary/muted text |
| --color-text-faint | #3e3c38 | oklch(0.357 0.007 84.6) | Faint/disabled text |

**Font definitions from silverreyes.net:**
```
--font-display: "Syne", sans-serif
--font-mono: "IBM Plex Mono", monospace
```

**Font weights used on silverreyes.net:** Syne 400,500,600,700,800 | IBM Plex Mono 300,400,500,600

### Token Mapping: silverreyes.net to shadcn/ui

The `.dark` block in `index.css` maps silverreyes.net tokens to shadcn semantic names:

| shadcn Token | Current Value | New Value (oklch) | Maps To |
|-------------|---------------|-------------------|---------|
| --background | oklch(0.145 0 0) | oklch(0.134 0.003 106.7) | --color-bg |
| --foreground | oklch(0.985 0 0) | oklch(0.883 0.015 84.6) | --color-text |
| --card | oklch(0.205 0 0) | oklch(0.177 0.002 106.6) | --color-surface |
| --card-foreground | oklch(0.985 0 0) | oklch(0.883 0.015 84.6) | --color-text |
| --popover | oklch(0.205 0 0) | oklch(0.177 0.002 106.6) | --color-surface |
| --popover-foreground | oklch(0.985 0 0) | oklch(0.883 0.015 84.6) | --color-text |
| --primary | oklch(0.922 0 0) | oklch(0.767 0.157 71.7) | --color-accent |
| --primary-foreground | oklch(0.205 0 0) | oklch(0.134 0.003 106.7) | --color-bg (contrast) |
| --secondary | oklch(0.269 0 0) | oklch(0.214 0.004 84.6) | --color-surface-2 |
| --secondary-foreground | oklch(0.985 0 0) | oklch(0.883 0.015 84.6) | --color-text |
| --muted | oklch(0.269 0 0) | oklch(0.214 0.004 84.6) | --color-surface-2 |
| --muted-foreground | oklch(0.708 0 0) | oklch(0.561 0.019 84.6) | --color-text-muted |
| --accent | oklch(0.269 0 0) | oklch(0.767 0.157 71.7 / 12%) | --color-accent-dim |
| --accent-foreground | oklch(0.985 0 0) | oklch(0.767 0.157 71.7) | --color-accent |
| --destructive | oklch(0.704 0.191 22.216) | oklch(0.704 0.191 22.216) | Keep existing |
| --border | oklch(1 0 0 / 10%) | oklch(0.260 0.007 95.3) | --color-border |
| --input | oklch(1 0 0 / 15%) | oklch(0.260 0.007 95.3) | --color-border |
| --ring | oklch(0.556 0 0) | oklch(0.767 0.157 71.7) | --color-accent |

Additionally, the sidebar tokens should mirror the main tokens since the sidebar is part of the same dark theme:

| Sidebar Token | New Value | Maps To |
|--------------|-----------|---------|
| --sidebar | oklch(0.177 0.002 106.6) | --color-surface |
| --sidebar-foreground | oklch(0.883 0.015 84.6) | --color-text |
| --sidebar-primary | oklch(0.767 0.157 71.7) | --color-accent |
| --sidebar-primary-foreground | oklch(0.883 0.015 84.6) | --color-text |
| --sidebar-accent | oklch(0.767 0.157 71.7 / 12%) | --color-accent-dim |
| --sidebar-accent-foreground | oklch(0.767 0.157 71.7) | --color-accent |
| --sidebar-border | oklch(0.260 0.007 95.3) | --color-border |
| --sidebar-ring | oklch(0.767 0.157 71.7) | --color-accent |

### Confidence Tier Colors (Traffic-Light)

Custom CSS custom properties for the tier system. These are NOT part of the silverreyes.net palette -- they are application-specific semantic colors.

```css
/* Add to .dark block */
--tier-high: oklch(0.72 0.17 142);      /* Green - confident */
--tier-high-bg: oklch(0.72 0.17 142 / 15%);
--tier-medium: oklch(0.767 0.157 71.7);  /* Amber - matches accent */
--tier-medium-bg: oklch(0.767 0.157 71.7 / 15%);
--tier-low: oklch(0.65 0.15 25);         /* Desaturated red */
--tier-low-bg: oklch(0.65 0.15 25 / 15%);

/* Semantic status colors (used beyond tiers) */
--status-success: oklch(0.72 0.17 142);
--status-error: oklch(0.65 0.15 25);
--status-warning: oklch(0.767 0.157 71.7);
```

These need to be registered in the `@theme inline` block so Tailwind generates utilities:
```css
@theme inline {
  --color-tier-high: var(--tier-high);
  --color-tier-high-bg: var(--tier-high-bg);
  --color-tier-medium: var(--tier-medium);
  --color-tier-medium-bg: var(--tier-medium-bg);
  --color-tier-low: var(--tier-low);
  --color-tier-low-bg: var(--tier-low-bg);
  --color-status-success: var(--status-success);
  --color-status-error: var(--status-error);
  --color-status-warning: var(--status-warning);
}
```

### Font Architecture

**Import strategy (in `index.css`, replacing Google Fonts CDN):**
```css
/* Remove: @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400&display=swap'); */

/* In main.tsx or index.css (CSS @import): */
@import "@fontsource/syne/400.css";
@import "@fontsource/syne/700.css";
@import "@fontsource/syne/800.css";
@import "@fontsource/ibm-plex-mono/300.css";
@import "@fontsource/ibm-plex-mono/400.css";
@import "@fontsource/ibm-plex-mono/500.css";
@import "@fontsource/ibm-plex-mono/600.css";
```

**Weight selection rationale:**
- Syne 400: Normal body weight if ever needed as fallback
- Syne 700: Bold headings
- Syne 800: Extra-bold display (hero text, matching silverreyes.net hero)
- IBM Plex Mono 300: Light weight for subtle elements
- IBM Plex Mono 400: Default body text
- IBM Plex Mono 500: Medium emphasis
- IBM Plex Mono 600: Semi-bold labels/emphasis

**Typography assignment (matching silverreyes.net patterns):**
- `--font-display: "Syne", sans-serif` -- h1, h2, h3 headings, page titles, "NFL Predictor" brand text
- `--font-mono: "IBM Plex Mono", monospace` -- body text, labels, code, data values, navigation items, badges

**Update `@theme inline` block:**
```css
@theme inline {
  --font-sans: 'IBM Plex Mono', ui-monospace, monospace;
  --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
  --font-display: 'Syne', sans-serif;
  /* ... color tokens ... */
}
```

**Update `body` rule:**
```css
body {
  margin: 0;
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Note:** silverreyes.net uses IBM Plex Mono as its PRIMARY body font (not Syne). Syne is only for display/headings. The `--font-sans` in the theme should map to IBM Plex Mono since that is the default body font. A custom `font-display` utility is needed for headings.

### Recommended File Structure

No new files needed beyond `index.css` modifications. The migration changes values in existing structure:

```
frontend/src/
  index.css                    # PRIMARY: All token values change here
  main.tsx                     # Add @fontsource imports
  components/
    layout/
      Sidebar.tsx              # Replace zinc-*/blue-* classes
    shared/
      ConfidenceBadge.tsx      # Traffic-light tier colors
      ResultIndicator.tsx       # Semantic status-success/error
      ErrorState.tsx            # Semantic status-error
    picks/
      PickCard.tsx             # Traffic-light border colors
      SpreadLabel.tsx          # Semantic status colors for spread error
    accuracy/
      SummaryCards.tsx          # Semantic status-success/error badges
      SpreadSummaryCards.tsx    # Semantic status-success/error badges
    experiments/
      ExperimentTable.tsx       # Replace zinc-*, semantic status badges
      ExperimentDetail.tsx      # Replace zinc-800, blue-500 progress bars
    history/
      HistoryTable.tsx          # Replace hover:bg-zinc-800/50
      HistoryLegend.tsx         # Replace zinc-800/900, semantic status colors
  pages/
    ThisWeekPage.tsx            # Replace text-blue-400 link
    AccuracyPage.tsx            # Replace hover:bg-zinc-800/50
```

### Anti-Patterns to Avoid
- **Adding a separate tokens.css file:** Keep all tokens in `index.css` where shadcn already manages them. Splitting creates sync issues.
- **Using hex values in CSS custom properties:** The existing system uses oklch. Converting to hex would break consistency with shadcn's generated utilities.
- **Importing all @fontsource weights:** Only import weights actually used. Each weight is a separate font file (~20-50KB).
- **Replacing semantic Tailwind classes:** Classes like `text-muted-foreground`, `bg-background`, `bg-card` are ALREADY semantic tokens. Only hardcoded color classes (zinc-800, blue-500, etc.) need replacement.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font hosting | Manual @font-face declarations | @fontsource packages | Handles formats, unicode-range, preload hints |
| Color palette conversion | Manual hex-to-oklch conversion for each usage | CSS custom properties with oklch values in :root | Single source of truth; Tailwind generates utilities from @theme inline |
| Semantic color system | New color utility classes | Tailwind v4 @theme inline + CSS custom properties | Already the established pattern in this codebase |
| Dark mode toggling | JavaScript theme switching | `class="dark"` on html + `.dark` CSS block | Already implemented; v1.2 is dark-only |

**Key insight:** The existing architecture is already correct. This phase changes VALUES in the token system, not the architecture itself. The `@theme inline` block, the `.dark` CSS block, and the shadcn component token consumption are all in place.

## Common Pitfalls

### Pitfall 1: Invisible Text After Token Swap
**What goes wrong:** After changing `--primary` from a neutral gray to amber, any text using `text-primary` becomes amber instead of the expected light text color. Similarly, `--primary-foreground` text on amber backgrounds may lack contrast.
**Why it happens:** shadcn components use `primary`/`primary-foreground` as a pair. When `--primary` becomes the accent color, the foreground must be a color that contrasts against amber (dark background, not light text).
**How to avoid:** Always test the full primary/primary-foreground pair. `--primary-foreground` should be the near-black background color (`oklch(0.134 0.003 106.7)`) since primary is now the bright amber.
**Warning signs:** Buttons with text that blends into the button background.

### Pitfall 2: Missing Tailwind Utility Generation for Custom Tokens
**What goes wrong:** Adding `--tier-high` as a CSS custom property but forgetting to register it in `@theme inline` means `text-tier-high` and `bg-tier-high` Tailwind classes don't exist.
**Why it happens:** Tailwind v4 only generates utility classes for tokens registered in `@theme inline` (prefixed with `--color-`).
**How to avoid:** Every new semantic color needs BOTH a CSS custom property in `.dark {}` AND a corresponding `--color-*` entry in `@theme inline`.
**Warning signs:** Tailwind classes appear in code but have no effect; no matching CSS generated.

### Pitfall 3: Stale Google Fonts CDN Reference
**What goes wrong:** The `@import url('https://fonts.googleapis.com/...')` line remains in `index.css` alongside @fontsource imports, causing double font loading and potential FOUT.
**Why it happens:** Easy to add new fonts without removing old ones.
**How to avoid:** Delete the Google Fonts `@import` line when adding @fontsource imports. Verify no network requests to fonts.googleapis.com in dev tools.
**Warning signs:** Two font requests for similar families in the Network tab.

### Pitfall 4: Hardcoded Colors in Status Indicators
**What goes wrong:** Replacing `text-green-500` in ResultIndicator with `text-status-success` but forgetting to handle the green/amber/red used in HistoryLegend descriptive text, or the spread error color function.
**Why it happens:** Status colors (green/red for correct/wrong, green/amber/red for spread accuracy) appear in many components with slightly different patterns.
**How to avoid:** Use the complete audit below. Replace ALL instances, including conditional string returns in utility functions like `getSpreadErrorColor()`.
**Warning signs:** Some components show old blue/default colors while others show the new palette.

### Pitfall 5: oklch Alpha Syntax
**What goes wrong:** Using `oklch(0.767 0.157 71.7 / 0.12)` when it should be `oklch(0.767 0.157 71.7 / 12%)`. Or using the Tailwind opacity modifier syntax `bg-primary/20` which doesn't compose the same way with oklch alpha.
**Why it happens:** oklch alpha syntax differs from rgb/hsl. Tailwind's opacity modifiers work differently with oklch.
**How to avoid:** For token-level opacity, bake it into the CSS custom property value (e.g., `--tier-high-bg: oklch(0.72 0.17 142 / 15%)`). For one-off opacity, Tailwind's `/` modifier still works with `@theme inline` registered colors.
**Warning signs:** Colors appear fully opaque when they should be translucent, or completely invisible.

## Code Examples

### Example 1: Updated `.dark` block in `index.css`
```css
/* Source: silverreyes.net live site CSS, extracted 2026-03-24 */
.dark {
  --background: oklch(0.134 0.003 106.7);
  --foreground: oklch(0.883 0.015 84.6);
  --card: oklch(0.177 0.002 106.6);
  --card-foreground: oklch(0.883 0.015 84.6);
  --popover: oklch(0.177 0.002 106.6);
  --popover-foreground: oklch(0.883 0.015 84.6);
  --primary: oklch(0.767 0.157 71.7);
  --primary-foreground: oklch(0.134 0.003 106.7);
  --secondary: oklch(0.214 0.004 84.6);
  --secondary-foreground: oklch(0.883 0.015 84.6);
  --muted: oklch(0.214 0.004 84.6);
  --muted-foreground: oklch(0.561 0.019 84.6);
  --accent: oklch(0.767 0.157 71.7 / 12%);
  --accent-foreground: oklch(0.767 0.157 71.7);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(0.260 0.007 95.3);
  --input: oklch(0.260 0.007 95.3);
  --ring: oklch(0.767 0.157 71.7);

  /* Confidence tier tokens */
  --tier-high: oklch(0.72 0.17 142);
  --tier-high-bg: oklch(0.72 0.17 142 / 15%);
  --tier-medium: oklch(0.767 0.157 71.7);
  --tier-medium-bg: oklch(0.767 0.157 71.7 / 15%);
  --tier-low: oklch(0.65 0.15 25);
  --tier-low-bg: oklch(0.65 0.15 25 / 15%);

  /* Semantic status colors */
  --status-success: oklch(0.72 0.17 142);
  --status-error: oklch(0.65 0.15 25);
  --status-warning: oklch(0.767 0.157 71.7);
}
```

### Example 2: Updated ConfidenceBadge with semantic tokens
```typescript
// Before:
const tierStyles: Record<string, string> = {
  high: "bg-blue-500/20 text-blue-400",
  medium: "bg-amber-500/20 text-amber-400",
  low: "bg-zinc-500/20 text-zinc-400",
};

// After:
const tierStyles: Record<string, string> = {
  high: "bg-tier-high-bg text-tier-high",
  medium: "bg-tier-medium-bg text-tier-medium",
  low: "bg-tier-low-bg text-tier-low",
};
```

### Example 3: Updated Sidebar replacing hardcoded classes
```typescript
// Before:
<aside className="... border-zinc-800 bg-zinc-900 ...">
  <Separator className="bg-zinc-800" />
  <Card className="border-zinc-800 bg-zinc-900/50">
  // Active nav: "bg-blue-500/10 text-blue-400"
  // Inactive hover: "hover:bg-zinc-800"

// After:
<aside className="... border-border bg-card ...">
  <Separator className="bg-border" />
  <Card className="border-border bg-background/50">
  // Active nav: "bg-accent text-accent-foreground"
  // Inactive hover: "hover:bg-secondary"
```

### Example 4: Font imports in index.css
```css
/* Remove Google Fonts CDN import */
/* Add @fontsource imports (after npm install) */
@import "@fontsource/syne/400.css";
@import "@fontsource/syne/700.css";
@import "@fontsource/syne/800.css";
@import "@fontsource/ibm-plex-mono/300.css";
@import "@fontsource/ibm-plex-mono/400.css";
@import "@fontsource/ibm-plex-mono/500.css";
@import "@fontsource/ibm-plex-mono/600.css";
```

## Complete Hardcoded Color Audit

Every hardcoded Tailwind color class that must be replaced, organized by file:

### Sidebar.tsx (largest migration target -- 10 instances)
| Line | Current Class | Replacement | Context |
|------|--------------|-------------|---------|
| 23 | `bg-zinc-800` | `bg-border` | Separator |
| 25 | `border-zinc-800 bg-zinc-900/50` | `border-border bg-background/50` | Model status card |
| 53 | `border-zinc-800 bg-zinc-900` | `border-border bg-card` | Desktop sidebar |
| 70 | `bg-blue-500/10 text-blue-400` | `bg-accent text-accent-foreground` | Active nav (desktop) |
| 71 | `hover:bg-zinc-800` | `hover:bg-secondary` | Inactive nav hover (desktop) |
| 85 | `border-zinc-800 bg-zinc-900` | `border-border bg-card` | Mobile nav |
| 98 | `bg-blue-500/10 text-blue-400` | `bg-accent text-accent-foreground` | Active nav (mobile) |
| 99 | `hover:bg-zinc-800` | `hover:bg-secondary` | Inactive nav hover (mobile) |

### ConfidenceBadge.tsx (3 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 5 | `bg-blue-500/20 text-blue-400` | `bg-tier-high-bg text-tier-high` |
| 6 | `bg-amber-500/20 text-amber-400` | `bg-tier-medium-bg text-tier-medium` |
| 7 | `bg-zinc-500/20 text-zinc-400` | `bg-tier-low-bg text-tier-low` |

### PickCard.tsx (3 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 8 | `border-blue-500` | `border-tier-high` |
| 9 | `border-amber-500` | `border-tier-medium` |
| 10 | `border-zinc-500` | `border-tier-low` |

### ExperimentDetail.tsx (2 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 58 | `bg-zinc-800` | `bg-secondary` |
| 60 | `bg-blue-500` | `bg-primary` |

### ExperimentTable.tsx (4 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 91 | `hover:bg-zinc-800/50` | `hover:bg-secondary/50` |
| 116 | `bg-green-500/20 text-green-400` | `bg-status-success/15 text-status-success` |
| 120 | `bg-red-500/20 text-red-400` | `bg-status-error/15 text-status-error` |
| 127 | `bg-zinc-900/50` | `bg-background/50` |

### HistoryLegend.tsx (1 structural + content refs)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 17 | `border-zinc-800 bg-zinc-900/50` | `border-border bg-background/50` |

Note: The text-green-400, text-amber-400, text-red-400 in HistoryLegend lines 25-26, 43-51, 58-59 are descriptive legend content. Replace with `text-status-success`, `text-status-warning`, `text-status-error` respectively.

### HistoryTable.tsx (1 instance)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 79 | `hover:bg-zinc-800/50` | `hover:bg-secondary/50` |

### AccuracyPage.tsx (1 instance)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 227 | `hover:bg-zinc-800/50` | `hover:bg-secondary/50` |

### ThisWeekPage.tsx (1 instance)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 69 | `text-blue-400` | `text-accent-foreground` |

### ResultIndicator.tsx (3 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 9 | `text-green-500` | `text-status-success` |
| 13 | `text-red-500` | `text-status-error` |
| 18 | `text-zinc-500` | `text-muted-foreground` |

### ErrorState.tsx (1 instance)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 21 | `text-red-500` | `text-destructive` |

### SummaryCards.tsx (2 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 23 | `bg-green-500/20 text-green-400` | `bg-status-success/15 text-status-success` |
| 30 | `bg-red-500/20 text-red-400` | `bg-status-error/15 text-status-error` |

### SpreadSummaryCards.tsx (2 instances)
| Line | Current Class | Replacement |
|------|--------------|-------------|
| 57 | `bg-green-500/20 text-green-400` | `bg-status-success/15 text-status-success` |
| 64 | `bg-red-500/20 text-red-400` | `bg-status-error/15 text-status-error` |

### SpreadLabel.tsx (3 instances -- in utility function)
| Line | Current Return | Replacement |
|------|---------------|-------------|
| 12 | `text-green-400` | `text-status-success` |
| 13 | `text-amber-400` | `text-status-warning` |
| 14 | `text-red-400` | `text-status-error` |

### HistoryTable.tsx getSpreadErrorColor (3 instances -- in utility function)
| Line | Current Return | Replacement |
|------|---------------|-------------|
| 24 | `text-green-400` | `text-status-success` |
| 25 | `text-amber-400` | `text-status-warning` |
| 26 | `text-red-400` | `text-status-error` |

**Total: ~36 hardcoded color class instances across 14 files**

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HSL colors in CSS vars | oklch colors in CSS vars | shadcn v4 (Feb 2025) | Better perceptual uniformity; already in use |
| tailwind.config.js theme | @theme inline in CSS | Tailwind v4 (Jan 2025) | No config file needed; tokens live in CSS |
| Google Fonts CDN | @fontsource self-hosted | Best practice 2024+ | No FOUT, no third-party dependency, better Core Web Vitals |
| @layer base for variable scoping | @theme inline for Tailwind registration | Tailwind v4 | @theme inline tells Tailwind to generate utilities |

**Deprecated/outdated:**
- tailwind.config.js: Not used in this project (Tailwind v4 + @theme inline)
- HSL color format: shadcn migrated to oklch in v4
- `@apply` for component styles: Still works but `@theme inline` is the registration mechanism

## Open Questions

1. **Exact oklch hue for "desaturated red" tier-low**
   - What we know: User wants a "desaturated red" that is less alarming than pure red. The proposed `oklch(0.65 0.15 25)` is a warm, muted red.
   - What's unclear: Whether the exact chroma (0.15) provides enough visual distinction from the amber tier.
   - Recommendation: Implement the proposed value and visually verify. Adjust chroma/lightness during implementation if the green-amber-red progression doesn't read clearly.

2. **Whether `:root` (light mode) values need updating**
   - What we know: The app is dark-only (class="dark" on html). The `:root` block defines light mode values that are never used.
   - What's unclear: Whether leaving stale `:root` values causes any issues.
   - Recommendation: Update `:root` to roughly match the silverreyes.net `[data-theme=light]` palette for future-proofing (v1.3 adds light mode), but this is low priority. At minimum, leave a comment noting they are unused in v1.2.

3. **Heading font application strategy**
   - What we know: Syne is for headings, IBM Plex Mono for everything else. Currently there is no `font-display` utility in the Tailwind setup.
   - What's unclear: Whether to apply Syne via a CSS rule targeting h1-h3, or via explicit `font-display` Tailwind classes on each heading.
   - Recommendation: Use `@theme inline { --font-display: 'Syne', sans-serif; }` to register the utility, then apply `font-display` class to headings. Additionally, add a base layer rule `h1, h2, h3 { font-family: var(--font-display); }` as a default. This gives both automatic heading styling and manual override capability.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None currently installed (no test runner in frontend) |
| Config file | None |
| Quick run command | `cd frontend && npm run build` (type-check + build) |
| Full suite command | `cd frontend && npm run build` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DSGN-01 | Dashboard colors match silverreyes.net palette | manual | Visual inspection in browser | N/A |
| DSGN-02 | Syne + IBM Plex Mono render correctly, no FOUT | manual | Visual inspection + Network tab | N/A |
| DSGN-03 | No hardcoded zinc-*/blue-*/gray-* classes remain | automated grep | `grep -rE "(zinc\|blue\|gray\|slate)-[0-9]" frontend/src --include="*.tsx" --include="*.css"` | N/A |
| DSGN-04 | shadcn/ui components display correctly with new tokens | manual + build | `cd frontend && npm run build` (catches type errors) | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run build` (ensures no compilation errors)
- **Per wave merge:** `cd frontend && npm run build` + grep validation for hardcoded classes
- **Phase gate:** Build succeeds + grep shows zero hardcoded color classes + visual verification of all pages

### Wave 0 Gaps
- [ ] No test framework installed -- all validation for this design phase is build-check + visual inspection + grep-based audit
- [ ] Grep command for DSGN-03 validation: `grep -rEn "(zinc|blue|gray|slate)-[0-9]" frontend/src/ --include="*.tsx" --include="*.css"` should return zero results after migration

*(Note: A CSS/design token phase is inherently visual. Automated visual regression testing would require Playwright/Chromatic setup which is out of scope. The build check and grep audit provide sufficient automated validation.)*

## Sources

### Primary (HIGH confidence)
- silverreyes.net live site CSS -- All palette values, font definitions, and design patterns extracted directly from the deployed Astro site's compiled CSS (2026-03-24)
- `frontend/src/index.css` -- Current shadcn/ui token structure, oklch values, @theme inline block
- `frontend/package.json` -- Current dependency versions (Tailwind 4.2.1, shadcn 4.0.8)

### Secondary (MEDIUM confidence)
- [shadcn/ui Tailwind v4 docs](https://ui.shadcn.com/docs/tailwind-v4) -- @theme inline approach, oklch migration
- [shadcn/ui Theming docs](https://ui.shadcn.com/docs/theming) -- CSS variable theming pattern
- [Fontsource Variable Fonts docs](https://fontsource.org/docs/getting-started/variable) -- @fontsource import patterns
- [@fontsource/syne npm](https://www.npmjs.com/package/@fontsource/syne) -- Package availability, version 5.2.7
- [@fontsource/ibm-plex-mono npm](https://www.npmjs.com/package/@fontsource/ibm-plex-mono) -- Package availability, version 5.2.7

### Tertiary (LOW confidence)
- oklch conversion values -- Computed via JavaScript conversion from hex; should be visually verified in browser against the live silverreyes.net site. Minor rounding differences possible.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All packages verified on npm registry, versions confirmed, existing project already uses Tailwind v4 + shadcn/ui
- Architecture: HIGH - Token remapping approach verified against existing index.css structure and shadcn/ui official docs; silverreyes.net palette extracted from live site
- Pitfalls: HIGH - Based on direct code audit of all 14 affected files with line-level specificity
- Color values: MEDIUM - oklch conversions computed mathematically from hex; may need minor visual tuning

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain -- CSS theming, font packages)
