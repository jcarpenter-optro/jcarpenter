---
description: Re-scan the auditboard-frontend repo for Luna design token adoption and republish the luna-module-scores.html dashboard to GitHub Pages.
---

# Update Tokens Skill

Use this skill when asked to refresh, re-run, or update the Luna Token Adoption dashboard.

## What this skill does

Runs `~/jcarpenter/scripts/luna-module-audit.py` against the current state of the repo, writes the updated HTML report to the GitHub Pages working copy, and pushes it live. No manual steps required.

## Prerequisites

- **Repo root:** `/Users/jcarpenter/Git Repositories/auditboard-frontend`
- **Scanner:** `~/jcarpenter/scripts/luna-module-audit.py` (Python 3, at `/usr/bin/python3`)
- **GitHub Pages working copy:** `~/jcarpenter/`
- **Live URL:** https://jcarpenter-optro.github.io/jcarpenter/luna-module-scores.html

If `~/jcarpenter/` does not exist, clone it first:
```bash
git clone https://github.com/jcarpenter-optro/jcarpenter.git ~/jcarpenter
```

## Steps

> **Do not change style or layout.** Only update data. The CSS, HTML structure, and layout of the deployed `luna-module-scores.html` are the canonical versions. Do not let the scanner overwrite the deployed file directly — that would overwrite any visual polish. Instead, use the JSON output to update only the data sections.

### 1. Run the scanner to JSON

```bash
cd "/Users/jcarpenter/Git Repositories/auditboard-frontend"
/usr/bin/python3 ~/jcarpenter/scripts/luna-module-audit.py --out ~/jcarpenter/luna-module-scores.json --format json
```

If the script does not support `--format json`, run it to a temp file and extract the data:

```bash
/usr/bin/python3 ~/jcarpenter/scripts/luna-module-audit.py --out /tmp/luna-scores-fresh.html
```

Then read the fresh scores from stdout or the JSON sidecar file.

Print the per-module results so the user can see what changed.

### 2. Update data in the existing luna-module-scores.html

Open `~/jcarpenter/luna-module-scores.html`. Update **only** these sections — touch nothing else:

1. **Embedded JSON data**: the `const DATA = {...}` or equivalent object in the `<script>` block
2. **Summary stat values**: overall score, total violations, token usages, files scanned
3. **Generated date**: update the subtitle timestamp to today

Do **not** touch: `<style>`, page layout, heading structure, panel structure, or any visual element.

### 3. Commit and push

```bash
cd ~/jcarpenter
git add luna-module-scores.html luna-module-scores.json
git commit -m "chore: refresh Luna token adoption scores"
git push
```

### 4. Confirm

Tell the user the dashboard has been updated and share the live URL:
https://jcarpenter-optro.github.io/jcarpenter/luna-module-scores.html

---

## How the scanner works

### Token maps

Parsed from five CSS files, each containing `--luna-*` custom property declarations:

| File | Category | Properties scanned |
|------|----------|--------------------|
| `color.css` | color | `color`, `background-color`, `background`, `border-color`, `box-shadow`, `fill`, `stroke`, etc. |
| `space.css` + `size.css` | space (merged) | `margin`, `padding`, `gap`, `width`, `height`, `top`, `left`, etc. |
| `radius.css` | radius | `border-radius` and longhand variants |
| `typography.css` | typography | `font-size` |

Token values are normalized (hex shorthand expanded, whitespace stripped) and stored in reverse maps: `value -> [--luna-token-name, ...]`.

### Violation detection

For each `.css` / `.scss` file, the scanner:
1. Strips block comments and `url()` expressions
2. Splits on `;` to get declarations
3. Finds the first `:` at depth 0 to separate property from value
4. Skips CSS custom properties (`--*`) and SCSS variables (`$*`)
5. Only scans properties in the relevant category set (property-aware: `0` is a violation in `margin` but not `z-index`)
6. Counts `var(--luna-*)` references as token usages
7. Counts raw values that match a token map entry as violations

### Score formula

```
score = round(token_usages / (token_usages + violations) * 100)
```

If `token_usages + violations == 0` (no scannable declarations found), the module scores 100 with a note "No scannable CSS".

### Grades

| Score | Grade |
|-------|-------|
| 80–100 | A |
| 65–79 | B |
| 50–64 | C |
| 35–49 | D |
| 0–34 | F |

### Modules scanned

| Name | Directory |
|------|-----------|
| admin | `apps/client/app/components/module-admin` |
| opsaudits | `apps/client/app/components/module-opsaudits` |
| assessments | `apps/client/app/components/module-assessments` |
| compliance | `apps/client/app/components/module-compliance-assessments` |
| hubs | `apps/client/app/components/manage-hub` |
| issues | `apps/client/app/components/module-issues` |
| tasks | `apps/client/app/components/module-tasks` |
| resource-planner | `apps/client/app/components/module-resource-planner` |
| dashboard | `apps/client/app/components/module-dashboard` |
| risks | `apps/client/app/components/module-risks` |
| owner-dashboard | `apps/client/app/components/owner-dashboard` |

---

## Troubleshooting

**Python not found:** Use `/usr/bin/python3` explicitly. `node` is not available in the shell PATH.

**Token file missing:** If a Luna token CSS file doesn't exist, that category is skipped silently. Check that `libraries/luna-tokens/package/src/styles/` contains `color.css`, `space.css`, `size.css`, `radius.css`, `typography.css`.

**Module directory not found:** The scanner skips missing directories. If a module scores unexpectedly at 100% with 0 files, verify the directory path in `MODULES` in `~/jcarpenter/scripts/luna-module-audit.py`.

**JS broken after editing the Python script:** All `\n` inside the Python f-string that generates JS must be written as `\\n`. This applies everywhere: regex literals (`/\\n/g`), string values (`'line one;\\nline two;'`), etc. A bare `\n` in a Python f-string becomes a real newline in the output, breaking JS string literals and regex literals silently — the entire script block fails to parse and no click handlers work.
