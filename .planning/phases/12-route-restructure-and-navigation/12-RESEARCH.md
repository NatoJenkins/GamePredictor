# Phase 12: Route Restructure and Navigation - Research

**Researched:** 2026-03-24
**Domain:** React Router v7 nested layouts, route restructuring, sidebar navigation
**Confidence:** HIGH

## Summary

Phase 12 is a focused structural refactor of the application's route tree and navigation. The current app renders all pages inside a single `AppLayout` wrapper (sidebar + content). The goal is to split into two layout branches: a full-width standalone layout for the landing page at `/`, and the existing dashboard layout with sidebar for `/this-week`, `/accuracy`, `/experiments`, and `/history`.

The project uses React Router v7.13.1 with the declarative `BrowserRouter`/`Routes`/`Route` pattern (not file-based routing). React Router v7 natively supports "layout routes" -- routes without a `path` prop that wrap children in a shared layout via `<Outlet />`. This makes the two-layout-branch pattern trivial: one pathless `<Route element={<LandingLayout />}>` wrapping the `/` route, and another pathless `<Route element={<AppLayout />}>` wrapping all dashboard routes. No new libraries are needed.

The sidebar's `navItems` array is a simple data structure that drives both desktop sidebar and mobile top nav. Adding a Home item and changing This Week's path from `/` to `/this-week` are single-array edits. The `Home` icon is available from `lucide-react` (re-exports the `House` icon). The only internal link in page components (`to="/history"` in ThisWeekPage) does not need changing.

**Primary recommendation:** Use React Router v7's pathless layout route pattern to split the route tree into two branches -- one for the full-width landing and one for the dashboard with sidebar. This requires changes to exactly 3 files: `App.tsx` (route tree), `Sidebar.tsx` (navItems + branding), and a new `LandingLayout.tsx` component.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- NAV-01: Sidebar includes a Home tab linking to `/`
- NAV-02: This Week page moves from `/` to `/this-week`
- NAV-03: All existing routes (`/accuracy`, `/experiments`, `/history`) continue to work unchanged

### Claude's Discretion
- **Home tab placement and icon** -- Where Home appears in the sidebar nav order, what icon to use (e.g., Home from lucide-react), label text ("Home" vs site name)
- **Sidebar branding** -- Whether to update "NFL Predictor" text to "NFL Nostradamus" or "Nostradamus" to match the landing page (Phase 13 uses "NFL Nostradamus")
- **Landing page placeholder** -- What `/` renders between Phase 12 (route setup) and Phase 13 (content). Options: minimal placeholder with site name and link into dashboard, or a simple redirect to `/this-week` until Phase 13 is built
- **Layout transition** -- How navigation between the landing page (full-width, no sidebar) and dashboard (sidebar) feels -- abrupt layout switch vs. any transition treatment
- **Route structure** -- Whether to use nested routes with two layout wrappers (one for landing, one for dashboard) or flat routes with per-route layout assignment

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | Sidebar includes a Home tab linking to `/` | `Home` icon confirmed in lucide-react v0.577.0; `navItems` array pattern in Sidebar.tsx supports trivial addition; NavLink `end` prop prevents false active-state matching |
| NAV-02 | This Week page moves from `/` to `/this-week` route | Route tree restructure in App.tsx; navItems path update in Sidebar.tsx; no other components link to `/` for This Week |
| NAV-03 | All existing internal links and routes continue to work after restructure | Grep confirms only internal link is `to="/history"` in ThisWeekPage which is unchanged; `/accuracy`, `/experiments`, `/history` routes stay inside AppLayout branch |
</phase_requirements>

## Standard Stack

### Core (already installed -- no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-router | 7.13.1 | Client-side routing with nested layout routes | Already installed; pathless `<Route element={}>` pattern is the official way to create layout branches |
| lucide-react | 0.577.0 | `Home` icon for nav item | Already installed; `Home` is a named export (aliases `House` icon) |

### Supporting (already installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tailwindcss | 4.2.1 | Styling for LandingLayout component | Already used everywhere; use semantic tokens from Phase 11 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pathless layout routes | Per-route inline layout wrapping | Layout routes are cleaner -- no duplication, React Router handles it natively |
| New LandingLayout component | Conditional rendering in AppLayout | Violates single-responsibility; two distinct layouts should be two components |

**Installation:** No new packages required. All dependencies are already in place.

## Architecture Patterns

### Recommended Route Structure

```
<Routes>
  {/* Landing page -- standalone full-width layout, no sidebar */}
  <Route element={<LandingLayout />}>
    <Route index element={<LandingPage />} />
  </Route>

  {/* Dashboard pages -- sidebar + constrained content area */}
  <Route element={<AppLayout />}>
    <Route path="this-week" element={<ThisWeekPage />} />
    <Route path="accuracy" element={<AccuracyPage />} />
    <Route path="experiments" element={<ExperimentsPage />} />
    <Route path="history" element={<HistoryPage />} />
  </Route>
</Routes>
```

### Recommended File Structure

```
frontend/src/
├── components/
│   └── layout/
│       ├── AppLayout.tsx        # Existing -- sidebar + Outlet (unchanged)
│       ├── LandingLayout.tsx    # NEW -- full-width Outlet, no sidebar
│       └── Sidebar.tsx          # Modified -- add Home item, update paths, update branding
├── pages/
│   ├── LandingPage.tsx          # NEW -- placeholder until Phase 13
│   ├── ThisWeekPage.tsx         # Unchanged (just served at /this-week now)
│   ├── AccuracyPage.tsx         # Unchanged
│   ├── ExperimentsPage.tsx      # Unchanged
│   └── HistoryPage.tsx          # Unchanged
└── App.tsx                      # Modified -- two layout branches
```

### Pattern 1: Pathless Layout Routes (Two-Branch Route Tree)

**What:** React Router v7 allows `<Route>` elements without a `path` prop to act as layout wrappers. Child routes render inside the layout's `<Outlet />`. Two sibling pathless routes create two independent layout branches.

**When to use:** When different groups of routes need fundamentally different page chrome (e.g., landing page vs dashboard).

**Example:**
```tsx
// Source: https://reactrouter.com/start/declarative/routing
// Routes WITHOUT a path create new nesting without adding URL segments

<Routes>
  <Route element={<LandingLayout />}>
    <Route index element={<LandingPage />} />
  </Route>

  <Route element={<AppLayout />}>
    <Route path="this-week" element={<ThisWeekPage />} />
    <Route path="accuracy" element={<AccuracyPage />} />
  </Route>
</Routes>
```

**Key detail:** The `index` route (no `path`, uses `index` prop) matches the root `/` URL. This is how the landing page claims `/` without a path prefix.

### Pattern 2: NavLink Active State with `end` Prop

**What:** The `end` prop on `NavLink` prevents the link from matching descendant routes. Without `end`, a link `to="/"` would match every route since all paths start with `/`.

**When to use:** Any nav link pointing to `/` or any parent path that has children.

**Example:**
```tsx
// Source: Existing Sidebar.tsx pattern
<NavLink
  to="/"
  end  // Only active when URL is exactly "/"
  className={({ isActive }) =>
    cn(
      "flex items-center gap-2 rounded-md px-3 py-2 text-xs",
      isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-secondary"
    )
  }
>
  <Home className="h-5 w-5" />
  Home
</NavLink>
```

### Pattern 3: LandingLayout -- Minimal Full-Width Wrapper

**What:** A simple layout component that renders `<Outlet />` without sidebar, constrained width, or dashboard chrome. Uses the same `bg-background text-foreground` base as AppLayout for visual consistency.

**Example:**
```tsx
// Source: Pattern derived from existing AppLayout.tsx
import { Outlet } from "react-router";

export function LandingLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main>
        <Outlet />
      </main>
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Conditional layout in a single wrapper:** Do not add `if (isLandingPage) return <FullWidth>` inside AppLayout. Two distinct layouts should be two separate components connected via the route tree.
- **Redirecting `/` to `/this-week` as the permanent solution:** While a temporary redirect is fine during Phase 12 (before Phase 13 content exists), the route tree must support `/` as a real landing page route so Phase 13 can drop in content.
- **Removing `end` prop from Home NavLink:** Without `end`, the Home link would show active state on every page since all URLs technically match `/`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Layout branching | Custom layout-selection logic | React Router pathless `<Route element={}>` | Router handles it declaratively; no conditional rendering needed |
| Active nav highlighting | Manual `useLocation` + string matching | `NavLink` with `isActive` callback + `end` prop | Built into React Router; handles edge cases (trailing slashes, query params) |
| Mobile + desktop nav sync | Separate nav item arrays | Single `navItems` array driving both views | Already the established pattern in Sidebar.tsx; one change covers both |

**Key insight:** This phase needs zero custom logic. React Router's declarative route tree and NavLink component handle every requirement natively.

## Common Pitfalls

### Pitfall 1: Forgetting `end` on the Home NavLink
**What goes wrong:** The Home link shows as active on every dashboard page because `/` is a prefix of all paths.
**Why it happens:** `NavLink` without `end` matches the current URL by prefix, not exact match.
**How to avoid:** Always use `end` prop on the Home (`to="/"`) NavLink.
**Warning signs:** Home tab appears highlighted on every page.

### Pitfall 2: Index Route vs Path Route Confusion
**What goes wrong:** Using `<Route path="/" element={<LandingPage />}>` inside a pathless layout route creates a conflict with dashboard routes also nested under `/`.
**Why it happens:** `path="/"` matches differently than `index` when nested under pathless layout routes.
**How to avoid:** Use `<Route index element={<LandingPage />} />` (no `path` prop, just `index`) for the landing page inside the LandingLayout branch.
**Warning signs:** Landing page renders when navigating to dashboard routes, or 404s on `/`.

### Pitfall 3: Breaking Bookmarked URLs
**What goes wrong:** Users who bookmarked `/` expecting This Week content now see the landing page.
**Why it happens:** This is by design (NAV-02), but needs awareness.
**How to avoid:** This is intentional behavior. The placeholder landing page should include a clear link/CTA into the dashboard at `/this-week` so users can easily find the content they expect.
**Warning signs:** User confusion if the placeholder offers no navigation to the dashboard.

### Pitfall 4: Sidebar NavLink `end` Prop on Non-Root Routes
**What goes wrong:** Adding `end` to dashboard NavLinks that don't need it (e.g., `/accuracy`).
**Why it happens:** Copy-paste from the Home link pattern.
**How to avoid:** Only use `end` on the Home link (`to="/"`). Other dashboard routes are leaf routes and don't need it. The existing pattern already handles this correctly (`end={item.to === "/"}`).
**Warning signs:** No visible issue, but unnecessary code.

### Pitfall 5: SPA Fallback in Production
**What goes wrong:** Direct browser navigation to `/this-week` returns a 404 in production.
**Why it happens:** The web server doesn't know to serve `index.html` for all routes. Currently no SPA fallback config exists (no `_redirects`, `vercel.json`, or similar).
**How to avoid:** This is a pre-existing concern, not introduced by Phase 12. Vite dev server handles it automatically. In production, the deployment target must be configured for SPA fallback. This is outside Phase 12 scope but worth noting.
**Warning signs:** 404 on page refresh in production.

## Code Examples

### Updated App.tsx Route Tree
```tsx
// Source: Derived from existing App.tsx + React Router v7 layout route pattern
import { BrowserRouter, Routes, Route } from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppLayout } from "@/components/layout/AppLayout";
import { LandingLayout } from "@/components/layout/LandingLayout";
import { LandingPage } from "@/pages/LandingPage";
import { ThisWeekPage } from "@/pages/ThisWeekPage";
import { AccuracyPage } from "@/pages/AccuracyPage";
import { ExperimentsPage } from "@/pages/ExperimentsPage";
import { HistoryPage } from "@/pages/HistoryPage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<LandingLayout />}>
              <Route index element={<LandingPage />} />
            </Route>
            <Route element={<AppLayout />}>
              <Route path="this-week" element={<ThisWeekPage />} />
              <Route path="accuracy" element={<AccuracyPage />} />
              <Route path="experiments" element={<ExperimentsPage />} />
              <Route path="history" element={<HistoryPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
```

### Updated Sidebar navItems Array
```tsx
// Source: Derived from existing Sidebar.tsx navItems pattern
import { Home, Calendar, BarChart3, FlaskConical, History } from "lucide-react";

const navItems = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/this-week", icon: Calendar, label: "This Week" },
  { to: "/accuracy", icon: BarChart3, label: "Accuracy" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments" },
  { to: "/history", icon: History, label: "History" },
] as const;
```

### New LandingLayout Component
```tsx
// Source: Derived from existing AppLayout.tsx pattern
import { Outlet } from "react-router";

export function LandingLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main>
        <Outlet />
      </main>
    </div>
  );
}
```

### Placeholder LandingPage Component
```tsx
// Temporary placeholder until Phase 13 builds the real content
import { Link } from "react-router";

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="font-display text-4xl text-foreground">NFL Nostradamus</h1>
      <p className="text-muted-foreground">Landing page coming soon.</p>
      <Link
        to="/this-week"
        className="rounded-md bg-primary px-6 py-3 text-sm text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
```

## Discretion Recommendations

Based on research, here are recommendations for the areas left to Claude's discretion:

### Home Tab Placement and Icon
**Recommendation:** Place Home first in the navItems array (before This Week), use the `Home` icon from lucide-react, label it "Home". Rationale: Home is conventionally the first nav item in every sidebar. The `Home` icon is universally recognized.

### Sidebar Branding
**Recommendation:** Update "NFL Predictor" to "Nostradamus" in both desktop sidebar header and mobile nav. Rationale: Phase 13 introduces "NFL Nostradamus" as the brand. The sidebar should match. "Nostradamus" is shorter and fits better in the sidebar's constrained width. The landing page (Phase 13) will show the full "NFL Nostradamus" in the hero.

### Landing Page Placeholder
**Recommendation:** Create a minimal placeholder page (not a redirect) with "NFL Nostradamus" heading, a brief "coming soon" message, and a prominent link to `/this-week`. Rationale: A real route with real content (even minimal) validates the entire route structure works. A redirect would mask routing bugs and make it impossible to visually confirm the landing layout has no sidebar.

### Layout Transition
**Recommendation:** No transition treatment -- simple abrupt layout switch. Rationale: Adding CSS transitions between full-width and sidebar layouts is complex (layout shifts, animation timing, route-change detection) and provides minimal UX value for a technical dashboard. Clean, instant layout switches are standard for this type of application.

### Route Structure
**Recommendation:** Use nested routes with two pathless layout wrappers (LandingLayout and AppLayout). Rationale: This is the React Router v7 standard pattern. It is declarative, clean, and supported natively. Flat routes with per-route layout assignment would require manual layout wrapping in each page component.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| React Router v5/v6 `<Switch>` | React Router v7 `<Routes>` + pathless `<Route>` | v6.4+ / v7.0 | Layout routes are first-class; no need for custom layout HOCs |
| Manual `useLocation` for active nav | `NavLink` with `isActive` callback | React Router v6+ | Built-in active class management with `end` prop support |

**Deprecated/outdated:**
- `<Switch>` component: Replaced by `<Routes>` in React Router v6+. Not applicable to this project (already on v7).

## Open Questions

1. **SPA fallback for production deployment**
   - What we know: No SPA fallback config exists (`_redirects`, `vercel.json`, etc.). Vite dev server handles it automatically. The Dockerfile only serves the Python API.
   - What's unclear: How the frontend is deployed in production. Adding `/this-week` as a new deep-linkable route means direct browser access must be handled.
   - Recommendation: Outside Phase 12 scope. Note it as a concern but do not block on it. This is a pre-existing issue (all current routes have the same problem).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None -- no frontend test infrastructure exists |
| Config file | None |
| Quick run command | `cd frontend && npm run build` (type-check + build validates no broken imports/routes) |
| Full suite command | `cd frontend && npm run build && npm run lint` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | Sidebar includes Home tab linking to `/` | manual | Visual inspection in browser: sidebar shows Home icon+label, clicking navigates to `/` | N/A |
| NAV-02 | This Week page at `/this-week` | manual | Navigate to `/this-week` in browser, confirm This Week page renders with sidebar | N/A |
| NAV-03 | Existing routes continue to work | smoke | `cd frontend && npm run build` (verifies no broken imports); manual navigation to `/accuracy`, `/experiments`, `/history` | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run build` (catches TypeScript errors, broken imports, missing components)
- **Per wave merge:** `cd frontend && npm run build && npm run lint`
- **Phase gate:** Build succeeds + manual verification of all 5 routes (/, /this-week, /accuracy, /experiments, /history) with correct layout per route

### Wave 0 Gaps
- No frontend test framework exists (no vitest, jest, or playwright). This is a project-wide gap, not specific to Phase 12.
- For this phase, `npm run build` provides sufficient automated validation (TypeScript type-checking catches broken imports and missing props). Manual route verification covers the rest.
- Setting up a test framework is outside Phase 12 scope.

## Sources

### Primary (HIGH confidence)
- `frontend/src/App.tsx` -- Current route tree (4 routes under single AppLayout)
- `frontend/src/components/layout/AppLayout.tsx` -- Current dashboard layout (Sidebar + Outlet)
- `frontend/src/components/layout/Sidebar.tsx` -- Current navItems array, NavLink pattern, branding text
- `frontend/package.json` -- react-router@7.13.1, lucide-react@0.577.0
- `frontend/node_modules/lucide-react/dist/esm/lucide-react.js` -- Confirmed `Home` is a named export (aliases House)
- [React Router v7 Declarative Routing](https://reactrouter.com/start/declarative/routing) -- Official docs confirming pathless layout route pattern

### Secondary (MEDIUM confidence)
- [React Router v7 Guide - LogRocket](https://blog.logrocket.com/react-router-v7-guide/) -- Community guide confirming nested layout patterns
- [Nested Routes in React Router - react.wiki](https://react.wiki/router/nested-routes/) -- Additional confirmation of layout route pattern

### Tertiary (LOW confidence)
- None -- all findings verified against installed code and official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and verified; no new dependencies
- Architecture: HIGH -- React Router v7 pathless layout route pattern verified against official docs and matches existing project patterns
- Pitfalls: HIGH -- All pitfalls derived from direct code inspection and React Router documentation
- Discretion recommendations: MEDIUM -- Based on common conventions and project context, but subjective

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable -- no fast-moving dependencies)
