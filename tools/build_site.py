#!/usr/bin/env python3
"""
build_site.py — generates the hightouch-101 multi-page presentation site.

Reads every .md doc under course/ and business-packs/tollway/ (CLAUDE.md files
excluded — those are Claude/Johan working conventions, not colleague-facing
content) and renders them into a shared-template static site under docs/.

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
cross-page links by matching against the manifest below — regardless of how
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
# Manifest — every page in the site. (src, out, title, section)
#   src: path relative to ROOT
#   out: path relative to SITE_DIR (mirrors src's shape, "business-packs/"
#        prefix dropped for readability — link resolution is computed from
#        this manifest, not from the source file's own relative-path text,
#        so the exact shape here doesn't have to match source depth)
# ----------------------------------------------------------------------

MANIFEST = [
    ("course/syllabus.md", "course/syllabus.html", "Syllabus", "Course"),
    ("course/diagrams/architecture-overview.md", "course/diagrams/architecture-overview.html", "Generic Architecture", "Course"),
    ("course/diagrams/course-flow.md", "course/diagrams/course-flow.html", "Generic Course Flow", "Course"),
    ("course/recipes/hightouch-model-recipes.md", "course/recipes/hightouch-model-recipes.html", "Hightouch Model Recipes", "Course"),
    ("course/recipes/hightouch-sync-recipes.md", "course/recipes/hightouch-sync-recipes.html", "Hightouch Sync Recipes", "Course"),
    ("course/recipes/braze-canvas-recipes.md", "course/recipes/braze-canvas-recipes.html", "Braze Canvas Recipes", "Course"),
    ("course/reset/README.md", "course/reset/index.html", "Reset — Index", "Course"),
    ("course/reset/warehouse-reset-template.md", "course/reset/warehouse-reset-template.html", "Warehouse Reset Template", "Course"),
    ("course/reset/hightouch-braze-checklist-template.md", "course/reset/hightouch-braze-checklist-template.html", "Hightouch + Braze Checklist Template", "Course"),

    ("business-packs/tollway/brief.md", "tollway/brief.html", "Business Brief", "TollWay"),
    ("business-packs/tollway/use-cases.md", "tollway/use-cases.html", "Use Cases", "TollWay"),
    ("business-packs/tollway/dictionary/README.md", "tollway/dictionary/index.html", "Dictionary — Index", "TollWay Dictionary"),
    ("business-packs/tollway/dictionary/tables.md", "tollway/dictionary/tables.html", "Table Dictionary", "TollWay Dictionary"),
    ("business-packs/tollway/dictionary/relationships.md", "tollway/dictionary/relationships.html", "Relationships & Diagrams", "TollWay Dictionary"),
    ("business-packs/tollway/dictionary/cheatsheet.md", "tollway/dictionary/cheatsheet.html", "Diagnostic Cheatsheet", "TollWay Dictionary"),
    ("business-packs/tollway/dictionary/inconsistencies.md", "tollway/dictionary/inconsistencies.html", "Known Deviations", "TollWay Dictionary"),

    ("business-packs/tollway/lessons/01-cdp-standup.md", "tollway/lessons/01-cdp-standup.html", "Lesson 1 — Stand Up the CDP", "TollWay Lessons"),
    ("business-packs/tollway/lessons/02-single-customer-view.md", "tollway/lessons/02-single-customer-view.html", "Lesson 2 — Single Customer View", "TollWay Lessons"),
    ("business-packs/tollway/lessons/03-destinations.md", "tollway/lessons/03-destinations.html", "Lesson 3 — Destinations (roadmap)", "TollWay Lessons"),
    ("business-packs/tollway/lessons/04-segments-and-activation.md", "tollway/lessons/04-segments-and-activation.html", "Lesson 4 — Segments + Activation (roadmap)", "TollWay Lessons"),
    ("business-packs/tollway/lessons/05-closing-the-loop.md", "tollway/lessons/05-closing-the-loop.html", "Lesson 5 — Closing the Loop (roadmap)", "TollWay Lessons"),

    ("business-packs/tollway/reset/reset-tollway-checklist.md", "tollway/reset/reset-tollway-checklist.html", "TollWay Reset Checklist", "TollWay"),
]

SECTION_ORDER = ["Course", "TollWay", "TollWay Dictionary", "TollWay Lessons"]

# ----------------------------------------------------------------------
# Link resolution — match an inline-code path reference (however many
# ../ segments it has, correct or not) to a manifest entry by longest
# matching path suffix.
# ----------------------------------------------------------------------

def build_link_index():
    index = {}
    for src, out, title, section in MANIFEST:
        parts = src.split("/")
        for i in range(len(parts)):
            suffix = "/".join(parts[i:])
            index.setdefault(suffix, []).append((src, out, title))
    return index

LINK_INDEX = build_link_index()

def resolve_md_reference(raw_text, current_src):
    """raw_text is the exact content of a `...` code span. Returns the
    manifest 'out' path if raw_text looks like a reference to a known doc,
    else None."""
    if not raw_text.endswith(".md"):
        return None
    cleaned = raw_text.lstrip("./")
    # try longest suffix match first
    candidates = []
    parts = cleaned.split("/")
    for i in range(len(parts)):
        suffix = "/".join(parts[i:])
        if suffix in LINK_INDEX:
            candidates.extend(LINK_INDEX[suffix])
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0][1]
    # ambiguous bare filename — prefer a match in the same directory as the referencing file
    current_dir = os.path.dirname(current_src)
    for src, out, title in candidates:
        if os.path.dirname(src) == current_dir:
            return out
    return candidates[0][1]

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
    # 1. pull out code spans first so bold/italic/escaping never touch their content
    spans = []
    def stash_code(m):
        spans.append(m.group(1))
        return f"\x00CODE{len(spans) - 1}\x00"
    text = CODE_SPAN_RE.sub(stash_code, text)

    # 2. bold / italic on the remaining text
    text = BOLD_RE.sub(lambda m: f"\x00B{len(spans)}\x00{m.group(1)}\x00/B\x00", text)
    # (bold marker content itself may need escaping later — handle by re-walking)

    # 3. escape everything that isn't a placeholder, then rebuild
    def escape_and_restore(s):
        # escape base text
        out = []
        i = 0
        pattern = re.compile(r"\x00(CODE)(\d+)\x00|\x00(B)(\d+)\x00(.*?)\x00/B\x00", re.S)
        last = 0
        for m in pattern.finditer(s):
            out.append(html.escape(s[last:m.start()]))
            if m.group(1) == "CODE":
                idx = int(m.group(2))
                raw = spans[idx]
                target = resolve_md_reference(raw, current_src)
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
    result = ITALIC_RE.sub(lambda m: f"<em>{html.escape(m.group(1))}</em>", result) if "\x00" not in result else result
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
    """Returns a list of block dicts. lines: list of raw source lines (no
    trailing newline), already de-indented to the current nesting level."""
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
            i += 1  # skip closing fence
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
                # gather continuation / nested lines: indented deeper than the marker line
                while i < n:
                    nxt = lines[i]
                    if nxt.strip() == "":
                        # blank line inside a list item's fenced code block is fine; otherwise ends item on next non-continuation
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

        # paragraph: consecutive plain lines until blank or new block signal
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
                # first block of an item, if a paragraph, renders inline (no wrapping <p>) for tight lists
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
  <div class="brand"><span class="eyebrow">Hightouch 101</span><br>TollWay</div>
  <nav>
{nav}
  </nav>
</aside>
<main class="page-content">
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
  --muted:#cfd0e0;--purple:#6C5CE7;--cyan:#00D4FF;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:Poppins,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.shell{display:flex;min-height:100vh}
.sidebar{width:260px;flex:0 0 260px;background:var(--card);border-right:1px solid var(--line);padding:22px 18px;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{font-size:15px;font-weight:700;margin-bottom:18px;line-height:1.4}
.brand .eyebrow{font-size:10.5px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:var(--purple)}
.navgroup{margin-bottom:16px}
.navgroup .gh{font-size:10.5px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted);margin:14px 0 6px}
.navgroup a{display:block;color:var(--muted);text-decoration:none;font-size:13px;padding:5px 8px;border-radius:7px;margin-bottom:1px}
.navgroup a:hover{background:rgba(255,255,255,.05);color:var(--txt)}
.navgroup a.active{background:rgba(108,92,231,.18);color:var(--cyan);font-weight:600}
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
.home-hero{max-width:820px;margin-bottom:30px}
.home-hero .eyebrow{font-size:11px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:var(--purple);margin-bottom:6px}
.home-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;max-width:1300px}
.home-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.home-card h3{margin-top:0;color:var(--txt);font-size:15px}
.home-card ul{margin:0;padding-left:20px}
.home-card a{color:var(--cyan);text-decoration:none;font-size:14px}
.home-card a:hover{text-decoration:underline}
.home-card li{margin-bottom:5px}
@media(max-width:900px){
  .shell{flex-direction:column}
  .sidebar{width:100%;flex:none;position:relative;height:auto}
  main.page-content{padding:24px 20px}
  .home-grid{grid-template-columns:1fr}
}
"""

def render_nav(active_out):
    groups = {}
    for src, out, title, section in MANIFEST:
        groups.setdefault(section, []).append((out, title))
    parts = ['    <a href="{}" class="{}">Home</a>'.format(
        relhref(active_out, "index.html"),
        "active" if active_out == "index.html" else "",
    )]
    for section in SECTION_ORDER:
        parts.append(f'  <div class="navgroup"><div class="gh">{html.escape(section)}</div>')
        for out, title in groups.get(section, []):
            cls = "active" if out == active_out else ""
            parts.append(f'    <a href="{relhref(active_out, out)}" class="{cls}">{html.escape(title)}</a>')
        parts.append("  </div>")
    return "\n".join(parts)

def render_page(title, content_html, out):
    nav = render_nav(out)
    return TEMPLATE.format(title=html.escape(title), css=CSS, nav=nav, content=content_html)

def write_file(out_rel, html_text):
    out_path = os.path.join(SITE_DIR, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_text)

# ----------------------------------------------------------------------
# Home page — auto-generated index, not copied from any single doc
# ----------------------------------------------------------------------

def build_home():
    groups = {}
    for src, out, title, section in MANIFEST:
        groups.setdefault(section, []).append((out, title))

    cards = []
    for section in SECTION_ORDER:
        items = "".join(
            f'<li><a href="{relhref("index.html", out)}">{html.escape(title)}</a></li>'
            for out, title in groups.get(section, [])
        )
        cards.append(f'<div class="home-card"><h3>{html.escape(section)}</h3><ul>{items}</ul></div>')

    content = f"""
<div class="home-hero">
  <div class="eyebrow">Hightouch 101 &middot; Composed Digital</div>
  <h1>TollWay Training Site</h1>
  <p>A fictional Australian toll-road operator, built to teach Hightouch end-to-end — standing
  up a CDP, building a single customer view, activating segments to Braze, and closing the loop
  with engagement data flowing back to the warehouse. Start with the <a href="{relhref('index.html', 'tollway/brief.html')}">Business Brief</a>
  and the <a href="{relhref('index.html', 'course/syllabus.html')}">Syllabus</a>, then work through
  the Lessons in order.</p>
</div>
<div class="home-grid">
{''.join(cards)}
</div>
"""
    write_file("index.html", render_page("Home", content, "index.html"))

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def build():
    if os.path.isdir(SITE_DIR):
        for dirpath, dirnames, filenames in os.walk(SITE_DIR):
            for fn in filenames:
                if fn.endswith(".html"):
                    os.remove(os.path.join(dirpath, fn))

    build_home()

    for src, out, title, section in MANIFEST:
        src_path = os.path.join(ROOT, src)
        if not os.path.isfile(src_path):
            print(f"MISSING SOURCE: {src}", file=sys.stderr)
            continue
        with open(src_path, encoding="utf-8") as f:
            text = f.read()
        lines = text.split("\n")
        blocks = parse_blocks(lines)
        # drop the doc's own H1 — the sidebar + page <title> already identify the page,
        # and the manifest title is used as the on-page heading for consistency
        if blocks and blocks[0]["type"] == "header" and blocks[0]["level"] == 1:
            blocks = blocks[1:]
        body_html = render_blocks(blocks, src, out)
        content = f"<h1>{html.escape(title)}</h1>\n{body_html}"
        write_file(out, render_page(title, content, out))

    print(f"Built {len(MANIFEST) + 1} pages into {SITE_DIR}")

if __name__ == "__main__":
    build()
