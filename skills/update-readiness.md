---
description: Refresh the Release Readiness dashboard by merging current data from luna-module-scores.json and auditboard-a11y-i18n.html. Run this AFTER update-tokens and update-a11y have already committed their output.
---

# UPDATE_READINESS Skill

Use this skill when asked to refresh or republish the Release Readiness dashboard. This skill does **not** re-evaluate any code. It reads the already-updated output of the other dashboards and merges it.

---

## What this dashboard is

A combined view of A11y, i18n, and Luna token adoption scores per module. Each score cell is clickable and opens a lightbox with facet-specific risks, recommendations, and a Claude Code prompt.

- **File:** `~/dashboard-projects/release-readiness.html`
- **Live URL:** https://jcarpenter-optro.github.io/dashboard-projects/release-readiness.html

---

## Prerequisites

The following files must already reflect the latest data before running this skill:

| Source | Updated by |
|---|---|
| `~/dashboard-projects/luna-module-scores.json` | `update-tokens` skill |
| `~/dashboard-projects/auditboard-a11y-i18n.html` | `update-a11y` skill |

If either file is stale, run the corresponding skill first.

---

## Steps

### Step 1: Read token data from luna-module-scores.json

```bash
cat ~/dashboard-projects/luna-module-scores.json
```

For each module in the JSON, note: `name`, `score`, `violations`, `css_files`, `token_usages`, `by_cat`, `top_files`.

### Step 2: Extract a11y and i18n data from auditboard-a11y-i18n.html

Read the `const MODULES = [...]` array from the `<script>` block in `~/dashboard-projects/auditboard-a11y-i18n.html`.

For each module, collect: `name`, `a11y`, `i18n`, `a11yRisks`, `a11yRecs`, `i18nRisks`, `i18nRecs`.

The 13 a11y modules are: admin, workspace, site-configuration, opsaudits, assessments, compliance, hubs, issues, tasks, resource-planner, dashboard, risks, owner-dashboard.

The 11 token modules are all of the above except workspace and site-configuration. Set `tokens: null` for those two.

### Step 3: Rebuild the const MODULES array

Open `~/dashboard-projects/release-readiness.html`. Find the `const MODULES = [` block in the `<script>` section. Replace the entire array (from `const MODULES = [` through the closing `];`) with the freshly merged data, using this format per entry:

```js
{ name:'<name>', display:'<Display Name>',
  a11y:<score>, i18n:<score>,
  a11yRisks:['<risk1>','<risk2>'],
  a11yRecs:['<rec1>','<rec2>'],
  i18nRisks:['<risk1>'],
  i18nRecs:['<rec1>'],
  tokens:{ score:<n>, violations:<n>, css_files:<n>, token_usages:<n>,
    by_cat:{color:<n>,space:<n>,radius:<n>,typography:<n>},
    top_files:[{path:'<path>',violations:<n>}, ...]
  }
},
```

For modules with no token data, use `tokens: null`.

**Display name mapping** (slug to title case):
- admin: Admin
- workspace: Workspace
- site-configuration: Site Configuration
- opsaudits: Ops Audits
- assessments: Assessments
- compliance: Compliance
- hubs: Hubs
- issues: Issues
- tasks: Tasks
- resource-planner: Resource Planner
- dashboard: Dashboard
- risks: Risks
- owner-dashboard: Owner Dashboard

### Step 4: Update the date

In the `<header>` subtitle of `release-readiness.html`, update the "Generated YYYY-MM-DD" date to today.

### Step 5: Rules

- **Do not change style or layout.** Only update the `const MODULES = [...]` array and the date. The CSS, HTML structure, lightbox code, and all rendering functions are the canonical versions. Touch nothing else.
- No em dashes anywhere in string values. Use ": " or "; " instead.
- All stat card values (avg scores, modules at risk) are derived programmatically from the MODULES array. Never hardcode them.

### Step 6: Commit and push

```bash
cd ~/dashboard-projects
git add release-readiness.html
git commit -m "chore: refresh Release Readiness scores $(date +%Y-%m-%d)"
git push origin main
```

---

## Confirm

Report:
- How many modules changed any score vs. the prior run
- New avg A11y, avg i18n, avg tokens
- Live URL: https://jcarpenter-optro.github.io/dashboard-projects/release-readiness.html
