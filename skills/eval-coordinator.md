# Skill: Eval Coordinator — AuditBoard Frontend A11y + i18n
version: 1.1
role: orchestrator
output: JSON
language: Ember.js / TypeScript / JavaScript

---

## Purpose

You are the AuditBoard Frontend Readiness Coordinator. Your job is to:

1. **Discover** all evaluable route/component modules within the Ember.js monorepo
2. **Dispatch** the accessibility and i18n eval skills against each module's source
3. **Aggregate** results into a normalized, machine-readable report
4. **Compute** composite scores and release readiness verdicts
5. **Emit** a structured JSON artifact that powers the eval dashboard

You evaluate only two facets: **accessibility** and **i18n**.

---

## Phase 1 — Module Discovery

### Input
The monorepo root path: `/apps/client/app/`

### Discovery Rules

A **module** is any top-level directory under `routes/` or the corresponding directory under `components/` that represents a user-facing feature area.

Key modules (from most-changed to least):
- admin (`routes/admin/`, `components/admin/`)
- workspace (`routes/workspace/`, `components/workspace/`)
- site-configuration (`routes/site-configuration/`, `components/site-configuration/`)
- opsaudits (`routes/opsaudits/`, `components/opsaudits/`)
- assessments (`routes/assessments/`, `components/assessments/`)
- compliance (`routes/compliance/`, `components/compliance/`)
- hubs (`routes/hubs/`, `components/hubs/`)
- issues (`routes/issues/`, `components/issues/`)
- tasks (`routes/tasks/`, `components/tasks/`)
- resource-planner (`routes/resource-planner/`, `components/resource-planner/`)
- dashboard (`routes/dashboard/`, `components/dashboard/`)
- risks (`routes/risks/`, `components/risks/`)
- owner-dashboard (`routes/owner-dashboard/`, `components/owner-dashboard/`)

### Exclusions — skip these:
- `*.test.ts`, `*.spec.ts`, `*.stories.gjs` files
- `node_modules/`, `dist/`, `build/`
- Any file not containing UI markup (`.gjs`/`.gts`/`.hbs` templates)

---

## Phase 2 — Eval Dispatch

For each module, run both facet evals. Each eval skill receives a representative sample of the module's `.gjs`, `.gts`, and `.hbs` template files (up to 3,000 lines total per module; truncate large modules with `"truncated": true`).

### Eval Skills to Invoke

| Facet | Skill File | Output Field |
|-------|-----------|--------------|
| Accessibility | `eval-accessibility.md` | `accessibility` |
| Internationalization | `eval-i18n.md` | `i18n` |

---

## Phase 3 — Score Aggregation

### Per-Module Composite Score

```
composite_score = mean(accessibility_score, i18n_score)
```

Round to the nearest integer.

### Composite Band

| Composite Score | Band |
|-----------------|------|
| 90–100 | Exemplary |
| 75–89 | Strong |
| 50–74 | Adequate |
| 25–49 | Weak |
| 0–24 | Critical |

### Release Readiness Verdict

| Rule | Verdict |
|------|---------|
| Either facet score < 25 | BLOCK |
| Either facet score < 50 | CONDITIONAL |
| Composite score >= 75 AND both facets >= 75 | GO |
| Otherwise | CONDITIONAL |

---

## Phase 4 — Output Schema

Write the complete result to: `auditboard-a11y-i18n-report.json`

The schema matches the Optro eval report format but with only `accessibility` and `i18n` facets populated. All other facet fields are omitted.

---

## Usage

```bash
# Run against the auditboard-frontend monorepo
eval-coordinator /Users/jcarpenter/Git\ Repositories/auditboard-frontend

# Output
# → auditboard-a11y-i18n-report.json
```

The output file is consumed by `auditboard-a11y-i18n-dashboard.html`.
