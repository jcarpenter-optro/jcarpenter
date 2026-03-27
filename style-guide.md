# How to publish a new dashboard to Jeff Carpenter's project site

## Context

This is a GitHub Pages site at https://jcarpenter-optro.github.io/jcarpenter/
The repo is: https://github.com/jcarpenter-optro/jcarpenter.git
The working copy on this machine lives at: /tmp/luna-report/

The site structure:
- index.html: password-protected projects hub (password gate uses SHA-256, key "luna_auth" in localStorage)
- luna-components.html: Luna Design System Ember vs React parity dashboard (first project)
- components/*.html: 79 individual component comparison pages for the luna report
- manifest.json: machine-generated component inventory used by the luna report

## To add a new dashboard

### Step 1: Create the dashboard HTML file

Build your dashboard as a self-contained HTML file (no external dependencies).
Name it something descriptive, e.g. `my-report.html`.
Place it at the root of /tmp/luna-report/ (alongside index.html and luna-components.html).

If the dashboard has sub-pages, put them in a subdirectory, e.g. `my-report/page.html`.

The dashboard does NOT need a password gate — the gate lives only on index.html.

### Step 2: Add an entry to index.html

Open /tmp/luna-report/index.html and find this comment:

    <!-- ADD NEW PROJECTS ABOVE THIS LINE -->

Insert a new project card above it, following this pattern:

    <a href="my-report.html" class="project-card">
      <div class="left">
        <div class="title">Your Report Title</div>
        <div style="margin-top:6px">
          <span class="tag">Tag 1</span>
          <span class="tag">Tag 2</span>
        </div>
        <div class="desc">One or two sentences describing what the report covers.</div>
      </div>
      <div class="arrow">→</div>
    </a>

### Step 3: Deploy

From /tmp/luna-report/:

    git add -A
    git commit -m "feat: add [report name] dashboard"
    git push origin main

GitHub Pages deploys automatically. The site is live within ~60 seconds.

## Password

The projects index is password-protected. The password is stored only as a SHA-256 hash
in index.html — never in plaintext. localStorage key: luna_auth.
To change the password, generate a new SHA-256 hash and replace the HASH constant in index.html.

---

## Style Guide

All dashboards on this site share a common visual language. Use the rules below so every report looks like it belongs to the same system.

### Color palette

| Role | Hex | Usage |
|---|---|---|
| Page background | `#0f1117` | `body` background |
| Card background | `#1e2130` | panels, stat cards, tables |
| Topbar/header bg | `#171923` | `thead`, panel headers, topbar |
| Border | `#2d3148` | all card/panel/table borders |
| Row hover | `#252a3d` | `tbody tr:hover` |
| Body text | `#e2e8f0` | primary readable text |
| Muted text | `#64748b` | labels, subtitles, empty states |
| Secondary text | `#94a3b8` | body copy inside callouts, table cells |
| Heading white | `#f8fafc` | `h1`, card titles |
| Accent purple | `#7c3aed` | buttons, focus rings, hover accents |
| Accent purple dark | `#6d28d9` | button hover state |
| Purple badge bg | `#2e1065` | "both" / shared status badges |
| Purple badge text | `#c4b5fd` | text on purple badges |

### Semantic colors (for status and callouts)

| Meaning | Background | Border/Text |
|---|---|---|
| Info / blue | `#0f1f3d` | `#38bdf8` |
| Warning / amber | `#1c1407` | `#fbbf24` |
| Success / green | `#052e16` | `#34d399` |
| Danger / red | `#1f0a0a` | `#f87171` |
| Orange accent | `#431407` bg / `#fb923c` text | `#7c2d12` border |
| Blue accent | `#082f49` bg / `#38bdf8` text | `#0c4a6e` border |

### Typography

- **Font stack:** `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- **Monospace stack:** `"SF Mono", "Fira Code", "Fira Mono", monospace` — use for code, component names, file paths, chips
- **Page title (`h1`):** 24px, weight 700, color `#f8fafc`
- **Subtitle:** 13px, color `#64748b`, margin-bottom 32px
- **Section labels:** 11px, uppercase, letter-spacing 0.08em, color `#64748b`, weight 600
- **Card labels:** 11px, uppercase, letter-spacing 0.08em, color `#64748b`
- **Body / table text:** 13px
- **Small / meta text:** 11px

### Spacing and shape

- **Page padding:** `32px` all sides (`padding: 32px` on body)
- **Card border-radius:** `10px` for panels and stat cards, `6px` for small elements (buttons, badges), `20px` for pills/filter buttons, `4px` for status badges
- **Card padding:** `20px` for stat cards, `16px 20px` for panel headers and callouts, `9px 16px` for table cells
- **Grid gaps:** `16px` standard between cards and panels
- **Section spacing:** `margin-bottom: 32px` after major sections, `24px` between mid-level sections

### Components

**Stat card** — large number metric with a label above and sub-label below:
```html
<div class="stat-card">
  <div class="label">Label Text</div>
  <div class="value color-*">42</div>
  <div class="sub">Supporting note</div>
</div>
```
Lay out in a CSS grid: `grid-template-columns: repeat(N, 1fr); gap: 16px`.

**Callout** — left-bordered insight box with icon, title, and body:
```html
<div class="callout callout-info|warn|success|danger">
  <div class="callout-icon">ℹ</div>
  <div class="callout-body">
    <div class="callout-title">Title</div>
    <div class="callout-text">Body text. <strong>Highlights</strong> in white.</div>
  </div>
</div>
```
Lay out in a 2-column grid with `gap: 16px`.

**Panel** — card with a header bar and content area:
```html
<div class="panel">
  <div class="panel-header">
    Title <span class="pill pill-count">N</span>
  </div>
  <!-- content -->
</div>
```

**Status badge** — inline colored label:
```html
<span class="status-badge status-both|status-ember|status-react">Label</span>
```

**Chip** — monospace tag, used for item lists:
```html
<span class="chip chip-ember-only|chip-react-only">name</span>
```

**Filter bar** — tab-style row of toggle buttons above a table:
```html
<div class="filter-bar">
  <button class="filter-btn active" onclick="filterTable('all',this)">All</button>
  <button class="filter-btn" onclick="filterTable('foo',this)">Foo</button>
</div>
```
Table rows carry `data-status="foo"`. The JS pattern to wire it up:
```js
function filterTable(status, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('tbody tr').forEach(row => {
    row.style.display = (status === 'all' || row.dataset.status === status) ? '' : 'none';
  });
}
```

**Progress bar** — thin segmented bar showing proportional breakdown:
```html
<div class="bar-wrap">
  <div class="bar-fill">
    <div style="width:85%;background:#7c3aed"></div>
    <div style="width:10%;background:#ea580c"></div>
    <div style="width:5%;background:#0284c7"></div>
  </div>
</div>
```

### Rules

- No external dependencies. All CSS and JS must be inline in the HTML file.
- No em dashes (—). Use a colon and a space instead.
- Dark background only. Do not mix light and dark sections.
- Do not add the password gate to dashboards — only `index.html` carries the gate.
- Derive all summary numbers programmatically from the same data source used to generate the content. Never hardcode stats by hand.

---

## Notes

- Do not add the password gate to sub-pages or individual dashboards — only index.html is gated.
- The luna-components.html report is generated by /tmp/generate-luna-report.py.
  To regenerate it (e.g. after luna-core or luna-react changes), run that script then redeploy.
