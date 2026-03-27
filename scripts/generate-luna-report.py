#!/usr/bin/env python3
"""
Luna component parity report generator.
Uses index.ts exports as the source of truth, not directory listings.
Styles follow the EUI-inspired design system (publish-dashboard.md).
"""
import os, re, html, json
from pathlib import Path
from datetime import datetime

EMBER_BASE  = Path("/Users/jcarpenter/Git Repositories/auditboard-frontend/libraries/luna-core/package/src")
REACT_BASE  = Path("/Users/jcarpenter/Git Repositories/auditboard-frontend/libraries/luna-react/package/src")
OUT_DIR     = Path("/tmp/luna-report")
COMP_DIR    = OUT_DIR / "components"
COMP_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parse index.ts exports
# ---------------------------------------------------------------------------

def parse_exports(index_path):
    text = index_path.read_text()
    entries = []
    for match in re.finditer(r"export\s+\{([^}]+)\}\s+from\s+'(\./[^']+)'", text):
        names_raw, path_raw = match.group(1), match.group(2)
        path_clean = re.sub(r'\.(gts|ts|tsx|js)$', '', path_raw.lstrip('./'))
        if not path_clean.startswith('components/'):
            continue
        names = [n.strip().lstrip('default as ').split(' as ')[-1].strip()
                 for n in names_raw.split(',')
                 if 'type ' not in n and n.strip()]
        if names:
            entries.append((names[0], path_clean))
    return entries

ember_exports = parse_exports(EMBER_BASE / "index.ts")
react_exports = parse_exports(REACT_BASE / "index.ts")

EMBER_EXCLUDE = {
    'fake-input', 'fake-textarea', 'fake-select', 'fake-select-multiple',
    'testing/render-test-container', 'util/cache-state', 'util/tablist-manager',
    'setup/announcer',
}

EMBER_PATH_RENAMES = {
    'layout/modal':       'modal-layout',
    'layout/navigation':  'navigation',
    'setup/growl':        'growl',
    'skeleton/text':      'skeleton',
    'tablist/panel':      None,
    'help/trigger':       None,
    'select-date/calendar': None,
    'checkbox/input':     None,
    'checkbox/element':   None,
    'button-with-menu/menu':   None,
    'button-with-menu/button': None,
    'button-with-popup/button': None,
    'select-recurrence/const':  None,
    'layout/modal/dialog': None,
    'layout/navigation/link': None,
}

def build_slug_map(exports, excludes):
    seen = {}
    for export_name, path in exports:
        rel = path.replace('components/', '', 1)
        if rel in EMBER_PATH_RENAMES:
            slug = EMBER_PATH_RENAMES[rel]
            if slug is None:
                continue
        else:
            slug = rel.split('/')[0]
        slug = re.sub(r'\.(gts|ts|tsx)$', '', slug)
        if slug in excludes or rel in excludes:
            continue
        if slug not in seen:
            seen[slug] = (export_name, path)
    return seen

ember_map = build_slug_map(ember_exports, EMBER_EXCLUDE)
react_map = build_slug_map(react_exports, set())

ember_slugs = set(ember_map.keys())
react_slugs = set(react_map.keys())
both_slugs  = ember_slugs & react_slugs
ember_only  = ember_slugs - react_slugs
react_only  = react_slugs - ember_slugs
all_slugs   = sorted(ember_slugs | react_slugs)

# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def get_ember_files(slug):
    for ext in ['.gts', '.ts']:
        f = EMBER_BASE / 'components' / f"{slug}{ext}"
        if f.exists():
            return [(f.name, f.read_text())]
    if slug in ember_map:
        _, path = ember_map[slug]
        full = EMBER_BASE / path
        for ext in ['.gts', '.ts', '']:
            candidate = Path(str(full) + ext) if ext else full
            if candidate.exists() and candidate.is_file():
                return [(candidate.name, candidate.read_text())]
        if full.parent.is_dir():
            files = sorted([f for f in full.parent.glob('*.gts')] +
                           [f for f in full.parent.glob('*.ts') if 'test' not in f.name])
            if files:
                return [(f.name, f.read_text()) for f in files[:2]]
    d = EMBER_BASE / 'components' / slug
    if d.is_dir():
        files = sorted(d.glob('*.gts')) or sorted(d.glob('*.ts'))
        return [(f.name, f.read_text()) for f in files[:2]]
    return []

def get_react_files(slug):
    d = REACT_BASE / 'components' / slug
    if not d.is_dir():
        return []
    files = sorted([f for f in d.glob('*.tsx') if 'test' not in f.name])
    return [(f.name, f.read_text()) for f in files[:2]]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

SEMANTIC_NOTES = {
    'tooltip': (
        "React has a <strong>Tooltip</strong> component with no direct Ember component equivalent. "
        "Ember exposes tooltip behaviour as a modifier, not a component. "
        "React also exports <strong>Help</strong> separately, giving it two tooltip-style APIs."
    ),
    'help': (
        "Both libraries export a <strong>Help</strong> component. "
        "Note that React also exports a separate <strong>Tooltip</strong> component. "
        "In Ember, tooltip behaviour is covered by the tooltip modifier rather than a component."
    ),
    'growl': (
        "Both libraries have a growl/notification component. "
        "Ember exports it as <strong>SetupGrowl</strong> from <code>setup/growl.gts</code>. "
        "React has it at <code>components/growl/</code>. Same concept, different naming convention."
    ),
    'modal-layout': (
        "Both libraries have a modal layout wrapper. "
        "Ember exports it as <strong>ModalLayout</strong> from <code>components/layout/modal.gts</code>. "
        "React has it as a standalone <code>modal-layout/</code> directory."
    ),
    'navigation': (
        "Both libraries have a navigation component. "
        "Ember exports it as <strong>NavigationLayout</strong> from <code>components/layout/navigation.gts</code>. "
        "React has it as a standalone <code>navigation/</code> directory."
    ),
    'skeleton': (
        "Both libraries have skeleton loading components. "
        "Ember exports <strong>SkeletonText</strong> from <code>components/skeleton/text.gts</code>. "
        "React exports both <strong>Skeleton</strong> and <strong>SkeletonText</strong>, suggesting a broader React API."
    ),
}

def analyze(slug, ember_files, react_files):
    if slug in SEMANTIC_NOTES:
        return SEMANTIC_NOTES[slug]
    in_ember, in_react = bool(ember_files), bool(react_files)
    if not in_ember:
        return (f"<strong>{slug}</strong> exists only in the React library. "
                "It has not yet been ported to Ember/Glimmer and represents work in the React migration backlog.")
    if not in_react:
        return (f"<strong>{slug}</strong> exists only in the Ember/Glimmer library. "
                "It is part of the React migration backlog.")
    ember_lines = sum(c.count('\n') for _, c in ember_files)
    react_lines  = sum(c.count('\n') for _, c in react_files)
    size_note = ""
    if abs(ember_lines - react_lines) > 40:
        bigger = "React" if react_lines > ember_lines else "Ember"
        size_note = (f" The {bigger} version is notably larger "
                     f"({max(ember_lines,react_lines)} vs {min(ember_lines,react_lines)} lines), "
                     "suggesting a broader API or different implementation approach.")
    ember_name, _ = ember_map.get(slug, (slug, ''))
    react_name,  _ = react_map.get(slug, (slug, ''))
    name_note = ""
    clean = lambda s: s.lower().replace('luna','').replace('layout','').strip()
    if clean(ember_name) != clean(react_name):
        name_note = f" Exported as <strong>{ember_name}</strong> in Ember and <strong>{react_name}</strong> in React."
    return (f"Both libraries implement <strong>{slug}</strong>.{name_note} "
            f"Ember: {ember_lines} lines. React: {react_lines} lines.{size_note}")

# ---------------------------------------------------------------------------
# EUI base CSS (shared across all pages)
# ---------------------------------------------------------------------------

EUI_CSS = """
:root {
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
  --color-full-shade: #07101F;
  --color-ink: #1A1C21;
  --color-paragraph: #343741;
  --color-subdued: #646A76;
  --color-ghost: #FFFFFF;
  --color-light-shade: #E3E8F2;
  --color-lightest-shade: #F5F7FA;
  --color-empty-shade: #FFFFFF;
  --font-body: 'Inter', BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  --font-mono: 'Roboto Mono', Menlo, Courier, monospace;
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-medium: 450;
  --font-weight-semibold: 500;
  --font-weight-bold: 600;
  --text-xs: 0.857rem;
  --text-s: 1.000rem;
  --text-m: 1.143rem;
  --text-l: 1.429rem;
  --text-xl: 1.714rem;
  --text-xxl: 2.143rem;
  --line-height-xs: 1.429rem;
  --line-height-s: 1.714rem;
  --line-height-m: 2.000rem;
  --line-height-l: 2.286rem;
  --space-xxs: 2px; --space-xs: 4px; --space-s: 8px; --space-m: 12px;
  --space-base: 16px; --space-l: 24px; --space-xl: 32px; --space-xxl: 40px;
  --space-xxxl: 48px; --space-xxxxl: 64px;
  --border-color: #E3E8F2;
  --border-thin: 1px solid #E3E8F2;
  --border-thick: 2px solid #E3E8F2;
  --border-radius: 4px;
  --shadow-xs: 0 1px 2px hsla(217,30%,24%,.08), 0 2px 4px hsla(217,30%,24%,.06);
  --shadow-s:  0 1px 3px hsla(217,30%,24%,.10), 0 4px 8px hsla(217,30%,24%,.07);
  --shadow-m:  0 2px 6px hsla(217,30%,24%,.10), 0 8px 16px hsla(217,30%,24%,.08);
  --page-max-width: 1200px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-body); font-size: var(--text-s); font-weight: var(--font-weight-regular); line-height: var(--line-height-s); color: var(--color-paragraph); background: var(--color-lightest-shade); -webkit-font-smoothing: antialiased; }
h1,h2,h3,h4,h5,h6 { font-family: var(--font-body); color: var(--color-ink); line-height: var(--line-height-m); }
h1 { font-size: var(--text-xxl); font-weight: var(--font-weight-semibold); }
h2 { font-size: var(--text-xl);  font-weight: var(--font-weight-semibold); }
h3 { font-size: var(--text-l);   font-weight: var(--font-weight-semibold); }
h4 { font-size: var(--text-m);   font-weight: var(--font-weight-semibold); }
h5 { font-size: var(--text-s);   font-weight: var(--font-weight-semibold); }
h6 { font-size: var(--text-xs);  font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: .06em; color: var(--color-subdued); }
p { line-height: var(--line-height-s); }
p + p { margin-top: var(--space-m); }
a { color: var(--color-primary); text-decoration: none; }
a:hover { text-decoration: underline; }
.text-subdued { color: var(--color-subdued); }
.text-xs { font-size: var(--text-xs); line-height: var(--line-height-xs); }
.text-s  { font-size: var(--text-s);  line-height: var(--line-height-s); }
.text-m  { font-size: var(--text-m);  line-height: var(--line-height-m); }
.text-mono { font-family: var(--font-mono); font-size: var(--text-xs); }
.text-number { font-variant-numeric: tabular-nums; }
.text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.page-header { background: var(--color-empty-shade); border-bottom: var(--border-thin); padding: var(--space-l) 0; }
.page-header-inner { max-width: var(--page-max-width); margin: 0 auto; padding: 0 var(--space-l); }
.page-header h1 { font-size: var(--text-l); font-weight: var(--font-weight-semibold); color: var(--color-ink); }
.breadcrumb { font-size: var(--text-xs); color: var(--color-subdued); margin-bottom: var(--space-xs); }
.breadcrumb a { color: var(--color-primary); }
.page-body { max-width: var(--page-max-width); margin: 0 auto; padding: var(--space-l); }
.panel { background: var(--color-empty-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-l); }
.panel + .panel { margin-top: var(--space-l); }
.panel--no-padding { padding: 0; }
.panel--shadow { border: none; box-shadow: var(--shadow-s); }
.panel--subdued { background: var(--color-lightest-shade); }
.panel-title { font-size: var(--text-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: .06em; color: var(--color-subdued); margin-bottom: var(--space-m); }
.stat-row { display: grid; gap: var(--space-m); grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); margin-bottom: var(--space-l); }
.stat-card { background: var(--color-empty-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-m) var(--space-l); }
.stat-card__label { font-size: var(--text-xs); color: var(--color-subdued); margin-bottom: var(--space-xs); text-transform: uppercase; letter-spacing: .05em; font-weight: var(--font-weight-semibold); }
.stat-card__value { font-size: var(--text-xl); font-weight: var(--font-weight-semibold); color: var(--color-ink); font-variant-numeric: tabular-nums; line-height: 1; }
.stat-card__description { font-size: var(--text-xs); color: var(--color-subdued); margin-top: var(--space-xs); }
.badge { display: inline-flex; align-items: center; font-size: var(--text-xs); font-weight: var(--font-weight-semibold); padding: 2px var(--space-s); border-radius: var(--border-radius); line-height: 1.5; }
.badge--default { background: var(--color-lightest-shade); color: var(--color-subdued); border: var(--border-thin); }
.badge--primary { background: var(--color-primary-bg); color: var(--color-primary); }
.badge--success { background: var(--color-success-bg); color: var(--color-success); }
.badge--warning { background: var(--color-warning-bg); color: var(--color-warning-text); }
.badge--danger  { background: var(--color-danger-bg); color: var(--color-danger); }
.callout { border-radius: var(--border-radius); padding: var(--space-m) var(--space-l); border-left: 4px solid; margin-bottom: var(--space-m); }
.callout--info    { background: var(--color-primary-bg); border-color: var(--color-primary); }
.callout--success { background: var(--color-success-bg); border-color: var(--color-success); }
.callout--warning { background: var(--color-warning-bg); border-color: var(--color-warning); }
.callout--danger  { background: var(--color-danger-bg);  border-color: var(--color-danger); }
.callout__title { font-size: var(--text-s); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-xs); color: var(--color-ink); }
.callout__body { font-size: var(--text-s); color: var(--color-paragraph); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--text-s); }
thead th { font-size: var(--text-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: .05em; color: var(--color-subdued); text-align: left; padding: var(--space-s) var(--space-m); border-bottom: var(--border-thick); white-space: nowrap; }
tbody td { padding: var(--space-m); border-bottom: var(--border-thin); vertical-align: middle; color: var(--color-paragraph); }
tbody tr:last-child td { border-bottom: none; }
tbody tr { transition: background .1s; }
tbody tr:hover { background: var(--color-lightest-shade); }
tbody tr.clickable { cursor: pointer; }
tbody tr.clickable:hover { background: var(--color-primary-bg); }
tbody tr.clickable:hover td.row-name { color: var(--color-primary); }
td.row-name { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-ink); transition: color .1s; }
td.row-arrow { color: var(--color-light-shade); font-size: 14px; width: 28px; text-align: right; transition: color .1s; }
tbody tr.clickable:hover td.row-arrow { color: var(--color-primary); }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-l); }
.grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: var(--space-l); }
@media (max-width: 768px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }
.flex-row { display: flex; align-items: center; gap: var(--space-m); }
.flex-row--apart { justify-content: space-between; }
.flex-row--wrap { flex-wrap: wrap; }
.separator { border: none; border-top: var(--border-thin); margin: var(--space-l) 0; }
pre { font-family: var(--font-mono); font-size: var(--text-xs); background: var(--color-lightest-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-m); overflow-x: auto; color: var(--color-ink); line-height: 1.6; white-space: pre-wrap; word-break: break-all; }
code { font-family: var(--font-mono); font-size: .9em; background: var(--color-lightest-shade); border: var(--border-thin); border-radius: 2px; padding: 1px var(--space-xs); color: var(--color-ink); }
pre code { background: none; border: none; padding: 0; font-size: inherit; }
hr { border: none; border-top: var(--border-thin); margin: var(--space-l) 0; }
.filter-bar { display: flex; gap: var(--space-s); padding: var(--space-m) var(--space-l); border-bottom: var(--border-thin); flex-wrap: wrap; }
.filter-btn { font-size: var(--text-xs); font-family: var(--font-body); padding: var(--space-xs) var(--space-m); border-radius: 20px; border: var(--border-thin); background: transparent; color: var(--color-subdued); cursor: pointer; transition: all .15s; font-weight: var(--font-weight-semibold); }
.filter-btn:hover, .filter-btn.active { background: var(--color-primary-bg); border-color: var(--color-primary); color: var(--color-primary); }
.chip-grid { display: flex; flex-wrap: wrap; gap: var(--space-s); padding: var(--space-l); }
.chip { font-family: var(--font-mono); font-size: var(--text-xs); padding: var(--space-xxs) var(--space-s); border-radius: var(--border-radius); border: var(--border-thin); color: var(--color-paragraph); background: var(--color-lightest-shade); text-decoration: none; display: inline-block; }
.chip:hover { border-color: var(--color-primary); color: var(--color-primary); text-decoration: none; }
.nav-footer { display: flex; justify-content: space-between; align-items: center; padding: var(--space-l); border-top: var(--border-thin); }
.btn { display: inline-block; font-size: var(--text-xs); font-family: var(--font-body); font-weight: var(--font-weight-semibold); padding: var(--space-xs) var(--space-m); border-radius: var(--border-radius); border: var(--border-thin); background: var(--color-empty-shade); color: var(--color-paragraph); text-decoration: none; cursor: pointer; transition: all .15s; }
.btn:hover { border-color: var(--color-primary); color: var(--color-primary); text-decoration: none; }
.progress-bar-wrap { height: 6px; background: var(--color-light-shade); border-radius: 3px; overflow: hidden; margin: var(--space-m) 0; }
.progress-bar-fill { height: 100%; display: flex; }
.col-header { padding: var(--space-m) var(--space-l); border-bottom: var(--border-thin); display: flex; align-items: center; gap: var(--space-s); font-size: var(--text-xs); font-weight: var(--font-weight-semibold); color: var(--color-subdued); text-transform: uppercase; letter-spacing: .05em; background: var(--color-lightest-shade); }
.empty-col { display: flex; align-items: center; justify-content: center; padding: var(--space-xxl) var(--space-l); color: var(--color-subdued); font-size: var(--text-xs); }
"""

HEAD_LINKS = """  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Roboto+Mono:wght@400&display=swap" rel="stylesheet">"""

# ---------------------------------------------------------------------------
# Component sub-pages
# ---------------------------------------------------------------------------

def status_badge(slug):
    if slug in both_slugs:
        return '<span class="badge badge--primary">Both</span>'
    elif slug in ember_slugs:
        return '<span class="badge badge--warning">Ember only</span>'
    else:
        return '<span class="badge badge--success">React only</span>'

def render_col(label, files):
    out = f'<div class="panel panel--no-padding" style="overflow:hidden"><div class="col-header">{label}</div>'
    if not files:
        out += '<div class="empty-col">Not present in this library</div>'
    else:
        for fname, code in files:
            out += f'<div style="padding:var(--space-xs) var(--space-l);border-bottom:var(--border-thin);font-size:var(--text-xs);font-family:var(--font-mono);color:var(--color-subdued)">{html.escape(fname)}</div>'
            out += f'<pre style="border:none;border-radius:0;margin:0">{html.escape(code)}</pre>'
    return out + '</div>'

def make_page(slug, prev_slug, next_slug):
    ember_files = get_ember_files(slug)
    react_files  = get_react_files(slug)
    analysis     = analyze(slug, ember_files, react_files)
    both         = bool(ember_files) and bool(react_files)

    prev_link = f'<a href="{prev_slug}.html" class="btn">← {prev_slug}</a>' if prev_slug else '<span></span>'
    next_link = f'<a href="{next_slug}.html" class="btn">{next_slug} →</a>' if next_slug else '<span></span>'

    cols = ''
    if both:
        cols = f'<div class="grid-2">{render_col("Ember (Glimmer)", ember_files)}{render_col("React (TSX)", react_files)}</div>'
    elif ember_files:
        cols = render_col("Ember (Glimmer)", ember_files)
    else:
        cols = render_col("React (TSX)", react_files)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{slug}: Luna Component Comparison</title>
{HEAD_LINKS}
  <style>{EUI_CSS}</style>
</head>
<body>
  <header class="page-header">
    <div class="page-header-inner">
      <div class="breadcrumb"><a href="../luna-components.html">Luna Components</a> / {slug}</div>
      <div style="display:flex;align-items:center;gap:var(--space-m);margin-top:var(--space-xs)">
        <h1 style="font-size:var(--text-l)">{slug}</h1>
        {status_badge(slug)}
      </div>
    </div>
  </header>
  <main class="page-body">
    <div class="callout callout--info" style="margin-bottom:var(--space-l)">
      <div class="callout__title">Analysis</div>
      <div class="callout__body">{analysis}</div>
    </div>
    {cols}
    <div class="nav-footer" style="margin-top:var(--space-l);padding-left:0;padding-right:0">
      {prev_link}
      <a href="../luna-components.html" class="btn">All Components</a>
      {next_link}
    </div>
  </main>
</body>
</html>"""

print(f"Generating {len(all_slugs)} component pages...")
for i, slug in enumerate(all_slugs):
    prev_slug = all_slugs[i-1] if i > 0 else None
    next_slug = all_slugs[i+1] if i < len(all_slugs)-1 else None
    (COMP_DIR / f"{slug}.html").write_text(make_page(slug, prev_slug, next_slug))
    print(f"  [{i+1}/{len(all_slugs)}] {slug}")

# ---------------------------------------------------------------------------
# luna-components.html
# ---------------------------------------------------------------------------

manifest = {
    "ember": sorted(ember_slugs), "react": sorted(react_slugs),
    "both": sorted(both_slugs), "ember_only": sorted(ember_only),
    "react_only": sorted(react_only), "all": all_slugs,
}
(OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

n_ember = len(ember_slugs)
n_react = len(react_slugs)
n_both  = len(both_slugs)
n_eo    = len(ember_only)
n_ro    = len(react_only)
total   = len(all_slugs)
pct     = round(n_both / total * 100)
pct_both  = round(n_both  / total * 100, 1)
pct_eo    = round(n_eo    / total * 100, 1)
pct_ro    = round(n_ro    / total * 100, 1)

# Get eval timestamp from most recently modified index.ts
ember_mtime = os.path.getmtime(str(EMBER_BASE / "index.ts"))
react_mtime = os.path.getmtime(str(REACT_BASE / "index.ts"))
eval_time = datetime.fromtimestamp(max(ember_mtime, react_mtime))
timestamp = eval_time.strftime("%B %d, %Y at %I:%M %p")

def chip(slug):
    return f'<a href="components/{slug}.html" class="chip">{slug}</a>'

ember_chips = "\n".join(chip(s) for s in sorted(ember_only))
react_chips = "\n".join(chip(s) for s in sorted(react_only))

def row(slug):
    in_e = slug in ember_slugs
    in_r = slug in react_slugs
    if in_e and in_r:
        badge = '<span class="badge badge--primary">Both</span>'
        status = 'both'
    elif in_e:
        badge = '<span class="badge badge--warning">Ember only</span>'
        status = 'ember-only'
    else:
        badge = '<span class="badge badge--success">React only</span>'
        status = 'react-only'
    href = f'components/{slug}.html'
    e_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--color-warning-text)"></span>' if in_e else '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--color-light-shade)"></span>'
    r_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--color-primary)"></span>' if in_r else '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--color-light-shade)"></span>'
    return (f'<tr class="clickable" data-status="{status}" onclick="location.href=\'{href}\'">'
            f'<td class="row-name">{slug}</td>'
            f'<td>{badge}</td>'
            f'<td style="text-align:center">{e_dot}</td>'
            f'<td style="text-align:center">{r_dot}</td>'
            f'<td class="row-arrow">→</td>'
            f'</tr>')

all_rows = "\n".join(row(s) for s in all_slugs)

dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Luna Design System: Ember vs React</title>
{HEAD_LINKS}
  <style>{EUI_CSS}</style>
</head>
<body>
  <header class="page-header">
    <div class="page-header-inner">
      <div class="breadcrumb"><a href="index.html">Projects</a> / Luna Design System</div>
      <h1 style="font-size:var(--text-l);margin-top:var(--space-xs)">Luna Design System: Ember vs React</h1>
      <p class="text-subdued" style="margin-top:var(--space-xs);font-size:var(--text-xs)">{timestamp}</p>
    </div>
  </header>

  <main class="page-body">

    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-card__label">Ember Components</div>
        <div class="stat-card__value">{n_ember}</div>
        <div class="stat-card__description">luna-core (Glimmer/GTS)</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">React Components</div>
        <div class="stat-card__value">{n_react}</div>
        <div class="stat-card__description">luna-react (TSX)</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">In Both</div>
        <div class="stat-card__value">{n_both}</div>
        <div class="stat-card__description">{pct}% parity</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Ember Only</div>
        <div class="stat-card__value">{n_eo}</div>
        <div class="stat-card__description">Missing from React</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">React Only</div>
        <div class="stat-card__value">{n_ro}</div>
        <div class="stat-card__description">Ahead of Ember</div>
      </div>
    </div>

    <div class="panel" style="margin-bottom:var(--space-l)">
      <div class="panel-title">Coverage</div>
      <div style="display:flex;gap:var(--space-l);margin-bottom:var(--space-m)">
        <span style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs)"><span style="width:10px;height:10px;border-radius:2px;background:var(--color-primary);display:inline-block"></span> Shared ({n_both})</span>
        <span style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs)"><span style="width:10px;height:10px;border-radius:2px;background:var(--color-warning);display:inline-block"></span> Ember only ({n_eo})</span>
        <span style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs)"><span style="width:10px;height:10px;border-radius:2px;background:var(--color-success);display:inline-block"></span> React only ({n_ro})</span>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-fill">
          <div style="width:{pct_both}%;background:var(--color-primary)"></div>
          <div style="width:{pct_eo}%;background:var(--color-warning)"></div>
          <div style="width:{pct_ro}%;background:var(--color-success)"></div>
        </div>
      </div>
    </div>

    <div style="margin-bottom:var(--space-l)">
      <div class="callout callout--success">
        <div class="callout__title">{pct}% parity on a corrected baseline</div>
        <div class="callout__body">Derived from <strong>index.ts exports</strong>, not directory listings. Previous counts were off because components in subdirectories (growl, modal-layout, navigation, skeleton, textarea, select-multiple) were missed.</div>
      </div>
      <div class="callout callout--danger">
        <div class="callout__title">{n_eo} components missing from React</div>
        <div class="callout__body">The remaining backlog includes <strong>format-markdown</strong>, <strong>search-highlight</strong>, <strong>select-date-range</strong>, <strong>portal</strong>, and <strong>animation</strong>, among others.</div>
      </div>
      <div class="callout callout--info">
        <div class="callout__title">tooltip: React is ahead</div>
        <div class="callout__body">React has a dedicated <strong>Tooltip</strong> component. Ember covers this via a tooltip modifier, not a component. React also exports <strong>Help</strong> separately, giving it two tooltip-style APIs.</div>
      </div>
      <div class="callout callout--warning" style="margin-bottom:0">
        <div class="callout__title">Name mismatches exist in shared components</div>
        <div class="callout__body">Some components match by slug but differ in exported name: <strong>SetupGrowl</strong> (Ember) vs <strong>Growl</strong> (React), <strong>ModalLayout</strong> (Ember) vs modal-layout dir (React). Click any component to see details.</div>
      </div>
    </div>

    <div class="grid-2" style="margin-bottom:var(--space-l)">
      <div class="panel panel--no-padding">
        <div class="col-header" style="background:var(--color-warning-bg);border-bottom:var(--border-thin)">
          Ember Only: Missing from React
          <span class="badge badge--warning" style="margin-left:auto">{n_eo}</span>
        </div>
        <div class="chip-grid">{ember_chips}</div>
      </div>
      <div class="panel panel--no-padding">
        <div class="col-header" style="background:var(--color-success-bg);border-bottom:var(--border-thin)">
          React Only: Ahead of Ember
          <span class="badge badge--success" style="margin-left:auto">{n_ro}</span>
        </div>
        <div class="chip-grid">{react_chips}</div>
      </div>
    </div>

    <div class="panel panel--no-padding">
      <div style="padding:var(--space-l);border-bottom:var(--border-thin);display:flex;align-items:center;justify-content:space-between">
        <h4>All Components</h4>
        <span class="badge badge--default">{total} total</span>
      </div>
      <div class="filter-bar">
        <button class="filter-btn active" onclick="filterTable('all',this)">All</button>
        <button class="filter-btn" onclick="filterTable('both',this)">In Both</button>
        <button class="filter-btn" onclick="filterTable('ember-only',this)">Ember Only</button>
        <button class="filter-btn" onclick="filterTable('react-only',this)">React Only</button>
      </div>
      <div class="table-wrap">
        <table id="component-table">
          <thead>
            <tr>
              <th>Component</th>
              <th>Status</th>
              <th style="text-align:center">Ember</th>
              <th style="text-align:center">React</th>
              <th style="width:28px"></th>
            </tr>
          </thead>
          <tbody>{all_rows}</tbody>
        </table>
      </div>
    </div>

  </main>

  <script>
    function filterTable(status, btn) {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#component-table tbody tr').forEach(row => {{
        row.style.display = (status === 'all' || row.dataset.status === status) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>"""

(OUT_DIR / "luna-components.html").write_text(dashboard)
print(f"\nluna-components.html written")
print(f"Summary: {n_ember} Ember, {n_react} React, {n_both} both, {n_eo} Ember-only, {n_ro} React-only")
