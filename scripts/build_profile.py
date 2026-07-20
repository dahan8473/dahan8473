#!/usr/bin/env python3
"""Compose the whole profile into ONE svg per theme (assets/profile-{d,l}.svg).

Nests the already-built panels (banner, section headers, stack, snake) as inner
<svg> at stacked y-offsets, and renders the work list + wall log as native SVG
text so nothing breaks the frame. Everything is one <img> tag in the README;
clickable links live in a compact markdown row below it.

Run after build_banner / build_headers / build_stack / build_snake.
"""
import base64
import json
import os
import re

from theme import FRAME, RADIUS

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

with open(os.path.join(HERE, "plexmono-sub.ttf"), "rb") as f:
    FONT_B64 = base64.b64encode(f.read()).decode()
FONT_FACE = ("@font-face{font-family:'Plex';"
             f"src:url(data:font/truetype;base64,{FONT_B64}) format('truetype');}}")
MONO = "'Plex',ui-monospace,'SF Mono',Menlo,Consolas,monospace"

GAP = 14          # vertical gap between panels
WIDTH = 960

PROJECTS = [
    ("tethos.ca", "solo-built platform for a 100-dev nonprofit · Next.js · Supabase · FastAPI · 400+ users", ""),
    ("tsi brain", "rag engine answering org questions with citations · pgvector · delta re-indexing", "private"),
    ("bumbot", "applies to jobs for you: scrapes, scores, writes, submits · Playwright · llm", "working"),
    ("biopilot", "turns drone footage into crop-health maps · computer vision · deck.gl", "won telus hackathon"),
    ("snake-and-commits", "your contribution graph as a real game of snake — the animation above", "open source"),
    ("kunlun", "a fashion label built on chinese myth: brand + storefront · Next.js", "in progress"),
    ("deja-view", "pinterest board in, 3d objects in your room out · three.js", "hackathon"),
    ("clawdash", "terminal-ui mission control for a 24/7 ai agent · Next.js · websockets", ""),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def piece(name):
    """Return (inner_svg, W, H) for a built panel, stripped of its <svg> wrapper."""
    s = open(os.path.join(ASSETS, name)).read()
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s)
    W, H = float(m.group(1)), float(m.group(2))
    inner = s[s.index(">", s.index("<svg")) + 1: s.rindex("</svg>")]
    return inner, W, H


def nest(name, y):
    inner, W, H = piece(name)
    h = WIDTH * H / W
    return f'<svg x="0" y="{y:.1f}" width="{WIDTH}" height="{h:.1f}" viewBox="0 0 {W:g} {H:g}">{inner}</svg>', h


def worklist_svg(theme, y):
    t = FRAME[theme]
    name_col = "#e6edf3" if theme == "dark" else "#1f2328"
    desc_col = "#9aa7b4" if theme == "dark" else "#57606a"
    row_h = 25
    rows = []
    for i, (nm, desc, tag) in enumerate(PROJECTS):
        ry = 20 + i * row_h
        tagsvg = f'<tspan fill="{t["accent"]}"> · {esc(tag)}</tspan>' if tag else ""
        rows.append(
            f'<text x="10" y="{ry}" font-size="14.5">'
            f'<tspan fill="{name_col}" font-weight="700">{esc(nm)}</tspan>'
            f'<tspan fill="{desc_col}">  {esc(desc)}</tspan>{tagsvg}</text>'
        )
    h = 20 + len(PROJECTS) * row_h
    body = f'<g transform="translate(0,{y:.1f})" font-family="{MONO}">' + "".join(rows) + "</g>"
    return body, h


def wall_svg(theme, y):
    t = FRAME[theme]
    entries = json.load(open(os.path.join(HERE, "wall.json")))[-8:]
    prompt_col = t["accent"]
    at_col = "#e6edf3" if theme == "dark" else "#1f2328"
    msg_col = "#9aa7b4" if theme == "dark" else "#57606a"
    lh = 22
    lines = [f'<text x="10" y="20" font-size="14" fill="{prompt_col}">$ cat /var/log/wall</text>']
    for i, e in enumerate(entries):
        ry = 20 + (i + 1) * lh
        lines.append(
            f'<text x="26" y="{ry}" font-size="14">'
            f'<tspan fill="{at_col}">@{esc(e["user"])}</tspan>'
            f'<tspan fill="{msg_col}">: {esc(e["msg"])}  ({esc(e["date"])})</tspan></text>'
        )
    h = 20 + (len(entries) + 1) * lh
    body = f'<g transform="translate(0,{y:.1f})" font-family="{MONO}">' + "".join(lines) + "</g>"
    return body, h


def compose(theme):
    t = FRAME[theme]
    parts, y = [], 0

    def add_panel(name):
        nonlocal y
        svg, h = nest(name, y)
        parts.append(svg)
        y += h + GAP

    def add_native(fn):
        nonlocal y
        svg, h = fn(theme, y)
        parts.append(svg)
        y += h + GAP

    add_panel(f"banner-{theme}.svg")
    add_panel(f"hdr/work-{theme}.svg")
    add_native(worklist_svg)
    add_panel(f"hdr/stack-{theme}.svg")
    add_panel(f"stack-{theme}.svg")
    add_panel(f"hdr/commits-{theme}.svg")
    add_panel(f"snake-{theme}.svg")
    add_panel(f"hdr/wall-{theme}.svg")
    add_native(wall_svg)
    total_h = y - GAP + 6

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {total_h:.0f}" width="{WIDTH}">
  <style>{FONT_FACE}</style>
  {''.join(parts)}
</svg>
"""


for name in ("dark", "light"):
    with open(os.path.join(ASSETS, f"profile-{name}.svg"), "w") as f:
        f.write(compose(name))
size = os.path.getsize(os.path.join(ASSETS, "profile-dark.svg"))
print(f"built profile-dark.svg profile-light.svg ({size//1024}KB each)")
