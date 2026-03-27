---
description: Re-evaluate auditboard-frontend a11y + i18n scores and republish the dashboard to GitHub Pages.
---

# Skill: Update A11y + i18n Dashboard

Use this skill to re-run accessibility and i18n evaluations against the 13 auditboard-frontend modules, refresh the MODULES data in the dashboard HTML, and redeploy to GitHub Pages.

## Prereqs

- Repo: `/Users/jcarpenter/Git Repositories/auditboard-frontend`
- Dashboard: `/Users/jcarpenter/Git Repositories/dashboard-projects/auditboard-a11y-i18n.html`
- If `/Users/jcarpenter/Git Repositories/dashboard-projects/` is missing: `git clone https://github.com/jcarpenter-optro/dashboard-projects.git "/Users/jcarpenter/Git Repositories/dashboard-projects"`
- Style guide: `~/.claude/skills/publish-dashboard.md`
- Eval skills: `~/.claude/skills/eval-accessibility.md`, `~/.claude/skills/eval-i18n.md`
- Coordinator: `~/.claude/skills/eval-coordinator.md`

---

## Phase 1: Re-evaluate all 13 modules

Run the `eval-coordinator` skill against the repo. It will:
1. Sample `.gjs`, `.gts`, and `.hbs` template files from each module's `routes/` and `components/` directories (up to 3,000 lines total per module)
2. Apply `eval-accessibility.md` and `eval-i18n.md` scoring rubrics to each module
3. Return scores, top_risks, and recommendations per module

The 13 modules to evaluate, with their source paths under `/apps/client/app/`:

| Module | Routes path | Components path |
|---|---|---|
| admin | `routes/admin/` | `components/admin/` |
| workspace | `routes/workspace/` | `components/workspace/` |
| site-configuration | `routes/site-configuration/` | `components/site-configuration/` |
| opsaudits | `routes/opsaudits/` | `components/opsaudits/` |
| assessments | `routes/assessments/` | `components/assessments/` |
| compliance | `routes/compliance/` | `components/compliance/` |
| hubs | `routes/hubs/` | `components/hubs/` |
| issues | `routes/issues/` | `components/issues/` |
| tasks | `routes/tasks/` | `components/tasks/` |
| resource-planner | `routes/resource-planner/` | `components/resource-planner/` |
| dashboard | `routes/dashboard/` | `components/dashboard/` |
| risks | `routes/risks/` | `components/risks/` |
| owner-dashboard | `routes/owner-dashboard/` | `components/owner-dashboard/` |

For each module, produce:
- `a11y`: integer score 0–100
- `i18n`: integer score 0–100
- `a11yRisks`: array of 2 strings (top_risks from eval-accessibility output)
- `a11yRecs`: array of 2 strings (recommendations from eval-accessibility output)
- `i18nRisks`: array of 1–2 strings (top_risks from eval-i18n output)
- `i18nRecs`: array of 1–2 strings (recommendations from eval-i18n output)
- `files`: integer file count (count `.gjs` + `.gts` + `.hbs` files in both directories)

---

## Phase 2: Refresh the dashboard HTML

> **Do not change style or layout.** Only update data. The CSS, HTML structure, icons, and visual layout of the deployed `auditboard-a11y-i18n.html` are the canonical versions. The only permitted change in this file is replacing the `const MODULES` array and updating the date.

Open `/Users/jcarpenter/Git Repositories/dashboard-projects/auditboard-a11y-i18n.html`.

Replace the entire `const MODULES = [...]` array in the `<script>` block with the fresh evaluation results from Phase 1.

Format each entry as:
```js
{ name:'<module>', files:<n>, a11y:<score>, i18n:<score>,
  a11yRisks:['<risk1>','<risk2>'],
  a11yRecs:['<rec1>','<rec2>'],
  i18nRisks:['<risk1>'],
  i18nRecs:['<rec1>'] },
```

**Rules for the content:**
- No em dashes (—) anywhere in strings. Use ": " or "; " instead.
- All stats (avg scores, module count, needs-attention count) are derived programmatically from the MODULES array. Never hardcode them.
- Update the timestamp in the page header subtitle to today's date.
- Do NOT include a Composite score column in the table. The table has exactly these columns: Module, Files, A11y Score, i18n Score, and the expand button column.
- Do NOT include a `composite()` helper function. "Needs Attention" count uses `m.a11y < 75 || m.i18n < 75`. Filtering and row band use `scoreBand(Math.min(m.a11y, m.i18n))`. Default sort is `a11y` descending.

**Rules for the CSS/HTML (apply publish-dashboard.md style guide exactly):**
- `<style>` block must contain the full EUI token set from publish-dashboard.md verbatim
- `--page-max-width: 1200px`
- All media query breakpoints at 768px
- `.panel` has `padding: var(--space-l)` by default; table panel uses class `panel--no-padding`
- Page structure follows the template: `.page-header` > breadcrumb + h1 + subtitle > `.page-body` > stat-row + callouts + panel

**Update the two callout boxes** (strongest patterns / top cross-cutting gaps) to reflect any patterns that changed across the new evaluation results. Base these on the actual new scores and risks — do not copy the old text verbatim if the findings have shifted.

---

## Phase 3: Deploy

```bash
cd "/Users/jcarpenter/Git Repositories/dashboard-projects"
git add auditboard-a11y-i18n.html
git commit -m "chore: refresh a11y + i18n scores $(date +%Y-%m-%d)"
git push origin main
```

GitHub Pages deploys automatically within ~60 seconds.

Confirm success by reporting:
- How many modules changed score vs. the prior run
- The new avg a11y and avg i18n scores
- The live URL: https://jcarpenter-optro.github.io/dashboard-projects/auditboard-a11y-i18n.html
