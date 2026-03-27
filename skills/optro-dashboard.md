---
description: The Optro Release Readiness Dashboard — a self-contained HTML dashboard template (index.html) that renders multi-facet production readiness eval reports. Accepts an optro-eval-report.json file and visualizes stability, performance, accessibility, i18n, security, observability, data privacy, brand compliance, and usability scores per module.
---

# Optro Release Readiness Dashboard

The full dashboard HTML lives at: `/Users/jcarpenter/.claude/projects/-Users-jcarpenter-Git-Repositories-auditboard-frontend/skills/optro-dashboard.html`

Or retrieve the source from the conversation where it was originally provided.

## What it does

- Loads an `optro-eval-report.json` produced by the eval-coordinator skill
- Renders a KPI row, radar chart, facet averages bar list, and sortable/filterable module table
- Each score cell has a hover tooltip with signals, deductions, top risks, and recommendations
- Clicking a module row opens a slide-in drill-down panel
- Supports a "Load Demo" button with built-in sample data for 8 modules

## Facets supported

stability, performance, accessibility, i18n, security, observability, data_privacy, brand_compliance, usability

## Verdict logic

- BLOCK: any facet < 25, or security/data_privacy < 50, or brand_compliance < 50 with AuditBoard references
- CONDITIONAL: composite < 50, or any facet < 50
- GO: composite >= 75 and no facet < 50

## Related skills

- `eval-coordinator.md` — orchestrates all facet evals and produces the JSON report
- `eval-accessibility.md` — accessibility facet eval
- `eval-i18n.md` — i18n facet eval
- `publish-dashboard.md` / `publish-dashboard-v2.md` — publish to GitHub Pages
