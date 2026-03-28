#!/usr/bin/env python3
"""
luna-module-audit.py
Scans module CSS/SCSS files for hardcoded values that match Luna design tokens.
Scores each module 0-100: token_usages / (token_usages + violations) * 100

Usage: python3 bin/luna-module-audit.py [--out path/to/report.html]
"""

import os, re, sys, json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path.cwd()

TOKEN_FILES = {
    "color":      REPO_ROOT / "libraries/luna-tokens/package/src/styles/color.css",
    "space":      REPO_ROOT / "libraries/luna-tokens/package/src/styles/space.css",
    "size":       REPO_ROOT / "libraries/luna-tokens/package/src/styles/size.css",
    "radius":     REPO_ROOT / "libraries/luna-tokens/package/src/styles/radius.css",
    "typography": REPO_ROOT / "libraries/luna-tokens/package/src/styles/typography.css",
}

MODULES = [
    {"name": "Dashboard (module-dashboard, owner-dashboard)",
     "dirs": ["apps/client/app/components/module-dashboard",
              "apps/client/app/components/owner-dashboard"],
     "description": ""},
    {"name": "Controls (module-assessments, manage-hub, module-resource-planner)",
     "dirs": ["apps/client/app/components/module-assessments",
              "apps/client/app/components/manage-hub",
              "apps/client/app/components/module-resource-planner"],
     "description": ""},
    {"name": "Risks (module-risks)",
     "dirs": ["apps/client/app/components/module-risks"],
     "description": ""},
    {"name": "CrossComply (module-compliance-assessments)",
     "dirs": ["apps/client/app/components/module-compliance-assessments"],
     "description": ""},
    {"name": "Issues (module-issues)",
     "dirs": ["apps/client/app/components/module-issues"],
     "description": ""},
    {"name": "OpsAudit (module-opsaudits)",
     "dirs": ["apps/client/app/components/module-opsaudits"],
     "description": ""},
    {"name": "WorkStream (module-tasks)",
     "dirs": ["apps/client/app/components/module-tasks"],
     "description": ""},
    {"name": "BCM (module-bcm)",
     "dirs": ["apps/client/app/components/module-bcm"],
     "description": ""},
    {"name": "Settings (module-admin, site-configuration)",
     "dirs": ["apps/client/app/components/module-admin",
              "apps/client/app/components/site-configuration"],
     "description": ""},
    {"name": "ESG (module-esg)",
     "dirs": ["apps/client/app/components/module-esg"],
     "description": ""},
    {"name": "TPRM (module-tprm)",
     "dirs": ["apps/client/app/components/module-tprm"],
     "description": ""},
    {"name": "Narratives (module-narratives)",
     "dirs": ["apps/client/app/components/module-narratives"],
     "description": ""},
    {"name": "RegComply (module-regulations, libraries/module-regulations)",
     "dirs": ["apps/client/app/components/module-regulations",
              "libraries/module-regulations"],
     "description": ""},
    {"name": "Exceptions (module-exceptions)",
     "dirs": ["apps/client/app/components/module-exceptions"],
     "description": ""},
    {"name": "Integrations (module-integrations)",
     "dirs": ["apps/client/app/components/module-integrations"],
     "description": ""},
    {"name": "Automations (module-automations)",
     "dirs": ["apps/client/app/components/module-automations"],
     "description": ""},
    {"name": "Inventory (module-inventory)",
     "dirs": ["apps/client/app/components/module-inventory"],
     "description": ""},
    {"name": "AI Governance (module-ai-governance)",
     "dirs": ["apps/client/app/components/module-ai-governance"],
     "description": ""},
    {"name": "Files (files)",
     "dirs": ["apps/client/app/components/files"],
     "description": ""},
    {"name": "Timesheets (module-timesheets)",
     "dirs": ["apps/client/app/components/module-timesheets"],
     "description": ""},
    {"name": "Automated Security Questionnaires (module-questionnaires)",
     "dirs": ["apps/client/app/components/module-questionnaires"],
     "description": ""},
    {"name": "ITRM / Cyber Risk (module-itrm)",
     "dirs": ["apps/client/app/components/module-itrm"],
     "description": ""},
    {"name": "Other (shared, application-chrome)",
     "dirs": ["apps/client/app/components/shared",
              "apps/client/app/components/application-chrome"],
     "description": ""},
]

# Properties scanned per category — keeps detection context-aware
SPACE_PROPS = {
    "margin","margin-top","margin-right","margin-bottom","margin-left",
    "padding","padding-top","padding-right","padding-bottom","padding-left",
    "gap","row-gap","column-gap","grid-gap","grid-row-gap","grid-column-gap",
    "top","right","bottom","left","inset","inset-block","inset-inline",
    "width","height","min-width","max-width","min-height","max-height","flex-basis",
}
COLOR_PROPS = {
    "color","background-color","background","border-color",
    "border-top-color","border-right-color","border-bottom-color","border-left-color",
    "outline-color","fill","stroke","text-decoration-color",
    "caret-color","accent-color","border","outline","column-rule-color",
    "box-shadow","text-shadow",
}
RADIUS_PROPS = {
    "border-radius","border-top-left-radius","border-top-right-radius",
    "border-bottom-left-radius","border-bottom-right-radius",
    "border-start-start-radius","border-start-end-radius",
    "border-end-start-radius","border-end-end-radius",
}
TYPO_PROPS = {"font-size"}
ALL_SCANNABLE = SPACE_PROPS | COLOR_PROPS | RADIUS_PROPS | TYPO_PROPS

# ── Token parsing ─────────────────────────────────────────────────────────────

def normalize_hex(h):
    h = h.lower().strip()
    if re.match(r'^#[0-9a-f]{3}$', h):
        return '#' + h[1]*2 + h[2]*2 + h[3]*2
    return h

def parse_token_file(path):
    """Return dict: normalized_value -> [token_name, ...]"""
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8")
    result = {}
    for m in re.finditer(r'--luna-([\w-]+)\s*:\s*([^;]+);', content):
        name = f"--luna-{m.group(1)}"
        raw  = re.sub(r'/\*.*?\*/', '', m.group(2)).strip()
        if not raw or 'var(' in raw:
            continue
        value = normalize_hex(raw) if raw.startswith('#') else raw
        result.setdefault(value, []).append(name)
    return result

def build_token_maps():
    color  = parse_token_file(TOKEN_FILES["color"])
    space  = parse_token_file(TOKEN_FILES["space"])
    size   = parse_token_file(TOKEN_FILES["size"])
    radius = parse_token_file(TOKEN_FILES["radius"])
    typo   = parse_token_file(TOKEN_FILES["typography"])

    # Color: hex values only
    hex_colors = {v: t for v, t in color.items() if v.startswith('#')}
    # Space: merge space + size (identical scale)
    space_size = {**space, **size}
    # Typography: font-size-* tokens only
    font_sizes = {v: t for v, t in typo.items() if any('font-size' in n for n in t)}

    return {"color": hex_colors, "space": space_size, "radius": radius, "typography": font_sizes}

# ── CSS scanning ──────────────────────────────────────────────────────────────

def strip_var_expressions(s):
    """Iteratively remove var() calls (handles nesting)."""
    prev = None
    while s != prev:
        prev = s
        s = re.sub(r'var\([^()]*\)', ' ', s)
    return s

LUNA_VAR_RE = re.compile(r'var\(--luna-[^)]+\)')

def count_luna_vars(value):
    return len(LUNA_VAR_RE.findall(value))

def extract_atoms(value):
    s = re.sub(r'/\*.*?\*/', '', value)
    s = re.sub(r'url\([^)]*\)', ' ', s)
    s = strip_var_expressions(s)
    return [a for a in re.split(r'[\s,/]+', s) if a.strip()]

def count_color_violations(value, color_map):
    return sum(1 for a in extract_atoms(value) if normalize_hex(a) in color_map)

def count_literal_violations(value, token_map):
    return sum(1 for a in extract_atoms(value) if a in token_map)

def parse_declarations(content):
    """Yield (property, value) tuples from CSS/SCSS content."""
    # Strip block comments
    clean = re.sub(r'/\*[\s\S]*?\*/', '', content)
    for segment in clean.split(';'):
        # Find first colon outside parentheses
        depth, colon = 0, -1
        for i, c in enumerate(segment):
            if c == '(':   depth += 1
            elif c == ')': depth -= 1
            elif c == ':' and depth == 0:
                colon = i
                break
        if colon == -1:
            continue
        prop  = re.sub(r'[\s{}]', '', segment[:colon]).lower()
        value = segment[colon+1:].strip()
        if not prop or not value:
            continue
        if prop.startswith('--') or prop.startswith('$'):
            continue
        yield prop, value

def scan_file(filepath, maps):
    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"token_usages": 0, "violations": 0, "by_cat": {k: 0 for k in ("color","space","radius","typography")}}

    by_cat = {"color": 0, "space": 0, "radius": 0, "typography": 0}
    token_usages = violations = 0

    for prop, value in parse_declarations(content):
        if prop not in ALL_SCANNABLE:
            continue
        token_usages += count_luna_vars(value)
        if prop in COLOR_PROPS:
            v = count_color_violations(value, maps["color"])
            violations += v; by_cat["color"] += v
        if prop in SPACE_PROPS:
            v = count_literal_violations(value, maps["space"])
            violations += v; by_cat["space"] += v
        if prop in RADIUS_PROPS:
            v = count_literal_violations(value, maps["radius"])
            violations += v; by_cat["radius"] += v
        if prop in TYPO_PROPS:
            v = count_literal_violations(value, maps["typography"])
            violations += v; by_cat["typography"] += v

    return {"token_usages": token_usages, "violations": violations, "by_cat": by_cat}

def find_css_files(directory):
    d = Path(directory)
    if not d.exists():
        return []
    return [p for p in d.rglob("*") if p.suffix in (".css", ".scss") and p.is_file()]

def scan_module(mod, maps):
    css_files = []
    for d in mod["dirs"]:
        css_files.extend(find_css_files(REPO_ROOT / d))

    by_cat = {"color": 0, "space": 0, "radius": 0, "typography": 0}
    token_usages = violations = 0
    top_files = []

    for fp in css_files:
        r = scan_file(fp, maps)
        token_usages += r["token_usages"]
        violations   += r["violations"]
        for k in by_cat:
            by_cat[k] += r["by_cat"][k]
        if r["violations"] > 0 or r["token_usages"] > 0:
            top_files.append({
                "path":        str(fp.relative_to(REPO_ROOT)),
                "violations":  r["violations"],
                "token_usages": r["token_usages"],
            })

    total = token_usages + violations
    score = 100 if total == 0 else round(token_usages / total * 100)
    grade = ("A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F")

    top_files.sort(key=lambda x: -x["violations"])

    return {
        **mod,
        "css_files":    len(css_files),
        "token_usages": token_usages,
        "violations":   violations,
        "by_cat":       by_cat,
        "score":        score,
        "grade":        grade,
        "exists":       any((REPO_ROOT / d).exists() for d in mod["dirs"]),
        "top_files":    top_files[:8],
    }

# ── HTML generation ───────────────────────────────────────────────────────────

def score_badge_class(s):
    if s >= 80: return "badge--success"
    if s >= 50: return "badge--warning"
    return "badge--danger"

def grade_badge_class(g):
    return {"A":"badge--success","B":"badge--success","C":"badge--warning","D":"badge--danger","F":"badge--danger"}.get(g,"badge--default")

def score_bar_color(s):
    if s >= 80: return "var(--color-success)"
    if s >= 50: return "var(--color-warning)"
    return "var(--color-danger)"

def score_text_color(s):
    if s >= 80: return "var(--color-success)"
    if s >= 50: return "var(--color-warning-text)"
    return "var(--color-danger)"

def cat_badges(by_cat):
    parts = []
    if by_cat["space"]:      parts.append(f'<span class="badge badge--warning">Space {by_cat["space"]:,}</span>')
    if by_cat["color"]:      parts.append(f'<span class="badge badge--danger">Color {by_cat["color"]:,}</span>')
    if by_cat["radius"]:     parts.append(f'<span class="badge badge--default">Radius {by_cat["radius"]:,}</span>')
    if by_cat["typography"]: parts.append(f'<span class="badge badge--primary">Type {by_cat["typography"]:,}</span>')
    return " ".join(parts) or '<span class="text-subdued text-xs">none detected</span>'

def generate_html(results, maps):
    sorted_r    = sorted(results, key=lambda r: -r["score"])
    total_viol  = sum(r["violations"] for r in results)
    total_uses  = sum(r["token_usages"] for r in results)
    total_files = sum(r["css_files"] for r in results)
    grand       = total_uses + total_viol
    overall     = 100 if grand == 0 else round(total_uses / grand * 100)

    cat_totals = {"color": 0, "space": 0, "radius": 0, "typography": 0}
    for r in results:
        for k in cat_totals:
            cat_totals[k] += r["by_cat"][k]

    cat_sum    = sum(cat_totals.values()) or 1
    space_pct  = round(cat_totals["space"]  / cat_sum * 100)
    color_pct  = round(cat_totals["color"]  / cat_sum * 100)
    radius_pct = round(cat_totals["radius"] / cat_sum * 100)
    typo_pct   = max(0, 100 - space_pct - color_pct - radius_pct)

    token_type_count = len(maps["color"]) + len(maps["space"]) + len(maps["radius"]) + len(maps["typography"])
    now   = datetime.now().strftime("%B %-d, %Y at %I:%M %p")
    best  = sorted_r[0]
    worst = max(results, key=lambda r: r["violations"])

    best_note = (f'{best["css_files"]} CSS files' if best["css_files"] > 0
                 else "no standalone CSS files (styles likely in templates)")

    # Serialize module data for embedding in JS (strip non-serialisable fields)
    js_data = json.dumps([{
        "name":         r["name"],
        "description":  r["description"],
        "score":        r["score"],
        "grade":        r["grade"],
        "css_files":    r["css_files"],
        "violations":   r["violations"],
        "token_usages": r["token_usages"],
        "by_cat":       r["by_cat"],
        "top_files":    r["top_files"],
        "dirs":         r.get("dirs", []),
    } for r in results], indent=2)

    # Build table rows — each row is clickable
    rows = []
    for i, mod in enumerate(sorted_r):
        score_band = "good" if mod["score"] >= 80 else "fair" if mod["score"] >= 50 else "poor"
        scannable  = mod["violations"] + mod["token_usages"]
        mod_name_js = mod["name"].replace("'", "\\'")
        display_name = mod["name"].split(" (")[0]
        subtitle = mod["name"][mod["name"].index("(")+1:-1] if "(" in mod["name"] else ""
        if scannable == 0:
            score_cell = '<span class="text-subdued text-xs">No scannable CSS</span>'
        else:
            score_cell = f'''<div style="display:flex;align-items:center;gap:var(--space-s);">
              <div style="height:6px;border-radius:3px;background:var(--color-light-shade);overflow:hidden;flex:1;min-width:80px;">
                <div style="height:100%;width:{mod["score"]}%;background:{score_bar_color(mod["score"])};border-radius:3px;"></div>
              </div>
              <span class="text-xs text-number" style="color:{score_text_color(mod["score"])};font-weight:600;min-width:32px;">{mod["score"]}%</span>
            </div>'''
        rows.append(f'''
    <tr data-score="{score_band}" onclick="openDrawer('{mod_name_js}')" style="cursor:pointer;">
      <td onclick="event.stopPropagation();openMI('{mod_name_js}')" style="cursor:pointer;" title="View module composition">
        <div style="font-weight:var(--font-weight-semibold);color:var(--color-ink);">{display_name}</div>
        <div style="margin-top:3px;font-size:calc(var(--text-xs) * 0.7);color:var(--color-subdued);font-family:var(--font-mono);font-weight:normal;">{subtitle}</div>
      </td>
      <td class="numeric text-xs text-subdued">{mod["css_files"]}</td>
      <td class="numeric"><span class="text-number" style="color:var(--color-danger);font-weight:var(--font-weight-semibold);">{mod["violations"]:,}</span></td>
      <td class="numeric"><span class="text-number" style="color:var(--color-success);">{mod["token_usages"]:,}</span></td>
      <td style="min-width:200px;">{score_cell}</td>
      <td style="text-align:center;"><span class="badge {grade_badge_class(mod["grade"])}">{mod["grade"]}</span></td>
      <td>{cat_badges(mod["by_cat"])}</td>
    </tr>''')

    rows_html = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Luna Token Adoption: Module Scores</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Figtree:wght@300;400;500;600&family=Roboto+Mono:wght@400&display=swap" rel="stylesheet">
  <style>
    /* Vibe design tokens */
    :root {{
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
      --font-heading: 'Poppins', Roboto, sans-serif;
      --font-body: 'Figtree', Roboto, sans-serif;
      --font-mono: 'Roboto Mono', Menlo, Courier, monospace;
      --font-weight-light: 300;
      --font-weight-regular: 400;
      --font-weight-medium: 450;
      --font-weight-semibold: 500;
      --font-weight-bold: 600;
      --text-xs: 0.857rem;
      --text-s:  1.000rem;
      --text-m:  1.143rem;
      --text-l:  1.429rem;
      --text-xl: 1.714rem;
      --text-xxl: 2.143rem;
      --line-height-xs: 1.429rem;
      --line-height-s:  1.714rem;
      --line-height-m:  2.000rem;
      --line-height-l:  2.286rem;
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
      --border-color: #E3E8F2;
      --border-thin: 1px solid #E3E8F2;
      --border-thick: 2px solid #E3E8F2;
      --border-radius: 4px;
      --shadow-xs: 0 1px 2px hsla(217,30%,24%,.08), 0 2px 4px hsla(217,30%,24%,.06);
      --shadow-s:  0 1px 3px hsla(217,30%,24%,.10), 0 4px 8px hsla(217,30%,24%,.07);
      --shadow-m:  0 2px 6px hsla(217,30%,24%,.10), 0 8px 16px hsla(217,30%,24%,.08);
      --page-max-width: 1200px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: var(--font-body); font-size: var(--text-s); font-weight: var(--font-weight-regular); line-height: var(--line-height-s); color: var(--color-paragraph); background: var(--color-lightest-shade); -webkit-font-smoothing: antialiased; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: var(--font-heading); color: var(--color-ink); line-height: var(--line-height-m); }}
    h1 {{ font-size: var(--text-xxl); font-weight: var(--font-weight-semibold); }}
    h4 {{ font-size: var(--text-m);   font-weight: var(--font-weight-semibold); }}
    h6 {{ font-size: var(--text-xs);  font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-subdued); }}
    p {{ line-height: var(--line-height-s); }}
    .text-subdued {{ color: var(--color-subdued); }}
    .text-xs {{ font-size: var(--text-xs); line-height: var(--line-height-xs); }}
    .text-mono {{ font-family: var(--font-mono); font-size: var(--text-xs); }}
    .text-number {{ font-variant-numeric: tabular-nums; }}
    a {{ color: var(--color-primary); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .page-header {{ background: var(--color-empty-shade); border-bottom: var(--border-thin); padding: var(--space-l) 0; }}
    .page-header-inner {{ max-width: var(--page-max-width); margin: 0 auto; padding: 0 var(--space-l); }}
    .page-header h1 {{ font-size: var(--text-l); font-weight: var(--font-weight-semibold); color: var(--color-ink); }}
    .page-header .breadcrumb {{ font-size: var(--text-xs); color: var(--color-subdued); margin-bottom: var(--space-xs); }}
    .page-header .breadcrumb a {{ color: var(--color-primary); }}
    .page-body {{ max-width: var(--page-max-width); margin: 0 auto; padding: var(--space-l); }}
    .panel {{ background: var(--color-empty-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-l); }}
    .panel + .panel {{ margin-top: var(--space-l); }}
    .panel--no-padding {{ padding: 0; }}
    .panel-title {{ font-size: var(--text-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-subdued); margin-bottom: var(--space-m); }}
    .stat-row {{ display: grid; gap: var(--space-m); grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin-bottom: var(--space-l); }}
    .stat-card {{ background: var(--color-empty-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-m) var(--space-l); }}
    .stat-card__label {{ font-size: var(--text-xs); color: var(--color-subdued); margin-bottom: var(--space-xs); text-transform: uppercase; letter-spacing: 0.05em; font-weight: var(--font-weight-semibold); }}
    .stat-card__value {{ font-size: var(--text-xl); font-weight: var(--font-weight-semibold); color: var(--color-ink); font-variant-numeric: tabular-nums; line-height: 1; }}
    .stat-card__description {{ font-size: var(--text-xs); color: var(--color-subdued); margin-top: var(--space-xs); }}
    .badge {{ display: inline-flex; align-items: center; font-size: var(--text-xs); font-weight: var(--font-weight-semibold); padding: 2px var(--space-s); border-radius: var(--border-radius); line-height: 1.5; }}
    .badge--default {{ background: var(--color-lightest-shade); color: var(--color-subdued); border: var(--border-thin); }}
    .badge--primary {{ background: var(--color-primary-bg); color: var(--color-primary); }}
    .badge--success {{ background: var(--color-success-bg); color: var(--color-success); }}
    .badge--warning {{ background: var(--color-warning-bg); color: var(--color-warning-text); }}
    .badge--danger  {{ background: var(--color-danger-bg);  color: var(--color-danger); }}
    .callout {{ border-radius: var(--border-radius); padding: var(--space-m) var(--space-l); border-left: 4px solid; margin-bottom: var(--space-m); }}
    .callout--info    {{ background: var(--color-primary-bg); border-color: var(--color-primary); }}
    .callout--success {{ background: var(--color-success-bg); border-color: var(--color-success); }}
    .callout--warning {{ background: var(--color-warning-bg); border-color: var(--color-warning); }}
    .callout--danger  {{ background: var(--color-danger-bg);  border-color: var(--color-danger); }}
    .callout__title {{ font-size: var(--text-s); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-xs); color: var(--color-ink); }}
    .callout__body {{ font-size: var(--text-s); color: var(--color-paragraph); }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: var(--text-s); }}
    thead th {{ font-size: var(--text-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-subdued); text-align: left; padding: var(--space-s) var(--space-m); border-bottom: var(--border-thick); white-space: nowrap; }}
    tbody td {{ padding: var(--space-m); border-bottom: var(--border-thin); vertical-align: middle; color: var(--color-paragraph); }}
    tbody tr:last-child td {{ border-bottom: none; }}
    tbody tr:hover {{ background: var(--color-lightest-shade); }}
    td.numeric, th.numeric {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-l); }}
    @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
    .separator {{ border: none; border-top: var(--border-thin); margin: var(--space-l) 0; }}
    .filter-bar {{ display: flex; gap: var(--space-s); padding: var(--space-m); border-bottom: var(--border-thin); flex-wrap: wrap; }}
    .filter-btn {{ font-size: var(--text-xs); padding: var(--space-xxs) var(--space-m); border-radius: var(--border-radius); border: var(--border-thin); background: transparent; color: var(--color-subdued); cursor: pointer; font-family: var(--font-body); font-weight: var(--font-weight-semibold); transition: all 0.15s; }}
    .filter-btn:hover {{ background: var(--color-lightest-shade); color: var(--color-ink); }}
    .filter-btn.active {{ background: var(--color-primary-bg); border-color: var(--color-primary); color: var(--color-primary); }}
    .panel-header {{ display: flex; align-items: center; justify-content: space-between; padding: var(--space-m) var(--space-l); border-bottom: var(--border-thin); }}
    /* Drawer */
    .drawer-overlay {{ position: fixed; inset: 0; background: rgba(7,16,31,0.4); z-index: 100; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
    .drawer-overlay.open {{ opacity: 1; pointer-events: auto; }}
    .drawer {{ position: fixed; top: 0; right: 0; height: 100vh; width: 560px; max-width: 100vw; background: var(--color-empty-shade); border-left: var(--border-thin); box-shadow: var(--shadow-m); z-index: 101; transform: translateX(100%); transition: transform 0.25s ease; overflow-y: auto; display: flex; flex-direction: column; }}
    .drawer.open {{ transform: translateX(0); }}
    .drawer-header {{ position: sticky; top: 0; background: var(--color-empty-shade); border-bottom: var(--border-thin); padding: var(--space-l); display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-m); z-index: 1; }}
    .drawer-close {{ background: none; border: none; cursor: pointer; color: var(--color-subdued); font-size: 18px; padding: var(--space-xs); border-radius: var(--border-radius); line-height: 1; }}
    .drawer-close:hover {{ background: var(--color-lightest-shade); color: var(--color-ink); }}
    .drawer-body {{ padding: var(--space-l); flex: 1; }}
    .drawer-section {{ margin-bottom: var(--space-xl); }}
    .drawer-section-title {{ font-size: var(--text-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-subdued); margin-bottom: var(--space-m); }}
    .cat-bar-row {{ display: flex; align-items: center; gap: var(--space-m); margin-bottom: var(--space-s); }}
    .cat-bar-label {{ font-size: var(--text-xs); color: var(--color-ink); width: 80px; flex-shrink: 0; }}
    .cat-bar-track {{ flex: 1; height: 8px; background: var(--color-light-shade); border-radius: 4px; overflow: hidden; }}
    .cat-bar-fill {{ height: 100%; border-radius: 4px; }}
    .cat-bar-count {{ font-size: var(--text-xs); color: var(--color-subdued); width: 50px; text-align: right; font-variant-numeric: tabular-nums; flex-shrink: 0; }}
    .code-example {{ background: var(--color-lightest-shade); border: var(--border-thin); border-radius: var(--border-radius); padding: var(--space-m); font-family: var(--font-mono); font-size: var(--text-xs); }}
    .code-before {{ color: var(--color-danger); }}
    .code-after  {{ color: var(--color-success); }}
    .quick-win-item {{ display: flex; align-items: center; justify-content: space-between; padding: var(--space-s) 0; border-bottom: var(--border-thin); }}
    .quick-win-item:last-child {{ border-bottom: none; }}
    .mi-overlay {{ position: fixed; inset: 0; background: rgba(7,16,31,0.5); z-index: 200; display: none; align-items: center; justify-content: center; }}
    .mi-overlay.open {{ display: flex; }}
    .mi-box {{ background: var(--color-empty-shade); border-radius: var(--border-radius); box-shadow: var(--shadow-l, 0 8px 32px rgba(0,0,0,0.18)); padding: var(--space-xl); max-width: 540px; width: 90vw; max-height: 80vh; overflow-y: auto; position: relative; }}
    .mi-close {{ position: absolute; top: var(--space-m); right: var(--space-m); background: none; border: none; cursor: pointer; color: var(--color-subdued); font-size: 18px; padding: var(--space-xs); border-radius: var(--border-radius); line-height: 1; }}
    .mi-close:hover {{ background: var(--color-lightest-shade); color: var(--color-ink); }}
    .mi-title {{ font-size: var(--text-l); font-weight: var(--font-weight-semibold); color: var(--color-ink); margin-bottom: var(--space-xs); padding-right: var(--space-xl); }}
    .mi-section-label {{ font-size: var(--text-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-subdued); margin-bottom: var(--space-s); margin-top: var(--space-l); }}
    .mi-dir-list {{ list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-xs); }}
    .mi-dir-list li code {{ display: inline-block; font-family: var(--font-mono); font-size: calc(var(--text-xs) * 0.85); background: var(--color-lightest-shade); border: var(--border-thin); border-radius: var(--border-radius-s, 3px); padding: 2px var(--space-s); color: var(--color-paragraph); }}
    .mi-stat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: var(--space-m); margin-top: var(--space-m); }}
    .mi-stat {{ background: var(--color-lightest-shade); border-radius: var(--border-radius); padding: var(--space-m); }}
    .mi-stat__label {{ font-size: calc(var(--text-xs) * 0.85); color: var(--color-subdued); margin-bottom: var(--space-xs); }}
    .mi-stat__value {{ font-size: var(--text-l); font-weight: 700; color: var(--color-ink); font-variant-numeric: tabular-nums; line-height: 1; }}
  </style>
</head>
<body>

  <header class="page-header">
    <div class="page-header-inner">
      <div class="breadcrumb"><a href="index.html">Projects</a> / Luna Token Adoption</div>
      <h1>Luna Token Adoption: Module Scores</h1>
      <p class="text-subdued" style="margin-top:var(--space-xs);">Scans CSS/SCSS for hardcoded values that match Luna design token values. Score = var(--luna-*) usages / (usages + violations).</p>
      <p class="text-subdued text-xs" style="margin-top:var(--space-xs);">{now}</p>
    </div>
  </header>

  <main class="page-body">

    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-card__label">Overall Score</div>
        <div class="stat-card__value" style="color:{score_text_color(overall)};">{overall}%</div>
        <div class="stat-card__description">across {len(results)} modules</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Violations</div>
        <div class="stat-card__value" style="color:var(--color-danger);">{total_viol:,}</div>
        <div class="stat-card__description">hardcoded token values</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Token Usages</div>
        <div class="stat-card__value" style="color:var(--color-success);">{total_uses:,}</div>
        <div class="stat-card__description">var(--luna-*) references</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">CSS Files</div>
        <div class="stat-card__value">{total_files}</div>
        <div class="stat-card__description">scanned across modules</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Token Values Indexed</div>
        <div class="stat-card__value">{token_type_count}</div>
        <div class="stat-card__description">Luna values in map</div>
      </div>
    </div>

    <div class="panel" style="margin-bottom:var(--space-l);">
      <div class="panel-title">Violation breakdown by token category</div>
      <div style="height:10px;border-radius:var(--border-radius);overflow:hidden;background:var(--color-light-shade);margin-bottom:var(--space-m);">
        <div style="height:100%;display:flex;">
          <div style="width:{space_pct}%;background:var(--color-warning);"></div>
          <div style="width:{color_pct}%;background:var(--color-danger);"></div>
          <div style="width:{radius_pct}%;background:var(--color-primary);"></div>
          <div style="width:{typo_pct}%;background:var(--color-accent-secondary);"></div>
        </div>
      </div>
      <div style="display:flex;gap:var(--space-l);flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs);color:var(--color-subdued);">
          <div style="width:10px;height:10px;border-radius:2px;background:var(--color-warning);flex-shrink:0;"></div>
          Space/Size ({cat_totals['space']:,}:{space_pct}%)
        </div>
        <div style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs);color:var(--color-subdued);">
          <div style="width:10px;height:10px;border-radius:2px;background:var(--color-danger);flex-shrink:0;"></div>
          Color ({cat_totals['color']:,}:{color_pct}%)
        </div>
        <div style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs);color:var(--color-subdued);">
          <div style="width:10px;height:10px;border-radius:2px;background:var(--color-primary);flex-shrink:0;"></div>
          Radius ({cat_totals['radius']:,}:{radius_pct}%)
        </div>
        <div style="display:flex;align-items:center;gap:var(--space-xs);font-size:var(--text-xs);color:var(--color-subdued);">
          <div style="width:10px;height:10px;border-radius:2px;background:var(--color-accent-secondary);flex-shrink:0;"></div>
          Typography ({cat_totals['typography']:,}:{typo_pct}%)
        </div>
      </div>
    </div>

    <div class="grid-2" style="margin-bottom:var(--space-l);">
      <div class="callout callout--info">
        <div class="callout__title">Scoring methodology</div>
        <div class="callout__body">Score = <strong>token usages / (token usages + violations)</strong>. Only property declarations in relevant categories are scanned: spacing properties for space/size tokens, color properties for hex colors, border-radius for radius, font-size for typography. Values like <code>0</code> are only flagged in spacing/radius contexts, not in z-index or opacity.</div>
      </div>
      <div class="callout callout--warning">
        <div class="callout__title">Space tokens dominate violations</div>
        <div class="callout__body">Space/size violations account for <strong>{space_pct}%</strong> of all violations. Values like <strong>0, 1rem, 0.5rem</strong> in margin/padding/gap should use <strong>var(--luna-space-*)</strong> equivalents. This is the single highest-impact migration target.</div>
      </div>
      <div class="callout callout--success">
        <div class="callout__title">Best performing: {best['name']}</div>
        <div class="callout__body">Leads with <strong>{best['score']}%</strong> across {best_note}. It has <strong>{best['violations']:,}</strong> violation{"s" if best["violations"] != 1 else ""} and <strong>{best['token_usages']:,}</strong> correct token usages.</div>
      </div>
      <div class="callout callout--danger">
        <div class="callout__title">Most violations: {worst['name']}</div>
        <div class="callout__body"><strong>{worst['violations']:,}</strong> violations across <strong>{worst['css_files']}</strong> CSS files (score: <strong>{worst['score']}%</strong>, grade: {worst['grade']}). Space token adoption is the primary gap.</div>
      </div>
    </div>

    <div class="panel panel--no-padding">
      <div class="panel-header">
        <h4 style="margin:0;">Module Leaderboard</h4>
        <span class="badge badge--default">{len(results)} modules</span>
      </div>
      <div class="filter-bar">
        <button class="filter-btn active" onclick="filterTable('all',this)">All</button>
        <button class="filter-btn" onclick="filterTable('good',this)">Good (80%+)</button>
        <button class="filter-btn" onclick="filterTable('fair',this)">Fair (50-79%)</button>
        <button class="filter-btn" onclick="filterTable('poor',this)">Needs Work (&lt;50%)</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Module</th>
              <th class="numeric">CSS Files</th>
              <th class="numeric">Violations</th>
              <th class="numeric">Token Uses</th>
              <th style="min-width:220px;">Score</th>
              <th style="text-align:center;">Grade</th>
              <th>Top Violations</th>
            </tr>
          </thead>
          <tbody>
{rows_html}
          </tbody>
        </table>
      </div>
    </div>

  </main>

  <div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
  <div class="drawer" id="drawer">
    <div class="drawer-header" id="drawerHeader"></div>
    <div class="drawer-body" id="drawerBody"></div>
  </div>

  <div class="mi-overlay" id="miOverlay" onclick="closeMI()">
    <div class="mi-box" onclick="event.stopPropagation()">
      <button class="mi-close" onclick="closeMI()">&#x2715;</button>
      <div id="miContent"></div>
    </div>
  </div>

  <script>
    var MODULE_DATA = {js_data};

    function filterTable(status, btn) {{
      document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      document.querySelectorAll('tbody tr').forEach(function(row) {{
        row.style.display = (status === 'all' || row.dataset.score === status) ? '' : 'none';
      }});
    }}

    function openDrawer(name) {{
      var mod = MODULE_DATA.find(function(m) {{ return m.name === name; }});
      if (!mod) return;
      var sorted = MODULE_DATA.slice().sort(function(a, b) {{ return b.score - a.score; }});
      var rank = sorted.findIndex(function(m) {{ return m.name === name; }}) + 1;

      var badgeClass = mod.score >= 80 ? 'badge--success' : mod.score >= 50 ? 'badge--warning' : 'badge--danger';
      var gradeClass = (mod.grade === 'A' || mod.grade === 'B') ? 'badge--success' : (mod.grade === 'C') ? 'badge--warning' : 'badge--danger';

      var drawerDispName = mod.name.split(' (')[0];
      var drawerSubtitle = mod.name.indexOf('(') !== -1 ? mod.name.slice(mod.name.indexOf('(') + 1, -1) : '';
      document.getElementById('drawerHeader').innerHTML =
        '<div>' +
        '<div style="font-size:var(--text-l);font-weight:var(--font-weight-semibold);color:var(--color-ink);margin-bottom:var(--space-xs);">' + drawerDispName + '</div>' +
        (drawerSubtitle ? '<div style="font-size:calc(var(--text-xs) * 0.7);color:var(--color-subdued);font-family:var(--font-mono);margin-bottom:var(--space-s);">' + drawerSubtitle + '</div>' : '<div style="margin-bottom:var(--space-s);"></div>') +
        '<div style="display:flex;gap:var(--space-s);flex-wrap:wrap;">' +
        '<span class="badge ' + badgeClass + '">' + mod.score + '%</span>' +
        '<span class="badge ' + gradeClass + '">Grade ' + mod.grade + '</span>' +
        '<span class="badge badge--default">Rank #' + rank + ' of ' + MODULE_DATA.length + '</span>' +
        '</div>' +
        '</div>' +
        '<button class="drawer-close" onclick="closeDrawer()">&#x2715;</button>';

      document.getElementById('drawerBody').innerHTML = renderDetail(mod, rank);
      document.getElementById('drawerOverlay').classList.add('open');
      document.getElementById('drawer').classList.add('open');
      document.body.style.overflow = 'hidden';
    }}

    function closeDrawer() {{
      document.getElementById('drawerOverlay').classList.remove('open');
      document.getElementById('drawer').classList.remove('open');
      document.body.style.overflow = '';
    }}

    function openMI(name) {{
      var m = MODULE_DATA.find(function(x) {{ return x.name === name; }});
      if (!m) return;
      var dispName = m.name.split(' (')[0];
      var dirs = m.dirs || [];
      var dirsHtml = dirs.length
        ? '<ul class="mi-dir-list">' + dirs.map(function(d) {{ return '<li><code>' + d + '</code></li>'; }}).join('') + '</ul>'
        : '<p style="color:var(--color-subdued);font-size:var(--text-xs);">No directories listed.</p>';
      var filesHtml = '<div style="font-size:var(--text-s);padding:var(--space-s) 0;color:var(--color-ink);">' +
        '<strong>' + m.css_files + '</strong> CSS / SCSS file' + (m.css_files !== 1 ? 's' : '') + ' scanned</div>';
      var sampleHtml = '';
      if (m.top_files && m.top_files.length) {{
        sampleHtml = '<div class="mi-section-label" style="margin-top:var(--space-l);">Sample File Locations</div>' +
          '<ul class="mi-dir-list">' +
          m.top_files.slice(0,8).map(function(f) {{ return '<li><code>' + f.path + '</code></li>'; }}).join('') +
          '</ul>';
      }}
      document.getElementById('miContent').innerHTML =
        '<div class="mi-title">' + dispName + '</div>' +
        '<div class="mi-section-label">Code Components</div>' + dirsHtml +
        '<div class="mi-section-label">Files</div>' + filesHtml +
        sampleHtml;
      document.getElementById('miOverlay').classList.add('open');
      document.body.style.overflow = 'hidden';
    }}

    function closeMI() {{
      document.getElementById('miOverlay').classList.remove('open');
      document.body.style.overflow = '';
    }}

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') {{ closeDrawer(); closeMI(); }}
    }});

    function renderDetail(mod, rank) {{
      var total = mod.token_usages + mod.violations;
      var scoreExplain = total === 0
        ? 'This module has no CSS files with scannable properties, so no violations or token usages were detected.'
        : mod.violations.toLocaleString() + ' out of ' + total.toLocaleString() + ' relevant CSS declarations use hardcoded values instead of Luna design tokens. Replacing these would raise the score to 100%.';

      var cats = [
        {{name: 'Space/Size', key: 'space',      color: 'var(--color-warning)'}},
        {{name: 'Color',      key: 'color',      color: 'var(--color-danger)'}},
        {{name: 'Radius',     key: 'radius',     color: 'var(--color-primary)'}},
        {{name: 'Typography', key: 'typography', color: 'var(--color-accent-secondary)'}},
      ];
      var maxCat = Math.max.apply(null, cats.map(function(c) {{ return mod.by_cat[c.key]; }})) || 1;

      var html = '';

      // Score summary
      var calloutType = mod.score >= 80 ? 'success' : mod.score >= 50 ? 'warning' : 'danger';
      html += '<div class="callout callout--' + calloutType + '" style="margin-bottom:var(--space-l);">';
      html += '<div class="callout__title">Score: ' + mod.score + '% (Grade ' + mod.grade + ')</div>';
      html += '<div class="callout__body">' + scoreExplain + '</div>';
      html += '</div>';

      // Category bars
      html += '<div class="drawer-section">';
      html += '<div class="drawer-section-title">Violations by Category</div>';
      cats.forEach(function(c) {{
        var count = mod.by_cat[c.key];
        var pct = maxCat > 0 ? Math.round(count / maxCat * 100) : 0;
        html += '<div class="cat-bar-row">';
        html += '<div class="cat-bar-label">' + c.name + '</div>';
        html += '<div class="cat-bar-track"><div class="cat-bar-fill" style="width:' + pct + '%;background:' + c.color + ';"></div></div>';
        html += '<div class="cat-bar-count">' + count.toLocaleString() + '</div>';
        html += '</div>';
      }});
      html += '</div>';

      // Top offending files
      if (mod.top_files && mod.top_files.length > 0) {{
        html += '<div class="drawer-section">';
        html += '<div class="drawer-section-title">Top Offending Files</div>';
        html += '<table style="font-size:var(--text-xs);width:100%;">';
        html += '<thead><tr>';
        html += '<th style="text-align:left;padding:var(--space-xs) var(--space-s);border-bottom:var(--border-thick);color:var(--color-subdued);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;font-size:var(--text-xs);">File</th>';
        html += '<th style="text-align:right;padding:var(--space-xs) var(--space-s);border-bottom:var(--border-thick);color:var(--color-subdued);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;font-size:var(--text-xs);">Violations</th>';
        html += '</tr></thead><tbody>';
        mod.top_files.forEach(function(f) {{
          var parts = f.path.split('/');
          var short = parts.slice(-2).join('/');
          html += '<tr>';
          html += '<td style="padding:var(--space-xs) var(--space-s);border-bottom:var(--border-thin);font-family:var(--font-mono);word-break:break-all;font-size:var(--text-xs);" title="' + f.path + '">' + short + '</td>';
          html += '<td style="text-align:right;padding:var(--space-xs) var(--space-s);border-bottom:var(--border-thin);color:var(--color-danger);font-weight:600;">' + f.violations + '</td>';
          html += '</tr>';
        }});
        html += '</tbody></table></div>';

        // Quick wins
        var quickWins = mod.top_files.filter(function(f) {{ return f.violations >= 1 && f.violations <= 3; }});
        if (quickWins.length > 0) {{
          html += '<div class="drawer-section">';
          html += '<div class="drawer-section-title">Quick Wins</div>';
          html += '<p class="text-xs text-subdued" style="margin-bottom:var(--space-m);">These files each have 3 or fewer violations. Fixing them is fast and raises your score immediately.</p>';
          html += '<div>';
          quickWins.forEach(function(f) {{
            var parts = f.path.split('/');
            var short = parts.slice(-2).join('/');
            html += '<div class="quick-win-item">';
            html += '<span class="text-mono">' + short + '</span>';
            html += '<span class="badge badge--warning">' + f.violations + ' violation' + (f.violations !== 1 ? 's' : '') + '</span>';
            html += '</div>';
          }});
          html += '</div></div>';
        }}
      }}

      // Improvement tips
      html += '<div class="drawer-section">';
      html += '<div class="drawer-section-title">How to Improve</div>';

      var tips = [];
      if (mod.by_cat.space > 0) {{
        tips.push({{
          title: 'Replace hardcoded spacing values',
          body: 'Margin, padding, gap, and size properties are using raw pixel or rem values. Swapping them for Luna space tokens is typically the highest-impact change and improves consistency across the app.',
          before: 'margin: 16px;\\npadding: 8px 24px;\\ngap: 12px;',
          after: 'margin: var(--luna-space-base);\\npadding: var(--luna-space-s) var(--luna-space-l);\\ngap: var(--luna-space-m);',
          color: 'var(--color-warning)',
        }});
      }}
      if (mod.by_cat.color > 0) {{
        tips.push({{
          title: 'Replace hardcoded hex colors',
          body: 'Color, background, and border properties are using hex values that map to Luna color tokens. Replacing them ensures your module respects future theme changes automatically.',
          before: 'color: #343741;\\nbackground-color: #F5F7FA;\\nborder-color: #E3E8F2;',
          after: 'color: var(--luna-color-paragraph);\\nbackground-color: var(--luna-color-lightest-shade);\\nborder-color: var(--luna-color-light-shade);',
          color: 'var(--color-danger)',
        }});
      }}
      if (mod.by_cat.radius > 0) {{
        tips.push({{
          title: 'Replace hardcoded border-radius values',
          body: 'Border-radius properties use raw pixel values that map directly to Luna radius tokens.',
          before: 'border-radius: 4px;\\nborder-radius: 8px;',
          after: 'border-radius: var(--luna-radius-s);\\nborder-radius: var(--luna-radius-m);',
          color: 'var(--color-primary)',
        }});
      }}
      if (mod.by_cat.typography > 0) {{
        tips.push({{
          title: 'Replace hardcoded font sizes',
          body: 'Font-size properties use raw rem values that map to Luna typography tokens.',
          before: 'font-size: 0.857rem;\\nfont-size: 1.143rem;',
          after: 'font-size: var(--luna-font-size-xs);\\nfont-size: var(--luna-font-size-m);',
          color: 'var(--color-accent-secondary)',
        }});
      }}

      if (tips.length === 0) {{
        html += '<p class="text-xs text-subdued">No specific improvement areas detected for this module.</p>';
      }} else {{
        tips.forEach(function(tip) {{
          html += '<div style="margin-bottom:var(--space-l);padding:var(--space-m);border:var(--border-thin);border-left:3px solid ' + tip.color + ';border-radius:var(--border-radius);">';
          html += '<div style="font-weight:var(--font-weight-semibold);font-size:var(--text-s);margin-bottom:var(--space-xs);">' + tip.title + '</div>';
          html += '<p class="text-xs text-subdued" style="margin-bottom:var(--space-s);">' + tip.body + '</p>';
          html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-s);">';
          html += '<div><div class="text-xs" style="color:var(--color-danger);font-weight:600;margin-bottom:2px;">Before</div>';
          html += '<div class="code-example"><span class="code-before">' + tip.before.replace(/\\n/g, '<br>') + '</span></div></div>';
          html += '<div><div class="text-xs" style="color:var(--color-success);font-weight:600;margin-bottom:2px;">After</div>';
          html += '<div class="code-example"><span class="code-after">' + tip.after.replace(/\\n/g, '<br>') + '</span></div></div>';
          html += '</div></div>';
        }});
      }}

      html += '</div>'; // close how-to-improve
      return html;
    }}
  </script>

</body>
</html>"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    out_path = REPO_ROOT / "luna-module-score-report.html"
    if "--out" in args:
        idx = args.index("--out")
        out_path = Path(args[idx + 1])

    print("Building Luna token maps...")
    maps = build_token_maps()
    print(f"  Color tokens:      {len(maps['color'])} hex values")
    print(f"  Space/size tokens: {len(maps['space'])} values")
    print(f"  Radius tokens:     {len(maps['radius'])} values")
    print(f"  Typography tokens: {len(maps['typography'])} font-size values")
    print()

    print("Scanning modules...")
    results = []
    for mod in MODULES:
        r = scan_module(mod, maps)
        results.append(r)
        print(f"  {mod['name']:<20} score={r['score']:>3}%  grade={r['grade']}  violations={r['violations']:>5,}  token_uses={r['token_usages']:>5,}  files={r['css_files']}")

    print()
    print("Generating report...")
    html = generate_html(results, maps)
    out_path.write_text(html, encoding="utf-8")
    print(f"Report written to: {out_path}")

    # Also write JSON data for debugging / re-use
    json_path = out_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Data written to:   {json_path}")

if __name__ == "__main__":
    main()
