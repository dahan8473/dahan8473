#!/usr/bin/env python3
"""Full-width terminal title bars for README sections. One shared frame spec
(theme.py) keeps every panel visually coherent. Traffic lights + prompt on the
left, a dim right-label to balance the bar. Output: assets/hdr/<key>-{d,l}.svg
"""
import base64
import os

from theme import DOTS, FRAME, RADIUS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "hdr")

with open(os.path.join(HERE, "plexmono-sub.ttf"), "rb") as f:
    FONT_B64 = base64.b64encode(f.read()).decode()
FONT_FACE = ("@font-face{font-family:'Plex';"
             f"src:url(data:font/truetype;base64,{FONT_B64}) format('truetype');}}")
MONO = "'Plex',ui-monospace,'SF Mono',Menlo,Consolas,monospace"

# key -> (command, right-aligned label)
SECTIONS = [
    ("work", "ls -t ~/projects", "what i'm building"),
    ("stack", "cat stack", "what i build with"),
    ("commits", "git log", "davids commits this year"),
    ("wall", "wall", "leave a message"),
]

W, H = 960, 40
FS = 15
PROMPT_USER = "david@tethos"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def bar(theme, cmd, right):
    t = FRAME[theme]
    dots = "".join(
        f'<circle cx="{22 + i * 18}" cy="{H/2}" r="6" fill="{c}"/>'
        for i, c in enumerate(DOTS)
    )
    ty = H / 2 + FS * 0.35
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <style>{FONT_FACE} text{{font-family:{MONO};font-size:{FS}px;}}</style>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{RADIUS}" fill="{t['bar']}" stroke="{t['border']}"/>
  {dots}
  <line x1="90" y1="9" x2="90" y2="{H-9}" stroke="{t['border']}"/>
  <text x="106" y="{ty:.1f}"><tspan fill="{t['user']}" font-weight="700">{PROMPT_USER}</tspan><tspan fill="{t['dim']}"> ~ % </tspan><tspan fill="{t['cmd']}">{esc(cmd)}</tspan></text>
  <text x="{W-22}" y="{ty:.1f}" text-anchor="end" fill="{t['dim']}">{esc(right)}</text>
</svg>
"""


os.makedirs(OUT, exist_ok=True)
for key, cmd, right in SECTIONS:
    for theme in ("dark", "light"):
        with open(os.path.join(OUT, f"{key}-{theme}.svg"), "w") as f:
            f.write(bar(theme, cmd, right))
print(f"built {len(SECTIONS)} header pairs (full-width)")
