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

MODULE_ICONS = {
    'Dashboard': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M.4 2.1h2.9V16H.4zM6.6 16h2.8V5.4H6.6zm6.1 0h2.9V0h-2.9z"/></svg>',
    'Controls': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M8 0 .8 2.5v.6a16.6 16.6 0 0 0 1 6 13.4 13.4 0 0 0 2.4 4 11 11 0 0 0 3.5 2.7l.3.2.3-.1a11 11 0 0 0 3.5-2.8 13.6 13.6 0 0 0 2.4-4 16.8 16.8 0 0 0 1-6v-.6zm5.6 3.7a14.4 14.4 0 0 1-1 4.8 11.6 11.6 0 0 1-2 3.4A10.9 10.9 0 0 1 8 14.3 10.2 10.2 0 0 1 5.4 12a11.6 11.6 0 0 1-2-3.5 14.6 14.6 0 0 1-1-4.8l5.6-2zm-6 6.6-2.9-3 .3-.2a1 1 0 0 1 1.4 0l1.2 1.1 2.7-2.7a1 1 0 0 1 1.5 0l.3.3z"/></svg>',
    'Risks': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M8.6 0 10 3.2 6 16 3.6 9.7H0v-.8a1.5 1.5 0 0 1 1.5-1.5H5l.8 1.8zm3.9 7.4-1-1.5-.7 2.5-.4 1.3h5.5v-.8a1.5 1.5 0 0 0-1.6-1.5h-1.9z"/></svg>',
    'CrossComply': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M15 2.8a2.6 2.6 0 0 0-5 .3L5.5 4.3a2.561 2.561 0 1 0-4 3.2 2.5 2.5 0 0 0 2.6.9l.3-.1 3.3 3.3a2.6 2.6 0 0 0 4.7 1.8 2.5 2.5 0 0 0 .1-1.6 2.6 2.6 0 0 0-.8-1.3L12.9 6h.2A2.5 2.5 0 0 0 15 3zm-5.6 7.3h-.2L5.9 6.8a2 2 0 0 0 .1-.5l4.5-1.2q.175.226.4.4L9.7 10q-.15-.021-.3 0z"/></svg>',
    'Issues': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 17 16"><path fill="currentColor" d="m16.7 12.1-6-10.3a2 2 0 0 0-3.5 0l-6 10.3a2 2 0 0 0 1.9 3.1h11.8a2 2 0 0 0 1.8-3zm-1.3 1.3a.5.5 0 0 1-.5.3H3.1a.5.5 0 0 1-.6-.5l6-10.3a.6.6 0 0 1 .8-.2.5.5 0 0 1 .2.2l6 10.3a.5.5 0 0 1 0 .5zM9 11a.9.9 0 1 0 0 1.8A.9.9 0 0 0 9 11m-.8-5.8h1.7v5H8.2z"/></svg>',
    'OpsAudit': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 17 16"><path fill="currentColor" d="M9 0v1.2a1.1 1.1 0 0 0 .8 1.1 6 6 0 0 1 3.9 7.4q-.21.52-.5 1a1 1 0 0 0 .2 1.3l.9.9A8 8 0 0 0 9 0m1.7 13.2A6 6 0 0 1 5.3 2.7a5.7 5.7 0 0 1 .9-.4 1 1 0 0 0 .7-1V0a8 8 0 1 0 6 14.3l-1-.9a1 1 0 0 0-1.2-.2"/></svg>',
    'WorkStream': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M14.2 14.2H1.8V1.8h9.8V0H0v16h16V9.4h-1.8zM5.3 7a1.4 1.4 0 0 0-2 0l-.3.4 4.5 4.4 8.1-8.1-.3-.4a1.4 1.4 0 0 0-2 0L7.5 9.1z"/></svg>',
    'BCM': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M0 16V0h1.848v16zm5.54 0V0H3.69v16zm3.69-8.266V16H7.383V7.734c0-1.867 1.355-3.336 3.078-3.336h.617v-1.73L16 5.332 11.078 8V6.398h-.617c-.738 0-1.23.668-1.23 1.336" clip-rule="evenodd"/></svg>',
    'Settings': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 17 16"><path fill="currentColor" d="M14.4 8a7 7 0 0 0 0-1L16 5.7l-2-3.4-2 .8a6.6 6.6 0 0 0-1.8-1L10 0H6l-.3 2A7.2 7.2 0 0 0 4 3l-2-.7-2 3.4L1.6 7a6.5 6.5 0 0 0 0 2L0 10.3l2 3.4 2-.8c.54.431 1.148.77 1.8 1L6 16h4l.3-2a7 7 0 0 0 1.8-1l2 .8 2-3.4L14.4 9a5 5 0 0 0 0-1m-5.6 4.7-.3 1.7h-1l-.3-1.7-.5-.2a4.8 4.8 0 0 1-2-1.1l-.4-.4-1.6.6-.6-.9 1.4-1-.1-.5a4.5 4.5 0 0 1 0-2.3v-.5L2.2 5.3l.6-1 1.6.7.4-.4a4.7 4.7 0 0 1 2-1.1l.5-.2.2-1.6h1.1l.3 1.6.5.2a4.8 4.8 0 0 1 2 1.1l.4.4 1.6-.6.5.9-1.4 1 .2.5a4.5 4.5 0 0 1 0 2.3l-.2.5 1.4 1-.5 1-1.6-.6-.4.4a4.7 4.7 0 0 1-2 1.1zM8 4.9a3.1 3.1 0 1 0 0 6.2 3.1 3.1 0 0 0 0-6.2M9.5 8a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"/></svg>',
    'ESG': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M8 4.559a11.3 11.3 0 0 1 7.642-3.304.35.35 0 0 1 .358.354v1.76a.34.34 0 0 1-.133.27.33.33 0 0 1-.213.081 8.86 8.86 0 0 0-6.097 2.77A9 9 0 0 0 8 8.746a8.8 8.8 0 0 0-.88 3.848v1.645a.35.35 0 0 1-.352.352H5.01a.35.35 0 0 1-.352-.352v-1.428a4.63 4.63 0 0 0-1.652-3.55 4.63 4.63 0 0 0-2.68-1.095A.35.35 0 0 1 0 7.814V6.053c0-.205.172-.364.377-.354A7.07 7.07 0 0 1 3.88 6.842c.61.4 1.16.89 1.62 1.453a11.4 11.4 0 0 1 .942-1.805 9 9 0 0 0-1.602-1.335A8.8 8.8 0 0 0 .346 3.72.353.353 0 0 1 0 3.368V1.61a.35.35 0 0 1 .358-.354c2.236.07 4.312.789 6.042 1.979.573.391 1.11.836 1.6 1.325m2.498 3.736a7.1 7.1 0 0 1 5.125-2.596.35.35 0 0 1 .247.08.35.35 0 0 1 .13.274v1.762c0 .184-.14.337-.325.351a4.66 4.66 0 0 0-4.332 4.645v1.428a.35.35 0 0 1-.352.352H9.23a.351.351 0 0 1-.352-.352v-1.428a7.1 7.1 0 0 1 1.62-4.516" clip-rule="evenodd"/></svg>',
    'TPRM': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M12.15 8.168a1.935 1.935 0 0 0 1.925-1.946 1.935 1.935 0 0 0-1.925-1.945H9.782a.21.21 0 0 1-.188-.303l.754-1.526a.21.21 0 0 1 .188-.117h1.614c2.127 0 3.85 1.742 3.85 3.891s-1.723 3.89-3.85 3.89H6.895a.21.21 0 0 1-.189-.302l.755-1.526a.21.21 0 0 1 .188-.116z" clip-rule="evenodd"/><path fill="currentColor" fill-rule="evenodd" d="M3.85 7.195A1.935 1.935 0 0 0 1.925 9.14c0 1.074.862 1.945 1.925 1.945h2.368a.21.21 0 0 1 .188.304l-.754 1.525a.21.21 0 0 1-.188.117H3.85C1.724 13.03 0 11.289 0 9.14c0-2.15 1.724-3.892 3.85-3.892h5.255a.21.21 0 0 1 .189.303l-.755 1.526a.21.21 0 0 1-.188.117z" clip-rule="evenodd"/></svg>',
    'Narratives': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M9.7 0H1.2v13.6A2.4 2.4 0 0 0 3.7 16h11V5.5zm.3 2.4 2.4 2.7H10zM3.7 14.6a1 1 0 0 1-1-1V1.4h5.9v5.1h4.7v8zm.9-6.1h6.3a.5.5 0 0 1 .5.5v.9H5.1a.5.5 0 0 1-.5-.5zm0 3h6.3a.5.5 0 0 1 .5.5v.9H5.1a.5.5 0 0 1-.5-.5z"/></svg>',
    'RegComply': '<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path d="M2 2.1V4.5L8.5 2.4L15 4.5V2.1L8.5 0L2 2.1Z" fill="currentColor"/><path d="M2 13.9V11.5L8.5 13.6L15 11.5V13.9L8.5 16L2 13.9Z" fill="currentColor"/><path d="M8.5 4L7.6 4.3V11.7L8.5 12L9.4 11.7V4.3L8.5 4Z" fill="currentColor"/><path d="M3.5 5.6V10.4L5.2 11V5.1L3.5 5.6Z" fill="currentColor"/><path d="M11.8 5.1V11L13.5 10.4V5.6L11.8 5.1Z" fill="currentColor"/></svg>',
    'Exceptions': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M0 16V0h1.848v16zm5.54 0V0H3.69v16zm3.69-8.266V16H7.383V7.734c0-1.867 1.355-3.336 3.078-3.336h.617v-1.73L16 5.332 11.078 8V6.398h-.617c-.738 0-1.23.668-1.23 1.336" clip-rule="evenodd"/></svg>',
    'Integrations': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M10.333 1v1.556h-3.11a3.123 3.123 0 0 0-3.112 3.11v.778h-.778A2.345 2.345 0 0 0 1 8.778V15h1.556V8.778c0-.44.338-.778.777-.778h.778v.778a3.123 3.123 0 0 0 3.111 3.11h3.111v1.556h1.556v-3.11H15V8.777h-3.111v-3.11H15V4.11h-3.111V1zm-3.11 3.111h3.11v6.222h-3.11a1.544 1.544 0 0 1-1.556-1.555V5.667c0-.869.687-1.556 1.555-1.556"/></svg>',
    'Automations': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M16 1.5v-1h-4.2L9 3H4.8c-.3-1-1.3-1.7-2.3-1.7C1.1 1.3 0 2.4 0 3.7s1.1 2.4 2.4 2.4l1.9 4.5H2.4c-.8.1-1.5.8-1.5 1.6v3.3h14.3v-3.3c0-.8-.7-1.5-1.5-1.6H5.9L3.8 5.8c.5-.3.8-.8 1-1.3H9L11.8 7H16V5.5h-3.5l-2-1.7 2-1.8H16zm-2.4 10.7v1.9H2.4v-1.9zM2.5 4.7c-.5 0-1-.4-1-1s.4-1 1-1 1 .4 1 1-.5 1-1 1"/></svg>',
    'Inventory': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M7.856 2.648c1.663-.078 3.143.678 4.239 1.89-.132.148-.425.57-.56.749-.302.399-.617.788-.943 1.167C9.164 8.119 7.588 9.652 5.884 11.033c-.445.367-.923.708-1.391 1.045-.211-.218-.374-.344-.589-.598C3.149 10.59 2.705 9.477 2.642 8.311 2.558 6.877 3.057 5.469 4.025 4.408 5.049 3.278 6.347 2.722 7.856 2.648zm6.593-2.647c.75-.024 1.445.388 1.534 1.164.18 1.575-1.1 3.42-1.974 4.639-.816 1.113-1.698 2.175-2.643 3.181-1.909 2.042-6.65 6.531-9.4 6.978-.484.079-1.018.08-1.432-.224C.253 15.534.076 15.232.024 14.889c-.257-1.7 1.559-4.069 2.535-5.373.059.24.133.444.227.672-.441.571-.838 1.174-1.187 1.804-.243.464-.49 1.006-.58 1.522-.064.36-.07.794.151 1.101.146.202.39.34.633.372 1.23.163 2.987-1.027 3.947-1.716 1.691-1.211 3.314-2.71 4.753-4.2C11.731 7.8 12.92 6.4 13.874 4.914c.438-.682.918-1.555 1.061-2.353.063-.349.061-.837-.163-1.122-.173-.22-.429-.373-.706-.403C12.854.909 11.087 2.073 10.154 2.79c-.18-.086-.453-.17-.647-.235.166-.086.523-.357.703-.473.737-.473 1.66-1.031 2.541-1.119z"/><path fill="currentColor" d="M13.3 7.193c.105.151.045 1.362.011 1.595-.21 1.414-.973 2.686-2.121 3.537-1.111.831-2.505 1.19-3.879.999-.049-.003-.085.001-.123-.027.009-.08.231-.217.306-.28.307-.26.613-.52.918-.784 1.203-1.054 2.347-2.173 3.428-3.352.308-.337.61-.678.906-1.024.176-.21.372-.473.554-.664z"/></svg>',
    'AI Governance': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M8.281 11.081c0 1.995-1.482 3.612-3.311 3.612H1v-2.021c0-.879.653-1.59 1.458-1.59zm3.24-4.457c0 1.757-1.307 3.183-2.917 3.183H1V7.784c0-.878.653-1.59 1.458-1.59h9.063zM15 1.737c0 1.757-1.306 3.182-2.917 3.182H1.082V2.897c0-.878.653-1.59 1.458-1.59H15z"/></svg>',
    'Files': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M12.8 4H8.2L7 2.8a3.3 3.3 0 0 0-2.6-1.2H0v13h16V7a3 3 0 0 0-3.2-3M4.5 3a1.9 1.9 0 0 1 1.4.6l.4.4H1.5V3zm10 10h-13V5.6h11.3A1.6 1.6 0 0 1 14.5 7z"/></svg>',
    'Timesheets': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0m6.2 8A6.2 6.2 0 1 1 1.8 8 6.2 6.2 0 0 1 14.2 8M9 7.7V4a1.2 1.2 0 0 0-1.2-1.2H7v5.6l3.5 3.4.4-.4a1.2 1.2 0 0 0 0-1.7z"/></svg>',
    'Automated Security Questionnaires': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" d="M16 16H3v-2h11V3h2zM13 2H2v11H0V0h13zm-2 9H5V9h6zm0-4H5V5h6z"/></svg>',
    'ITRM / Cyber Risk': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M3.266 4.078v5.567l1.574.909V4.547l5.32-3.071L8.467.5 3.762 3.216a1 1 0 0 0-.496.862m4.852 6.168a1.446 1.446 0 1 0 0-2.892 1.446 1.446 0 0 0 0 2.892m3.154 2.337-4.823 2.785a1 1 0 0 1-.994 0L.75 12.65v-1.953l5.32 3.071 5.202-3.004zm3.363-5.618L9.813 4.181l-1.574.908 5.202 3.004v6.143l1.691-.977V7.826a1 1 0 0 0-.497-.86" clip-rule="evenodd"/></svg>',
    'Other': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="m12.878.375.98.981L9.886 5.33l-.89.89c-.55.55-1.441.55-1.991 0l-.89-.89L2.14 1.356l.981-.98c.5-.501 1.31-.501 1.811 0L8 3.443 11.067.375c.5-.5 1.31-.5 1.81 0M.375 3.121l.981-.98L5.33 6.114l.89.89c.55.55.55 1.441 0 1.991l-.89.89-3.973 3.974-.98-.981c-.501-.5-.501-1.31 0-1.811L3.443 8 .375 4.932c-.5-.5-.5-1.31 0-1.81M14.644 13.86l.98-.981c.501-.5.501-1.31 0-1.811l-3.068-3.069 3.069-3.068c.5-.5.5-1.31 0-1.81l-.981-.982-3.974 3.976-.89.89c-.55.55-.55 1.441 0 1.991l.89.89zM3.12 15.625l-.98-.981 3.976-3.973.89-.89c.55-.55 1.442-.55 1.991 0l.89.89 3.973 3.973-.981.98c-.5.501-1.31.501-1.811 0L8 12.557l-3.069 3.069c-.5.5-1.31.5-1.81 0" clip-rule="evenodd"/></svg>',
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

    # Serialize MODULE_ICONS for embedding in JS
    icons_js = 'const MODULE_ICONS = {\n' + ',\n'.join(
        f"  '{k}':'{v}'" for k, v in MODULE_ICONS.items()
    ) + '\n};'

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
        icon_svg = MODULE_ICONS.get(display_name, '')
        rows.append(f'''
    <tr data-score="{score_band}" onclick="openDrawer('{mod_name_js}')" style="cursor:pointer;">
      <td onclick="event.stopPropagation();openMI('{mod_name_js}')" style="cursor:pointer;" title="View module composition">
        <div style="display:flex;align-items:center;gap:var(--space-s);">
          <span style="width:16px;height:16px;flex-shrink:0;display:inline-flex;align-items:center;color:var(--color-primary);">{icon_svg}</span>
          <div>
            <div style="font-weight:var(--font-weight-semibold);color:var(--color-ink);">{display_name}</div>
            <div style="margin-top:3px;font-size:calc(var(--text-xs) * 0.7);color:var(--color-subdued);font-family:var(--font-mono);font-weight:normal;">{subtitle}</div>
          </div>
        </div>
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

    {icons_js}

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
      var filesHtml = '<ul style="margin:var(--space-s) 0 0;padding-left:var(--space-l);font-size:var(--text-s);color:var(--color-ink);line-height:1.6;">' +
        '<li><strong>' + m.css_files + '</strong> CSS / SCSS file' + (m.css_files !== 1 ? 's' : '') + ' — scanned for Luna token adoption</li>' +
        '</ul>';
      var sampleHtml = '';
      if (m.top_files && m.top_files.length) {{
        sampleHtml = '<div class="mi-section-label" style="margin-top:var(--space-l);">Sample File Locations</div>' +
          '<ul class="mi-dir-list">' +
          m.top_files.slice(0,8).map(function(f) {{ return '<li><code>' + f.path + '</code></li>'; }}).join('') +
          '</ul>';
      }}
      var iconHtml = MODULE_ICONS[dispName] ? '<span style="width:20px;height:20px;display:inline-flex;flex-shrink:0;color:var(--color-primary);">' + MODULE_ICONS[dispName] + '</span>' : '';
      document.getElementById('miContent').innerHTML =
        '<div class="mi-title" style="display:flex;align-items:center;gap:var(--space-s);">' + iconHtml + dispName + '</div>' +
        '<div class="mi-section-label">Code Components</div>' + dirsHtml +
        '<div class="mi-section-label">Files Scanned</div>' + filesHtml +
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
