#!/usr/bin/env python3
"""
build_site.py — generates the hightouch-101 multi-page presentation site.

Reads every .md doc under course/ and business-packs/tollway/ (CLAUDE.md files
excluded — those are Claude/Johan working conventions, not colleague-facing
content) and renders them into a shared-template static site under docs/.

Two audiences, two manifests:
  STUDENT_MANIFEST -> the public nav (Lessons / Reference / Course Notes),
    what a colleague working through the course actually sees.
  ADMIN_MANIFEST    -> reset/teardown checklists, built as real pages under
    docs/admin/ but never linked from any student-facing page or nav. Not
    real security (this is a public repo) — just not advertised.

This script NEVER writes back to the source .md files — read-only input,
generated output only. Rerun it after editing any source doc:

    python3 tools/build_site.py

Pure stdlib. No pandoc/markdown package dependency (neither is available in
this environment) — the parser below is a compact, purpose-built subset
covering exactly what this project's docs use: headers, paragraphs, ordered/
unordered lists (one level of nesting), pipe tables, fenced code blocks
(```mermaid``` rendered client-side via mermaid.js, others as <pre><code>),
bold/italic, inline code, and inline-code-formatted relative-path references
(e.g. `` `../dictionary/cheatsheet.md` ``) which get resolved into real
cross-page links by matching against the manifests below — regardless of how
many `../` segments the source prose used, since those were never functioning
links before this script existed.
"""

import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "docs")  # "docs", not "site" — GitHub Pages only serves / or /docs

# ----------------------------------------------------------------------
# Student manifest — the public nav. (src, out, title, section)
#   src: path relative to ROOT
#   out: path relative to SITE_DIR
# ----------------------------------------------------------------------

STUDENT_MANIFEST = [
    ("business-packs/tollway/lessons/01-cdp-standup.md", "tollway/lessons/01-cdp-standup.html", "Lesson 1 — Stand Up the CDP", "Lessons"),
    ("business-packs/tollway/lessons/02-single-customer-view.md", "tollway/lessons/02-single-customer-view.html", "Lesson 2 — Single Customer View", "Lessons"),
    ("business-packs/tollway/lessons/03-destinations.md", "tollway/lessons/03-destinations.html", "Lesson 3 — Destinations", "Lessons"),
    ("business-packs/tollway/lessons/04-segments-and-activation.md", "tollway/lessons/04-segments-and-activation.html", "Lesson 4 — Segments + Activation", "Lessons"),
    ("business-packs/tollway/lessons/05-closing-the-loop.md", "tollway/lessons/05-closing-the-loop.html", "Lesson 5 — Closing the Loop", "Lessons"),

    ("business-packs/tollway/brief.md", "tollway/brief.html", "Business Brief", "Reference"),
    ("business-packs/tollway/use-cases.md", "tollway/use-cases.html", "Use Cases", "Reference"),
    ("business-packs/tollway/dictionary/tables.md", "tollway/dictionary/tables.html", "Table Dictionary", "Reference"),
    ("business-packs/tollway/dictionary/relationships.md", "tollway/dictionary/relationships.html", "Relationships & Diagrams", "Reference"),
    ("business-packs/tollway/dictionary/cheatsheet.md", "tollway/dictionary/cheatsheet.html", "Diagnostic Cheatsheet", "Reference"),
    ("business-packs/tollway/dictionary/inconsistencies.md", "tollway/dictionary/inconsistencies.html", "Known Deviations", "Reference"),

    ("course/syllabus.md", "course/syllabus.html", "Syllabus", "Course Notes"),
    ("course/diagrams/architecture-overview.md", "course/diagrams/architecture-overview.html", "Generic Architecture", "Course Notes"),
    ("course/diagrams/course-flow.md", "course/diagrams/course-flow.html", "Generic Course Flow", "Course Notes"),
    ("course/recipes/hightouch-model-recipes.md", "course/recipes/hightouch-model-recipes.html", "Hightouch Model Recipes", "Course Notes"),
    ("course/recipes/hightouch-sync-recipes.md", "course/recipes/hightouch-sync-recipes.html", "Hightouch Sync Recipes", "Course Notes"),
    ("course/recipes/braze-canvas-recipes.md", "course/recipes/braze-canvas-recipes.html", "Braze Canvas Recipes", "Course Notes"),
]

STUDENT_SECTION_ORDER = ["Lessons", "Reference", "Course Notes"]
SECTION_CLASS = {"Lessons": "lessons", "Reference": "reference", "Course Notes": "coursenotes"}
SECTION_ICON = {"Lessons": "▸", "Reference": "❖", "Course Notes": "⚙"}  # ▸ ❖ ⚙

# ----------------------------------------------------------------------
# Admin manifest — reset/teardown checklists. Built under docs/admin/,
# never linked from any student page. See ADMIN_BANNER below.
# ----------------------------------------------------------------------

ADMIN_MANIFEST = [
    ("course/reset/README.md", "admin/course-reset/index.html", "Reset — Index", "Reset"),
    ("course/reset/warehouse-reset-template.md", "admin/course-reset/warehouse-reset-template.html", "Warehouse Reset Template", "Reset"),
    ("course/reset/hightouch-braze-checklist-template.md", "admin/course-reset/hightouch-braze-checklist-template.html", "Hightouch + Braze Checklist Template", "Reset"),
    ("business-packs/tollway/reset/reset-tollway-checklist.md", "admin/tollway-reset/reset-tollway-checklist.html", "TollWay Reset Checklist", "Reset"),
]

ADMIN_SECTION_ORDER = ["Reset"]

ALL_MANIFEST = STUDENT_MANIFEST + ADMIN_MANIFEST

ADMIN_BANNER = (
    '<div class="admin-banner">Internal — not part of the lesson flow. '
    "Not linked from the student site.</div>"
)

# ----------------------------------------------------------------------
# Link resolution — match an inline-code path reference (however many
# ../ segments it has, correct or not) to a manifest entry by longest
# matching path suffix. Covers both manifests, since admin docs sometimes
# reference student docs (e.g. the reset checklist points at the cheatsheet).
# ----------------------------------------------------------------------

def build_link_index():
    index = {}
    for src, out, title, section in ALL_MANIFEST:
        parts = src.split("/")
        for i in range(len(parts)):
            suffix = "/".join(parts[i:])
            index.setdefault(suffix, []).append((src, out, title))
    return index

LINK_INDEX = build_link_index()
ADMIN_OUTS = {out for src, out, title, section in ADMIN_MANIFEST}

def resolve_md_reference(raw_text, current_src, current_out):
    """raw_text is the exact content of a `...` code span. Returns the
    manifest 'out' path if raw_text looks like a reference to a known doc,
    else None. Never resolves a link FROM a student page INTO the admin
    section — a student page mentioning a reset doc by path stays as plain
    text, not a clickable link, so the admin section is never reachable by
    browsing the student site."""
    if not raw_text.endswith(".md"):
        return None
    cleaned = raw_text.lstrip("./")
    candidates = []
    parts = cleaned.split("/")
    for i in range(len(parts)):
        suffix = "/".join(parts[i:])
        if suffix in LINK_INDEX:
            candidates.extend(LINK_INDEX[suffix])
    if not candidates:
        return None
    current_dir = os.path.dirname(current_src)
    target = None
    if len(candidates) == 1:
        target = candidates[0][1]
    else:
        for src, out, title in candidates:
            if os.path.dirname(src) == current_dir:
                target = out
                break
        if target is None:
            target = candidates[0][1]
    if target in ADMIN_OUTS and current_out not in ADMIN_OUTS:
        return None
    return target

def relhref(current_out, target_out):
    current_dir = os.path.dirname(os.path.join(SITE_DIR, current_out))
    target_path = os.path.join(SITE_DIR, target_out)
    return os.path.relpath(target_path, current_dir)

# ----------------------------------------------------------------------
# Inline rendering: bold, inline code (+ path-link resolution), italics,
# HTML-escaping of everything else.
# ----------------------------------------------------------------------

CODE_SPAN_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")

def render_inline(text, current_src, current_out):
    spans = []
    def stash_code(m):
        spans.append(m.group(1))
        return f"\x00CODE{len(spans) - 1}\x00"
    text = CODE_SPAN_RE.sub(stash_code, text)
    text = BOLD_RE.sub(lambda m: f"\x00B{len(spans)}\x00{m.group(1)}\x00/B\x00", text)

    def escape_and_restore(s):
        out = []
        pattern = re.compile(r"\x00(CODE)(\d+)\x00|\x00(B)(\d+)\x00(.*?)\x00/B\x00", re.S)
        last = 0
        for m in pattern.finditer(s):
            out.append(html.escape(s[last:m.start()]))
            if m.group(1) == "CODE":
                idx = int(m.group(2))
                raw = spans[idx]
                target = resolve_md_reference(raw, current_src, current_out)
                escaped_raw = html.escape(raw)
                if target:
                    href = relhref(current_out, target)
                    out.append(f'<a class="docref" href="{href}"><code>{escaped_raw}</code></a>')
                else:
                    out.append(f"<code>{escaped_raw}</code>")
            else:
                inner = html.escape(m.group(5))
                inner = ITALIC_RE.sub(lambda im: f"<em>{im.group(1)}</em>", inner)
                out.append(f"<strong>{inner}</strong>")
            last = m.end()
        out.append(html.escape(s[last:]))
        return "".join(out)

    result = escape_and_restore(text)
    if "\x00" not in result:
        result = ITALIC_RE.sub(lambda m: f"<em>{html.escape(m.group(1))}</em>", result)
    return result

# ----------------------------------------------------------------------
# Block parsing
# ----------------------------------------------------------------------

HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)$")
UL_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
OL_RE = re.compile(r"^(\s*)\d+\.\s+(.*)$")
FENCE_RE = re.compile(r"^(\s*)```(\S*)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]+\|?\s*$")

def join_wrapped_lines(lines):
    """Join soft-wrapped source lines into one paragraph. A line ending in a
    single ASCII hyphen (word-wrap mid-hyphenated-word, e.g. "non-\\nsubscription")
    joins with no space; everything else joins with a space. Doesn't apply to
    the em-dash (—) used throughout these docs as punctuation, since that's a
    different character."""
    result = ""
    for i, l in enumerate(lines):
        s = l.strip()
        if i == 0:
            result = s
        elif result.endswith("-") and not result.endswith("--"):
            result += s
        else:
            result += " " + s
    return result

def split_table_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]

def parse_blocks(lines):
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue

        m = HEADER_RE.match(line)
        if m:
            blocks.append({"type": "header", "level": len(m.group(1)), "text": m.group(2).strip()})
            i += 1
            continue

        m = FENCE_RE.match(line)
        if m:
            indent, lang = m.group(1), m.group(2)
            code_lines = []
            i += 1
            while i < n and not re.match(rf"^{re.escape(indent)}```\s*$", lines[i]):
                code_lines.append(lines[i][len(indent):] if lines[i].startswith(indent) else lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(code_lines)})
            continue

        if TABLE_ROW_RE.match(line) and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = split_table_row(line)
            i += 2
            rows = []
            while i < n and TABLE_ROW_RE.match(lines[i]):
                rows.append(split_table_row(lines[i]))
                i += 1
            blocks.append({"type": "table", "header": header, "rows": rows})
            continue

        m = OL_RE.match(line) or UL_RE.match(line)
        if m:
            ordered = bool(OL_RE.match(line))
            marker_re = OL_RE if ordered else UL_RE
            items = []
            while i < n:
                mm = marker_re.match(lines[i]) if lines[i].strip() else None
                if not mm:
                    break
                base_indent = len(mm.group(1))
                first_content = mm.group(2)
                item_lines = [first_content]
                i += 1
                while i < n:
                    nxt = lines[i]
                    if nxt.strip() == "":
                        lookahead = i + 1
                        if lookahead < n and (len(lines[lookahead]) - len(lines[lookahead].lstrip())) > base_indent:
                            item_lines.append("")
                            i += 1
                            continue
                        break
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent > base_indent:
                        item_lines.append(nxt[base_indent + 3:] if nxt[:base_indent + 3].strip() == "" else nxt.lstrip())
                        i += 1
                        continue
                    break
                items.append(parse_blocks(item_lines))
            blocks.append({"type": "ordered" if ordered else "unordered", "items": items})
            continue

        para_lines = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not (
            HEADER_RE.match(lines[i]) or FENCE_RE.match(lines[i]) or
            OL_RE.match(lines[i]) or UL_RE.match(lines[i]) or TABLE_ROW_RE.match(lines[i])
        ):
            para_lines.append(lines[i])
            i += 1
        blocks.append({"type": "paragraph", "text": join_wrapped_lines(para_lines)})

    return blocks

# ----------------------------------------------------------------------
# HTML rendering
# ----------------------------------------------------------------------

def render_blocks(blocks, current_src, current_out):
    out = []
    for b in blocks:
        if b["type"] == "header":
            out.append(f'<h{b["level"]}>{render_inline(b["text"], current_src, current_out)}</h{b["level"]}>')
        elif b["type"] == "paragraph":
            out.append(f'<p>{render_inline(b["text"], current_src, current_out)}</p>')
        elif b["type"] == "code":
            if b["lang"] == "mermaid":
                out.append(f'<div class="mermaid">\n{html.escape(b["text"], quote=False)}\n</div>')
            else:
                cls = f' class="language-{b["lang"]}"' if b["lang"] else ""
                out.append(f'<pre><code{cls}>{html.escape(b["text"])}</code></pre>')
        elif b["type"] == "table":
            head = "".join(f"<th>{render_inline(c, current_src, current_out)}</th>" for c in b["header"])
            body = ""
            for row in b["rows"]:
                body += "<tr>" + "".join(f"<td>{render_inline(c, current_src, current_out)}</td>" for c in row) + "</tr>\n"
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}</tbody></table>")
        elif b["type"] in ("ordered", "unordered"):
            tag = "ol" if b["type"] == "ordered" else "ul"
            items_html = ""
            for item_blocks in b["items"]:
                inner = render_blocks(item_blocks, current_src, current_out)
                items_html += f"<li>{inner}</li>\n"
            out.append(f"<{tag}>\n{items_html}</{tag}>")
    return "\n".join(out)

# ----------------------------------------------------------------------
# Page template
# ----------------------------------------------------------------------

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Hightouch 101</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
{css}
</style>
</head>
<body>
<div class="shell">
<aside class="sidebar">
  <div class="brand"><span class="eyebrow">Hightouch 101</span>TollWay<span class="brandsub">Training Site</span></div>
  <a class="homebtn" href="{home_href}">&larr; All lessons &amp; reference</a>
  <nav>
{nav}
  </nav>
</aside>
<main class="page-content">
{banner}
{content}
</main>
</div>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'dark',
    flowchart: {{ useMaxWidth: false }},
    er: {{ useMaxWidth: false }},
    themeVariables: {{
      background: '#1A1A2E',
      primaryColor: '#1A1A2E',
      primaryTextColor: '#ffffff',
      primaryBorderColor: '#2a2a44',
      lineColor: '#6C5CE7',
      secondaryColor: '#1A1A2E',
      tertiaryColor: '#1A1A2E',
      fontFamily: 'Poppins, sans-serif',
      fontSize: '18px'
    }}
  }});
</script>
</body>
</html>
"""

CSS = """
:root{
  --bg:#0D0D1A;--card:#1A1A2E;--line:#2a2a44;--txt:#ffffff;
  --muted:#cfd0e0;--purple:#6C5CE7;--cyan:#00D4FF;--green:#2ecc71;
  --amber:#f1a33c;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:Poppins,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.shell{display:flex;min-height:100vh}

.sidebar{width:272px;flex:0 0 272px;background:linear-gradient(180deg,#161629,var(--card));border-right:1px solid var(--line);padding:24px 16px;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{font-size:17px;font-weight:700;margin-bottom:14px;line-height:1.3;padding:0 6px}
.brand .eyebrow{display:block;font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:var(--purple);margin-bottom:2px}
.brand .brandsub{display:block;font-size:11px;font-weight:400;color:var(--muted);margin-top:2px}
.homebtn{display:block;font-size:12px;color:var(--muted);text-decoration:none;border:1px solid var(--line);border-radius:9px;padding:8px 12px;margin:0 4px 18px;text-align:center}
.homebtn:hover{border-color:var(--cyan);color:var(--cyan)}

.navgroup{margin:0 0 20px;padding:2px 0 2px 14px;border-left:2px solid rgba(255,255,255,.08)}
.navgroup.lessons{--gc:var(--cyan);--gcbg:rgba(0,212,255,.14)}
.navgroup.reference{--gc:var(--purple);--gcbg:rgba(108,92,231,.16)}
.navgroup.coursenotes{--gc:var(--amber);--gcbg:rgba(241,163,60,.14)}
.navgroup.reset{--gc:#e05a5a;--gcbg:rgba(224,90,90,.15)}
.navgroup .gh{display:flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:var(--gc);margin:0 0 8px}
.navgroup .gh .ic{font-size:11px}
.navgroup .gh .count{margin-left:auto;background:var(--gcbg);color:var(--gc);font-size:10px;font-weight:700;border-radius:999px;padding:1px 7px}
.navgroup a{display:block;color:var(--muted);text-decoration:none;font-size:13.5px;padding:6px 10px;border-radius:8px;margin-bottom:2px;border-left:3px solid transparent}
.navgroup a:hover{background:rgba(255,255,255,.05);color:var(--txt)}
.navgroup a.active{background:var(--gcbg);color:var(--txt);font-weight:600;border-left:3px solid var(--gc);margin-left:-3px;padding-left:10px}

main.page-content{flex:1;max-width:1300px;padding:36px 48px 80px}
main.page-content h1{font-size:30px;font-weight:700;letter-spacing:-.3px;margin:0 0 18px;max-width:900px}
main.page-content h2{font-size:19px;font-weight:600;margin:32px 0 12px;color:var(--cyan);max-width:900px}
main.page-content h3{font-size:16px;font-weight:600;margin:22px 0 8px;max-width:900px}
main.page-content h4{font-size:14px;font-weight:600;margin:18px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;max-width:900px}
main.page-content p{max-width:820px;color:var(--muted);margin:0 0 14px;font-size:15px}
main.page-content strong{color:var(--txt)}
main.page-content ul,main.page-content ol{max-width:820px;color:var(--muted);margin:0 0 14px;padding-left:24px;font-size:15px}
main.page-content li{margin-bottom:6px}
main.page-content li p{margin:0 0 6px}
main.page-content code{background:rgba(255,255,255,.08);padding:2px 6px;border-radius:5px;font-size:13px;color:var(--cyan);font-family:'SF Mono',Consolas,monospace}
main.page-content a.docref{text-decoration:none}
main.page-content a.docref code{color:var(--cyan);text-decoration:underline;text-decoration-color:rgba(0,212,255,.4)}
main.page-content pre{background:#0a0a18;border:1px solid var(--line);border-radius:10px;padding:16px 18px;overflow-x:auto;margin:0 0 16px;max-width:1100px}
main.page-content pre code{background:none;padding:0;color:var(--txt);font-size:13.5px;line-height:1.55}
main.page-content table{border-collapse:collapse;width:100%;max-width:1100px;margin:0 0 20px;font-size:14px}
main.page-content th{text-align:left;font-size:11px;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);padding:0 14px 10px 0;border-bottom:1px solid var(--line)}
main.page-content td{padding:10px 14px 10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:var(--muted);vertical-align:top}
main.page-content .mermaid{width:100%;display:flex;justify-content:center;margin:20px 0 28px;overflow-x:auto}
main.page-content .mermaid svg{max-width:100% !important;height:auto !important}

.admin-banner{max-width:1100px;background:rgba(224,90,90,.12);border:1px solid rgba(224,90,90,.4);color:#f0a5a5;border-radius:10px;padding:10px 16px;font-size:13px;font-weight:600;margin-bottom:24px}

.hero{max-width:820px;margin-bottom:14px}
.hero .eyebrow{font-size:11px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:var(--purple);margin-bottom:6px}
.hero p{font-size:16px}
.cta{display:inline-block;background:var(--purple);color:#fff;text-decoration:none;font-weight:600;font-size:15px;padding:13px 26px;border-radius:11px;margin:10px 0 34px}
.cta:hover{opacity:.88}
.home-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;max-width:1300px}
.home-card{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--gc);border-radius:14px;padding:18px 20px}
.home-card h3{margin:0 0 12px;color:var(--txt);font-size:14px;display:flex;align-items:center;gap:6px;letter-spacing:.4px;text-transform:uppercase}
.home-card ul{margin:0;padding-left:18px}
.home-card a{color:var(--muted);text-decoration:none;font-size:14px}
.home-card a:hover{color:var(--cyan);text-decoration:underline}
.home-card li{margin-bottom:6px}

@media(max-width:900px){
  .shell{flex-direction:column}
  .sidebar{width:100%;flex:none;position:relative;height:auto}
  main.page-content{padding:24px 20px}
  .home-grid{grid-template-columns:1fr}
}
"""

def render_nav(active_out, manifest, section_order):
    groups = {}
    for src, out, title, section in manifest:
        groups.setdefault(section, []).append((out, title))
    parts = []
    for section in section_order:
        cls = SECTION_CLASS.get(section, "reset")
        icon = SECTION_ICON.get(section, "■")
        items = groups.get(section, [])
        parts.append(f'  <div class="navgroup {cls}"><div class="gh"><span class="ic">{icon}</span>{html.escape(section)}<span class="count">{len(items)}</span></div>')
        for out, title in items:
            active = "active" if out == active_out else ""
            parts.append(f'    <a href="{relhref(active_out, out)}" class="{active}">{html.escape(title)}</a>')
        parts.append("  </div>")
    return "\n".join(parts)

def render_page(title, content_html, out, nav_html, home_href, banner=""):
    return TEMPLATE.format(title=html.escape(title), css=CSS, nav=nav_html, content=content_html,
                           home_href=home_href, banner=banner)

def write_file(out_rel, html_text):
    out_path = os.path.join(SITE_DIR, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_text)

# ----------------------------------------------------------------------
# Home page — auto-generated welcome + index, not copied from any single doc
# ----------------------------------------------------------------------

def build_home():
    groups = {}
    for src, out, title, section in STUDENT_MANIFEST:
        groups.setdefault(section, []).append((out, title))

    cards = []
    for section in STUDENT_SECTION_ORDER:
        cls = SECTION_CLASS.get(section, "")
        icon = SECTION_ICON.get(section, "")
        items = "".join(
            f'<li><a href="{relhref("index.html", out)}">{html.escape(title)}</a></li>'
            for out, title in groups.get(section, [])
        )
        cards.append(f'<div class="home-card {cls}"><h3>{icon} {html.escape(section)}</h3><ul>{items}</ul></div>')

    lesson1_href = relhref("index.html", "tollway/lessons/01-cdp-standup.html")
    content = f"""
<div class="hero">
  <div class="eyebrow">Hightouch 101 &middot; Composed Digital</div>
  <h1>Welcome to TollWay</h1>
  <p>You're about to learn Hightouch end-to-end by building a real customer data platform for
  TollWay — a fictional Australian toll-road operator with 1,000 customers, 10,000 trips, and a
  Braze account to activate against. Every lesson is a real click path, not a slide deck: by the
  end you'll have stood up a CDP, built a single customer view, and sent real Braze campaigns off
  real segments you built yourself.</p>
</div>
<a class="cta" href="{lesson1_href}">Start Lesson 1 &rarr;</a>
<div class="home-grid">
{''.join(cards)}
</div>
"""
    nav_html = render_nav("index.html", STUDENT_MANIFEST, STUDENT_SECTION_ORDER)
    write_file("index.html", render_page("Home", content, "index.html", nav_html, relhref("index.html", "index.html")))

def build_admin_home():
    groups = {}
    for src, out, title, section in ADMIN_MANIFEST:
        groups.setdefault(section, []).append((out, title))
    items = "".join(
        f'<li><a href="{relhref("admin/index.html", out)}">{html.escape(title)}</a></li>'
        for out, title in groups.get("Reset", [])
    )
    content = f"""
<h1>Admin — Reset &amp; Teardown</h1>
<p>Not part of the student lesson flow. These are the manual reset checklists for wiping the
shared Hightouch/Braze/Snowflake sandbox between learners — see <code>course/reset/README.md</code>
in the repo for why this is a manual checklist rather than a script.</p>
<div class="home-grid"><div class="home-card reset"><h3>Reset checklists</h3><ul>{items}</ul></div></div>
"""
    nav_html = render_nav("admin/index.html", ADMIN_MANIFEST, ADMIN_SECTION_ORDER)
    write_file("admin/index.html", render_page("Admin", content, "admin/index.html", nav_html,
                                                relhref("admin/index.html", "index.html"), banner=ADMIN_BANNER))

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def build_manifest_pages(manifest, section_order, home_target):
    for src, out, title, section in manifest:
        src_path = os.path.join(ROOT, src)
        if not os.path.isfile(src_path):
            print(f"MISSING SOURCE: {src}", file=sys.stderr)
            continue
        with open(src_path, encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")
        blocks = parse_blocks(lines)
        if blocks and blocks[0]["type"] == "header" and blocks[0]["level"] == 1:
            blocks = blocks[1:]
        body_html = render_blocks(blocks, src, out)
        content = f"<h1>{html.escape(title)}</h1>\n{body_html}"
        nav_html = render_nav(out, manifest, section_order)
        banner = ADMIN_BANNER if manifest is ADMIN_MANIFEST else ""
        write_file(out, render_page(title, content, out, nav_html, relhref(out, home_target), banner=banner))

def build():
    if os.path.isdir(SITE_DIR):
        for dirpath, dirnames, filenames in os.walk(SITE_DIR):
            for fn in filenames:
                if fn.endswith(".html"):
                    os.remove(os.path.join(dirpath, fn))

    build_home()
    build_manifest_pages(STUDENT_MANIFEST, STUDENT_SECTION_ORDER, "index.html")

    build_admin_home()
    build_manifest_pages(ADMIN_MANIFEST, ADMIN_SECTION_ORDER, "admin/index.html")

    total = len(STUDENT_MANIFEST) + len(ADMIN_MANIFEST) + 2
    print(f"Built {total} pages into {SITE_DIR} ({len(STUDENT_MANIFEST)} student + {len(ADMIN_MANIFEST)} admin)")

if __name__ == "__main__":
    build()
