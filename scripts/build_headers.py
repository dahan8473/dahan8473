#!/usr/bin/env python3
"""Generate terminal-window title bars for each README section.

Each section header becomes a self-hosted SVG (dark + light) styled like a
macOS terminal window title bar: traffic-light dots + a shell prompt showing
the section's command. Output: assets/hdr/<key>-{dark,light}.svg
"""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "hdr")

with open(os.path.join(HERE, "plexmono-sub.ttf"), "rb") as f:
    FONT_B64 = base64.b64encode(f.read()).decode()
FONT_FACE = ("@font-face{font-family:'Plex';"
             f"src:url(data:font/truetype;base64,{FONT_B64}) format('truetype');}}")
MONO = "'Plex',ui-monospace,'SF Mono',Menlo,Consolas,monospace"

# key -> (command shown after the prompt)
SECTIONS = [
    ("whoami", "whoami"),
    ("building", "ps aux | grep building"),
    ("live", "open --live"),
    ("tethos", "cat tethos.id"),
    ("projects", "tree ~/projects"),
    ("stack", "cat stack.txt"),
    ("commits", "git log  # davids commits this year"),
    ("wall", "wall"),
    ("ping", "ping david"),
]

THEMES = {
    "dark": dict(bar="#161b22", stroke="#30363d", user="#58a6ff",
                 dim="#6e7681", cmd="#e6edf3"),
    "light": dict(bar="#f6f8fa", stroke="#d0d7de", user="#0969da",
                  dim="#6e7781", cmd="#1f2328"),
}
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]

H = 38
FS = 14
CHARW = FS * 0.6
PROMPT = "david@tethos ~ % "


def bar(theme, cmd):
    t = THEMES[theme]
    text = PROMPT + cmd
    w = round(84 + len(text) * CHARW + 22)
    dots = "".join(
        f'<circle cx="{20 + i * 17}" cy="{H/2}" r="5.5" fill="{c}"/>'
        for i, c in enumerate(DOTS)
    )
    ty = H / 2 + FS * 0.35
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}">
  <style>{FONT_FACE} text{{font-family:{MONO};font-size:{FS}px;}}</style>
  <rect x="1" y="1" width="{w-2}" height="{H-2}" rx="9" fill="{t['bar']}" stroke="{t['stroke']}"/>
  {dots}
  <line x1="82" y1="8" x2="82" y2="{H-8}" stroke="{t['stroke']}"/>
  <text x="96" y="{ty:.1f}"><tspan fill="{t['user']}" font-weight="700">david@tethos</tspan><tspan fill="{t['dim']}"> ~ % </tspan><tspan fill="{t['cmd']}">{cmd.replace('&','&amp;').replace('<','&lt;')}</tspan></text>
</svg>
"""


os.makedirs(OUT, exist_ok=True)
for key, cmd in SECTIONS:
    for theme in ("dark", "light"):
        with open(os.path.join(OUT, f"{key}-{theme}.svg"), "w") as f:
            f.write(bar(theme, cmd))
print(f"built {len(SECTIONS)} header pairs")
