#!/usr/bin/env python3
"""Graphical stack component: a grid of monochrome tech logos in the blue
terminal theme. Logo paths are committed in logos.json (simple-icons, CC0),
so the build needs no network. Output: assets/stack-{dark,light}.svg
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

with open(os.path.join(HERE, "plexmono-sub.ttf"), "rb") as f:
    FONT_B64 = base64.b64encode(f.read()).decode()
FONT_FACE = ("@font-face{font-family:'Plex';"
             f"src:url(data:font/truetype;base64,{FONT_B64}) format('truetype');}}")
MONO = "'Plex',ui-monospace,'SF Mono',Menlo,Consolas,monospace"

LOGOS = json.load(open(os.path.join(HERE, "logos.json")))

COLS = 5
CELL_W, CELL_H = 184, 92
ICON = 30
PAD = 20
TITLE_H = 40

THEMES = {
    "dark": dict(card="#05070a", stroke="#30363d", icon="#58a6ff",
                 label="#8b98a5", title="#e6edf3", accent="#58a6ff"),
    "light": dict(card="#ffffff", stroke="#d0d7de", icon="#0969da",
                  label="#57606a", title="#1f2328", accent="#0969da"),
}


def build(theme_name):
    t = THEMES[theme_name]
    rows = (len(LOGOS) + COLS - 1) // COLS
    w = PAD * 2 + COLS * CELL_W
    h = PAD * 2 + TITLE_H + rows * CELL_H

    cells = []
    for i, lg in enumerate(LOGOS):
        r, c = divmod(i, COLS)
        cx = PAD + c * CELL_W + CELL_W / 2
        cy = PAD + TITLE_H + r * CELL_H + 30
        s = ICON / 24.0
        tx = cx - ICON / 2
        ty = cy - ICON / 2
        cells.append(
            f'<g transform="translate({tx:.1f},{ty:.1f}) scale({s:.3f})">'
            f'<path d="{lg["path"]}" fill="{t["icon"]}"/></g>'
            f'<text class="lab" x="{cx:.1f}" y="{cy + 32:.1f}" text-anchor="middle">{lg["label"]}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <style>
    {FONT_FACE}
    .lab {{ font-family:{MONO}; font-size:12px; fill:{t['label']}; }}
    .ttl {{ font-family:{MONO}; font-size:15px; font-weight:700; fill:{t['title']}; }}
    .cmt {{ font-family:{MONO}; font-size:13px; fill:{t['accent']}; }}
  </style>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{t['card']}" stroke="{t['stroke']}"/>
  <text class="ttl" x="{PAD+4}" y="{PAD+24}">stack</text>
  <text class="cmt" x="{w-PAD-4}" y="{PAD+24}" text-anchor="end"># what i build with</text>
  <line x1="{PAD}" y1="{PAD+TITLE_H-8}" x2="{w-PAD}" y2="{PAD+TITLE_H-8}" stroke="{t['stroke']}"/>
  {chr(10).join('  ' + c for c in cells)}
</svg>
"""


os.makedirs(ASSETS, exist_ok=True)
for name in ("dark", "light"):
    with open(os.path.join(ASSETS, f"stack-{name}.svg"), "w") as f:
        f.write(build(name))
print(f"built stack-dark.svg stack-light.svg ({len(LOGOS)} logos)")
