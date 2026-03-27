---
description: Refresh and republish all four project dashboards on Jeff Carpenter's GitHub Pages site. Orchestrates update-ember-react, update-tokens, and the a11y + i18n eval-coordinator in parallel, then update-readiness sequentially last.
---

# UPDATE_ALL Skill

Use this skill when asked to "update all dashboards", "refresh everything", or "republish all reports."

---

## What this skill does

Runs the first three dashboard update workflows in parallel, waits for all three to complete, then runs the Release Readiness dashboard last so it can read from their fresh output.

| Dashboard | Skill | Live URL |
|---|---|---|
| Release Readiness | `update-readiness.md` | `.../release-readiness.html` |
| Luna Design System: Ember vs React | `update-ember-react.md` | `.../luna-components.html` |
| Luna Token Adoption: Module Scores | `update-tokens.md` | `.../luna-module-scores.html` |
| AuditBoard: A11y + i18n Audit | `eval-coordinator.md` | `.../auditboard-a11y-i18n.html` |

Base URL: https://jcarpenter-optro.github.io/jcarpenter/

---

## Prerequisites

Pull the latest source before launching any updates:

```bash
cd "/Users/jcarpenter/Git Repositories/auditboard-frontend"
git pull origin develop
```

Also ensure `~/jcarpenter/` exists (clone if not):

```bash
git clone https://github.com/jcarpenter-optro/jcarpenter.git ~/jcarpenter
```

---

## Phase 1: launch the first three in parallel

Use the Agent tool to spawn three subagents simultaneously. Do not wait for one to finish before starting the next.

**Agent 1 — Ember vs React parity:**
> Follow the update-ember-react skill: run `~/jcarpenter/scripts/generate-luna-report.py`, check the summary, commit and push luna-components.html and all component sub-pages to `~/jcarpenter/`.

**Agent 2 — Luna token scores:**
> Follow the update-tokens skill: run `~/jcarpenter/scripts/luna-module-audit.py --out ~/jcarpenter/luna-module-scores.html` from the auditboard-frontend repo root, then commit and push luna-module-scores.html and luna-module-scores.json to `~/jcarpenter/`.

**Agent 3 — A11y + i18n audit:**
> Follow the eval-coordinator skill: evaluate the a11y and i18n facets for each module, write `auditboard-a11y-i18n-report.json`, generate `auditboard-a11y-i18n.html` using the optro-dashboard template, then commit and push to `~/jcarpenter/`.

---

## Notes on Agent 3

The A11y + i18n audit is significantly slower than the other two — it reads source files and generates AI-driven analysis per module. Agents 1 and 2 will finish first. Wait for all three before proceeding.

---

## Phase 2: update Release Readiness (after all three are done)

Only after Agents 1, 2, and 3 have all committed their output, follow the `update-readiness` skill to merge the fresh data from `luna-module-scores.json` and `auditboard-a11y-i18n.html` into `release-readiness.html` and push.

This step must run last. Running it before the others would pull stale data from their previous run.

---

## After all four complete

Report a summary table showing which dashboards were updated, any changes in key stats (e.g. component counts, module scores), and the base URL. Flag any agent that failed or produced unexpected output.
