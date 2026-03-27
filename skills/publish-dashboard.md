---
description: Publish a new HTML dashboard to Jeff Carpenter's GitHub Pages project site, following the Elastic EUI-inspired style guide.
---

# Publish Dashboard Skill

Use this skill when asked to create and publish a new dashboard or report to Jeff Carpenter's project site.

## Site context

- **Live URL:** https://jcarpenter-optro.github.io/jcarpenter/
- **Repo:** https://github.com/jcarpenter-optro/jcarpenter.git
- **Local working copy:** ~/jcarpenter/

If ~/jcarpenter/ does not exist locally, clone it first:
```bash
git clone https://github.com/jcarpenter-optro/jcarpenter.git ~/jcarpenter
```

## Steps to publish a new dashboard

### 1. Build the dashboard HTML

- Self-contained single HTML file, no external dependencies (all CSS and JS inline)
- Name it descriptively, e.g. `my-report.html`
- Place it at the root of ~/jcarpenter/
- Sub-pages go in a matching subdirectory, e.g. `my-report/page.html`
- Do NOT add a password gate: the gate lives only on index.html
- Do NOT use em dashes (—) or separator dashes (e.g. "Title - Subtitle"). Use a colon and a space instead (e.g. "Title: Subtitle")
- Derive all summary numbers from the same data source used to generate the content: never hardcode stats by hand

Apply the EUI Style Guide below exactly. Do not invent new patterns.

### 2. Add a project card to index.html

Open ~/jcarpenter/index.html and find:
```html
<!-- ADD NEW PROJECTS ABOVE THIS LINE -->
```

Insert above it:
```html
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
```

### 3. Deploy

```bash
cd ~/jcarpenter
git add -A
git commit -m "feat: add [report name] dashboard"
git push origin main
```

GitHub Pages deploys automatically within ~60 seconds.

---

## EUI Style Guide

Every dashboard must use this CSS and these patterns verbatim. The goal is a clean Elastic-style data dashboard: white background, subtle borders, Inter typeface, and semantic color for status.

### Required CSS (paste into every dashboard's `<style>` block)

```css
/* EUI-inspired design tokens */
:root {
  /* Colors */
  --color-primary: #0B64DD;
  --color-primary-bg: #F1F6FF;
  --color-accent: #BC1E70;
  --color-accent-secondary: #008B87;
  --color-success: #008A5E;
  --color-success-bg: #E6F5F0;
  --color-warning: #FACB3D;
  --color-warning-text: #825803;
  --color-warning-bg: #FFF8E1;
  --color-danger: #C61E25;
  --color-danger-bg: #FDECEA;

  /* Neutral scale */
  --color-full-shade: #07101F;
  --color-ink: #1A1C21;
  --color-paragraph: #343741;
  --color-subdued: #646A76;
  --color-ghost: #FFFFFF;
  --color-light-shade: #E3E8F2;
  --color-lightest-shade: #F5F7FA;
  --color-empty-shade: #FFFFFF;

  /* Typography */
  --font-body: 'Inter', BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  --font-mono: 'Roboto Mono', Menlo, Courier, monospace;
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-medium: 450;
  --font-weight-semibold: 500;
  --font-weight-bold: 600;

  /* Font scale (rem, 16px root) */
  --text-xs: 0.857rem;    /* ~13.7px */
  --text-s:  1.000rem;    /* 16px */
  --text-m:  1.143rem;    /* ~18.3px */
  --text-l:  1.429rem;    /* ~22.9px */
  --text-xl: 1.714rem;    /* ~27.4px */
  --text-xxl: 2.143rem;   /* ~34.3px */
  --line-height-xs: 1.429rem;
  --line-height-s:  1.714rem;
  --line-height-m:  2.000rem;
  --line-height-l:  2.286rem;

  /* Spacing (4px grid) */
  --space-xxs: 2px;
  --space-xs:  4px;
  --space-s:   8px;
  --space-m:   12px;
  --space-base: 16px;
  --space-l:   24px;
  --space-xl:  32px;
  --space-xxl: 40px;
  --space-xxxl: 48px;
  --space-xxxxl: 64px;

  /* Borders */
  --border-color: #E3E8F2;
  --border-thin: 1px solid #E3E8F2;
  --border-thick: 2px solid #E3E8F2;
  --border-radius: 4px;

  /* Shadows */
  --shadow-xs: 0 1px 2px hsla(217, 30%, 24%, 0.08), 0 2px 4px hsla(217, 30%, 24%, 0.06);
  --shadow-s:  0 1px 3px hsla(217, 30%, 24%, 0.10), 0 4px 8px hsla(217, 30%, 24%, 0.07);
  --shadow-m:  0 2px 6px hsla(217, 30%, 24%, 0.10), 0 8px 16px hsla(217, 30%, 24%, 0.08);

  /* Page max-width */
  --page-max-width: 1200px;
}

/* Reset + base */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-body);
  font-size: var(--text-s);
  font-weight: var(--font-weight-regular);
  line-height: var(--line-height-s);
  color: var(--color-paragraph);
  background: var(--color-lightest-shade);
  -webkit-font-smoothing: antialiased;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-body);
  color: var(--color-ink);
  line-height: var(--line-height-m);
}
h1 { font-size: var(--text-xxl); font-weight: var(--font-weight-semibold); }
h2 { font-size: var(--text-xl);  font-weight: var(--font-weight-semibold); }
h3 { font-size: var(--text-l);   font-weight: var(--font-weight-semibold); }
h4 { font-size: var(--text-m);   font-weight: var(--font-weight-semibold); }
h5 { font-size: var(--text-s);   font-weight: var(--font-weight-semibold); }
h6 { font-size: var(--text-xs);  font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-subdued); }

p { line-height: var(--line-height-s); }
p + p { margin-top: var(--space-m); }

.text-subdued { color: var(--color-subdued); }
.text-xs { font-size: var(--text-xs); line-height: var(--line-height-xs); }
.text-s  { font-size: var(--text-s);  line-height: var(--line-height-s); }
.text-m  { font-size: var(--text-m);  line-height: var(--line-height-m); }
.text-mono { font-family: var(--font-mono); font-size: var(--text-xs); }
.text-number { font-variant-numeric: tabular-nums; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Page layout */
.page-header {
  background: var(--color-empty-shade);
  border-bottom: var(--border-thin);
  padding: var(--space-l) 0;
}
.page-header-inner {
  max-width: var(--page-max-width);
  margin: 0 auto;
  padding: 0 var(--space-l);
}
.page-header h1 {
  font-size: var(--text-l);
  font-weight: var(--font-weight-semibold);
  color: var(--color-ink);
}
.page-header .breadcrumb {
  font-size: var(--text-xs);
  color: var(--color-subdued);
  margin-bottom: var(--space-xs);
}
.page-header .breadcrumb a {
  color: var(--color-primary);
  text-decoration: none;
}
.page-header .breadcrumb a:hover { text-decoration: underline; }

.page-body {
  max-width: var(--page-max-width);
  margin: 0 auto;
  padding: var(--space-l);
}

/* Panel (the core content container) */
.panel {
  background: var(--color-empty-shade);
  border: var(--border-thin);
  border-radius: var(--border-radius);
  padding: var(--space-l);
}
.panel + .panel { margin-top: var(--space-l); }
.panel--no-padding { padding: 0; }
.panel--shadow { border: none; box-shadow: var(--shadow-s); }
.panel--subdued { background: var(--color-lightest-shade); }

/* Panel title (flush top of panel) */
.panel-title {
  font-size: var(--text-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-subdued);
  margin-bottom: var(--space-m);
}

/* Stat / metric display */
.stat-row {
  display: grid;
  gap: var(--space-m);
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  margin-bottom: var(--space-l);
}
.stat-card {
  background: var(--color-empty-shade);
  border: var(--border-thin);
  border-radius: var(--border-radius);
  padding: var(--space-m) var(--space-l);
}
.stat-card__label {
  font-size: var(--text-xs);
  color: var(--color-subdued);
  margin-bottom: var(--space-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: var(--font-weight-semibold);
}
.stat-card__value {
  font-size: var(--text-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}
.stat-card__description {
  font-size: var(--text-xs);
  color: var(--color-subdued);
  margin-top: var(--space-xs);
}

/* Badge */
.badge {
  display: inline-flex;
  align-items: center;
  font-size: var(--text-xs);
  font-weight: var(--font-weight-semibold);
  padding: 2px var(--space-s);
  border-radius: var(--border-radius);
  line-height: 1.5;
}
.badge--default  { background: var(--color-lightest-shade); color: var(--color-subdued); border: var(--border-thin); }
.badge--primary  { background: var(--color-primary-bg); color: var(--color-primary); }
.badge--success  { background: var(--color-success-bg); color: var(--color-success); }
.badge--warning  { background: var(--color-warning-bg); color: var(--color-warning-text); }
.badge--danger   { background: var(--color-danger-bg); color: var(--color-danger); }

/* Status health dot */
.health {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-xs);
}
.health__dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.health--success .health__dot { background: var(--color-success); }
.health--warning .health__dot { background: var(--color-warning); }
.health--danger  .health__dot { background: var(--color-danger); }
.health--unknown .health__dot { background: var(--color-subdued); }

/* Callout */
.callout {
  border-radius: var(--border-radius);
  padding: var(--space-m) var(--space-l);
  border-left: 4px solid;
  margin-bottom: var(--space-m);
}
.callout--info    { background: var(--color-primary-bg); border-color: var(--color-primary); }
.callout--success { background: var(--color-success-bg); border-color: var(--color-success); }
.callout--warning { background: var(--color-warning-bg); border-color: var(--color-warning); }
.callout--danger  { background: var(--color-danger-bg);  border-color: var(--color-danger); }
.callout__title {
  font-size: var(--text-s);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-xs);
  color: var(--color-ink);
}
.callout__body { font-size: var(--text-s); color: var(--color-paragraph); }

/* Table */
.table-wrap { overflow-x: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-s);
}
thead th {
  font-size: var(--text-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-subdued);
  text-align: left;
  padding: var(--space-s) var(--space-m);
  border-bottom: var(--border-thick);
  white-space: nowrap;
}
tbody td {
  padding: var(--space-m);
  border-bottom: var(--border-thin);
  vertical-align: middle;
  color: var(--color-paragraph);
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: var(--color-lightest-shade); }
td.numeric, th.numeric { text-align: right; font-variant-numeric: tabular-nums; }

/* Two-column grid */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-l); }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-l); }
@media (max-width: 768px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
}

/* Flex row utility */
.flex-row { display: flex; align-items: center; gap: var(--space-m); }
.flex-row--apart { justify-content: space-between; }
.flex-row--wrap { flex-wrap: wrap; }

/* Separator */
.separator {
  border: none;
  border-top: var(--border-thin);
  margin: var(--space-l) 0;
}

/* Code block */
pre {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: var(--color-lightest-shade);
  border: var(--border-thin);
  border-radius: var(--border-radius);
  padding: var(--space-m);
  overflow-x: auto;
  color: var(--color-ink);
  line-height: 1.6;
}
code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: var(--color-lightest-shade);
  border: var(--border-thin);
  border-radius: 2px;
  padding: 1px var(--space-xs);
  color: var(--color-ink);
}
pre code { background: none; border: none; padding: 0; font-size: inherit; }

/* Link */
a { color: var(--color-primary); text-decoration: none; }
a:hover { text-decoration: underline; }
```

### Required `<head>` block

Every dashboard must include this `<head>` to load Inter:

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Report Title</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;450;500;600&family=Roboto+Mono:wght@400&display=swap" rel="stylesheet">
  <style>
    /* paste full EUI CSS here */
  </style>
</head>
```

### Page structure template

Every dashboard follows this skeleton:

```html
<body>
  <!-- Page header -->
  <header class="page-header">
    <div class="page-header-inner">
      <div class="breadcrumb"><a href="index.html">Projects</a> / Report Title</div>
      <h1>Report Title</h1>
      <p class="text-subdued" style="margin-top:var(--space-xs)">Short description of what this report covers. Generated YYYY-MM-DD.</p>
    </div>
  </header>

  <!-- Main content -->
  <main class="page-body">

    <!-- Summary stats row -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-card__label">Metric Name</div>
        <div class="stat-card__value">123</div>
        <div class="stat-card__description">Optional context</div>
      </div>
      <!-- repeat for each KPI -->
    </div>

    <!-- Content panels -->
    <div class="panel">
      <div class="panel-title">Section Title</div>
      <!-- content -->
    </div>

  </main>
</body>
```

### Design rules

1. **White panels on a light gray page.** Background is `--color-lightest-shade` (#F5F7FA). All content lives inside `.panel` (white, bordered).
2. **Borders, not shadows, by default.** Use `box-shadow` only for emphasis (`.panel--shadow`). Most panels use `border: var(--border-thin)`.
3. **Section labels are uppercase + subdued.** Use `.panel-title` or `h6` for all section headings inside panels.
4. **Semantic color carries meaning.** Use `.badge--success`, `.badge--warning`, `.badge--danger`, `.health--*` for status. Never use color alone: pair it with text.
5. **Tables are the default for tabular data.** Use the table styles above. Right-align numeric columns with `.numeric`.
6. **Spacing follows the 4px grid.** Use `--space-*` variables for all margins and padding. Never use arbitrary pixel values.
7. **No decorative color blocks.** Avoid full-color backgrounds except for semantic badges and callouts. Panels are white.
8. **Typography hierarchy:** Page title uses `h1`, panel sections use `.panel-title` (uppercase label), data uses `h4` or `.stat-card__value`, supporting text uses `.text-subdued`.
9. **Responsive grids.** Use `.grid-2` / `.grid-3` for side-by-side panels. They collapse to single column below 768px.
10. **Numbers use tabular numerals.** Add `font-variant-numeric: tabular-nums` (via `.text-number`) on any column of figures.
11. **No dashes as separators.** Never use em dashes (—) or separator dashes (e.g. "Title - Subtitle") anywhere in the HTML content. Use a colon and a space instead (e.g. "Title: Subtitle").

---

## Password

The projects index is password-protected. Password stored as SHA-256 hash only: never in plaintext. localStorage key: `luna_auth`. To change the password: generate a new SHA-256 hash and replace the `HASH` constant in index.html.
