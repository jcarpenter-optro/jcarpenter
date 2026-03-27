---
description: Re-evaluate the Ember vs React Luna component parity dashboard and publish updated results to GitHub Pages. Covers source-of-truth rules, known exceptions, and the full regenerate-and-deploy workflow.
---

# UPDATE_EMBER_REACT Skill

Use this skill when asked to refresh, regenerate, or republish the Luna Design System: Ember vs React dashboard.

---

## What this dashboard is

A component parity report comparing:
- **Ember:** `libraries/luna-core/package/src` (Glimmer `.gts` components)
- **React:** `libraries/luna-react/package/src` (TSX components)

Published at: https://jcarpenter-optro.github.io/dashboard-projects/luna-components.html
Generator script: `~/dashboard-projects/scripts/generate-luna-report.py`
Output directory: `~/dashboard-projects/` (GitHub Pages working copy of `jcarpenter-optro/dashboard-projects`)

If `~/dashboard-projects/` does not exist:
```bash
git clone https://github.com/jcarpenter-optro/dashboard-projects.git ~/dashboard-projects
```

If `~/dashboard-projects/scripts/generate-luna-report.py` does not exist, clone the repo first (`git clone https://github.com/jcarpenter-optro/dashboard-projects.git ~/dashboard-projects`) — the script lives at `scripts/generate-luna-report.py` in that repo.

---

## Source-of-truth rules

These rules were established after discovering systematic errors in an earlier directory-based analysis. Follow them exactly.

### 1. Use index.ts exports, not directory listings

Parse `src/index.ts` in each library to discover components. A file in `components/` that is not exported from `index.ts` is internal — do not count it.

```python
# Correct approach
parse_exports(EMBER_BASE / "index.ts")   # → list of (export_name, path) tuples
parse_exports(REACT_BASE / "index.ts")

# Wrong approach
list(EMBER_BASE.glob("components/**/*.gts"))  # includes internals, sub-components, tests
```

### 2. Slug canonicalization: use the first path segment after `components/`

`components/button/index.ts` → slug `button`
`components/select-date/calendar.ts` → slug `select-date` (not `calendar`)

Exception: apply `EMBER_PATH_RENAMES` before this rule (see below).

### 3. Deduplicate by slug

If multiple exports map to the same slug (e.g. `ButtonWithMenu` and `ButtonWithMenuButton` both under `button-with-menu`), keep only the first. Each slug = one logical component.

---

## Known exceptions to maintain

These are encoded in the generator script. If you reconstruct the script, carry them forward. If the libraries add new components under unusual paths, extend these dicts — do not delete existing entries.

### EMBER_EXCLUDE

Ember exports some non-component utilities alongside components. Exclude these slugs/paths:

```python
EMBER_EXCLUDE = {
    'fake-input', 'fake-textarea', 'fake-select', 'fake-select-multiple',  # test fakes
    'testing/render-test-container',    # test utility
    'util/cache-state',                 # internal util
    'util/tablist-manager',             # internal util
    'setup/announcer',                  # internal sub-component
}
```

### EMBER_PATH_RENAMES

Some Ember components live in subdirectories that do not match their canonical slug. Map them explicitly:

```python
EMBER_PATH_RENAMES = {
    'layout/modal':       'modal-layout',   # exported as ModalLayout, not Modal
    'layout/navigation':  'navigation',
    'setup/growl':        'growl',
    'skeleton/text':      'skeleton',
    # Sub-components to suppress entirely (None = skip):
    'tablist/panel':           None,
    'help/trigger':            None,
    'select-date/calendar':    None,
    'checkbox/input':          None,
    'checkbox/element':        None,
    'button-with-menu/menu':   None,
    'button-with-menu/button': None,
    'button-with-popup/button': None,
    'select-recurrence/const': None,
    'layout/modal/dialog':     None,
    'layout/navigation/link':  None,
}
```

### SEMANTIC_NOTES

Some components have known name mismatches or cross-library quirks. These are hand-curated analysis strings used on each component's sub-page. Always check if the slug being analyzed is in this dict before generating an automated analysis:

- `tooltip`: Ember uses a modifier, not a component. React has both Tooltip and Help.
- `help`: Both have Help. React additionally has Tooltip as a separate export.
- `growl`: Same concept, different naming: Ember `SetupGrowl` vs React `Growl`.
- `modal-layout`: Ember path is `layout/modal.gts`; React has a standalone directory.
- `navigation`: Ember path is `layout/navigation.gts`; React has a standalone directory.
- `skeleton`: Ember exports `SkeletonText`; React exports both `Skeleton` and `SkeletonText`.

---

## Re-evaluation steps

> **Do not change style or layout.** Only update data. The HTML structure, CSS, icons, and alignment in the deployed files are the canonical versions. Do not regenerate the full HTML from scratch — that would overwrite all visual polish. Instead, update only the data-driven sections of the existing files.

### Step 1: Verify source files are current

```bash
cd "/Users/jcarpenter/Git Repositories/auditboard-frontend"
git pull origin develop
```

### Step 2: Parse the source to get fresh component data

Run the generator script **for its data output only** — capture the summary and component list, but do not let it overwrite the deployed HTML:

```bash
python3 ~/dashboard-projects/scripts/generate-luna-report.py --dry-run 2>&1 | tail -5
```

If the script does not support `--dry-run`, run it into a temp file instead:

```bash
python3 ~/dashboard-projects/scripts/generate-luna-report.py --out /tmp/luna-fresh/
```

Collect from the output:
- Total Ember count, React count, shared count, Ember-only list, React-only list
- Per-component status (both / ember-only / react-only) and source files

### Step 3: Update data in the existing luna-components.html

Open `~/dashboard-projects/luna-components.html`. Update **only** these sections — touch nothing else:

1. **Stat card values**: the five `<div class="stat-card__value">` numbers (Ember, React, In Both, Ember Only, React Only)
2. **Legend counts**: the "(N)" numbers in the three legend `<span>` elements
3. **Progress bar widths**: the three `style="width:X%"` on bar segments
4. **Gap panel chips**: replace the `<div class="chip-grid">` contents inside each gap panel
5. **Table rows**: replace all `<tr data-status="...">` rows in `#component-table tbody`
6. **Page subtitle**: update the "Generated YYYY-MM-DD" date

Do **not** touch: `<style>`, icons, `.col-header` contents, grid layout, callout text, filter buttons, or table headers.

### Step 4: Update component sub-pages

Component sub-pages (`components/*.html`) contain actual source code that changes between runs. Regenerate them fresh, but ensure the output includes the Ember/React icons in every col-header (see Style section below). If the generator script does not include the icons, apply the batch icon patch after generating:

```python
import glob
EMBER_SVG = '<svg width="10" height="12" viewBox="0 0 14 16" fill="none" style="flex-shrink:0"><path d="M7 0.5C7 0.5 13 4.5 13 9.5C13 13 10.5 15.5 7 15.5C3.5 15.5 1 13 1 9.5C1 4.5 7 0.5 7 0.5Z" fill="#E04E39"/><path d="M7 6C7 6 10.5 8.5 10.5 11.5C10.5 13.5 8.8 15 7 15C5.2 15 3.5 13.5 3.5 11.5C3.5 8.5 7 6 7 6Z" fill="#FF8870"/></svg>'
REACT_SVG = '<svg width="12" height="12" viewBox="-50 -50 100 100" fill="none" style="flex-shrink:0"><circle r="9" fill="#61DAFB"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5" transform="rotate(60)"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5" transform="rotate(120)"/></svg>'
for f in glob.glob('~/dashboard-projects/components/*.html'):
    txt = open(f).read()
    txt = txt.replace('<div class="col-header">Ember (Glimmer)</div>', f'<div class="col-header">{EMBER_SVG}Ember (Glimmer)</div>')
    txt = txt.replace('<div class="col-header">React (TSX)</div>', f'<div class="col-header">{REACT_SVG}React (TSX)</div>')
    open(f, 'w').write(txt)
```

### Step 5: Sanity-check the numbers

Before publishing, verify the numbers are plausible:
- Ember count should be ~76 (rises if new components are added)
- React count should be ~70 (rises as migration progresses)
- React-only count should be low (3 or fewer) — if it is large, suspect a false positive and check EMBER_PATH_RENAMES

### Step 6: Commit and push

```bash
cd ~/dashboard-projects
git add luna-components.html components/
git commit -m "chore: refresh Ember vs React parity report"
git push origin main
```

GitHub Pages deploys within ~60 seconds.

---

## When to update the exceptions

| Situation | Action |
|---|---|
| New Ember component appears as false "React only" | Add entry to `EMBER_PATH_RENAMES` |
| New internal utility appears as a real component | Add slug to `EMBER_EXCLUDE` |
| A component has misleading name-match analysis | Add hand-curated entry to `SEMANTIC_NOTES` |
| A sub-component is being counted separately | Map its path to `None` in `EMBER_PATH_RENAMES` |

After any change to the exception dicts, re-run the generator and re-check the summary before pushing.

---

## Style

All generated HTML must follow the EUI style guide in `publish-dashboard.md`. The generator script has the full EUI CSS inline — do not simplify or replace it. Do not use em dashes anywhere in generated content.

### Ember and React icons

Every place the words "Ember" or "React" appear as a label (col-header, stat card label, legend item, filter button, table header) must be prefixed with the corresponding inline SVG icon. Use these exact strings:

**Ember flame icon** (use before any "Ember" label):
```html
<svg width="10" height="12" viewBox="0 0 14 16" fill="none" style="flex-shrink:0"><path d="M7 0.5C7 0.5 13 4.5 13 9.5C13 13 10.5 15.5 7 15.5C3.5 15.5 1 13 1 9.5C1 4.5 7 0.5 7 0.5Z" fill="#E04E39"/><path d="M7 6C7 6 10.5 8.5 10.5 11.5C10.5 13.5 8.8 15 7 15C5.2 15 3.5 13.5 3.5 11.5C3.5 8.5 7 6 7 6Z" fill="#FF8870"/></svg>
```

**React atom icon** (use before any "React" label):
```html
<svg width="12" height="12" viewBox="-50 -50 100 100" fill="none" style="flex-shrink:0"><circle r="9" fill="#61DAFB"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5" transform="rotate(60)"/><ellipse rx="47" ry="18" stroke="#61DAFB" stroke-width="5" transform="rotate(120)"/></svg>
```

For inline contexts (stat card labels, filter buttons, table headers) add `style="vertical-align:middle;margin-right:4px"` to the `<svg>` tag instead of `flex-shrink:0`.

Apply icons in these locations on the **main page** (`luna-components.html`):
- Stat card labels: "Ember Components", "Ember Only", "React Components", "React Only"
- Legend items: "Ember only (N)" and "React only (N)"
- Gap panel col-headers: "Ember Only: Missing from React" and "React Only: Ahead of Ember"
- Filter buttons: "Ember Only" and "React Only"
- Table headers: "Ember" and "React"

Apply icons in these locations on every **component sub-page** (`components/*.html`):
- Col-headers: `<div class="col-header">Ember (Glimmer)</div>` and `<div class="col-header">React (TSX)</div>`

### Gap panels alignment

The two gap panels (Ember Only / React Only) live in a `.grid-2` container. Add `align-items:start` to prevent the shorter panel from stretching to match the taller one:

```html
<div class="grid-2" style="margin-bottom:var(--space-l);align-items:start">
```
