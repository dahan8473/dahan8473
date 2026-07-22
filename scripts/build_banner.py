#!/usr/bin/env python3
"""Generate banner-dark/light.svg and tethos-card.svg.

Run from repo root: python scripts/build_banner.py
Reads scripts/stats.json (written by the telemetry workflow; committed
defaults keep local builds working). Fail-safe rule: every element's rest
state is fully visible; animation is layered on top.
"""
import base64
import json
import os

from theme import FRAME, RADIUS

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

# ---------------------------------------------------------------- font
with open(os.path.join(HERE, "plexmono-sub.ttf"), "rb") as f:
    FONT_B64 = base64.b64encode(f.read()).decode()

FONT_FACE = (
    "@font-face { font-family:'Plex'; "
    f"src:url(data:font/truetype;base64,{FONT_B64}) format('truetype'); }}"
)
MONO = "'Plex',ui-monospace,'SF Mono',Menlo,Consolas,monospace"

# ---------------------------------------------------------------- stats
DEFAULT_STATS = {
    "contributions": 700,
    "streak": 1,
    "last_repo": "tsi-website",
    "last_ago": "today",
}
try:
    with open(os.path.join(HERE, "stats.json")) as f:
        STATS = {**DEFAULT_STATS, **json.load(f)}
except Exception:
    STATS = DEFAULT_STATS


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- portrait
def ascii_portrait(cols=58, bg_cut=147, floor=90, gamma=1.0):
    """Negative-space portrait: face rendered in bright chars, hair + bright
    passport background dropped to black. avatar.png is a face crop; the bright
    background is flood-filled away from the border (hair walls it off from the
    face), then only the face highlights survive as dense characters."""
    from collections import deque

    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(os.path.join(HERE, "avatar.png")).convert("L")
    img = img.filter(ImageFilter.MedianFilter(3))
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = img.filter(ImageFilter.UnsharpMask(radius=6, percent=180, threshold=2))
    a = np.asarray(img).astype(np.float32)

    # flood-fill the bright background from the border; hair (dark) stops it
    H, W = a.shape
    bright = a > bg_cut
    seen = np.zeros_like(bright)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if bright[y, x]:
                q.append((y, x)); seen[y, x] = True
    for y in range(H):
        for x in (0, W - 1):
            if bright[y, x] and not seen[y, x]:
                q.append((y, x)); seen[y, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and bright[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    a[seen] = 0

    # crush hair/shadow below floor, stretch the face band, gamma-brighten
    a = np.clip((a - floor) / (bg_cut - floor), 0, 1) ** gamma
    im = Image.fromarray((a * 255).astype(np.uint8))

    w, h = im.size
    rows = max(1, round(cols * (h / w) * 0.52))
    im = im.resize((cols, rows))
    px = np.asarray(im)
    ramp = " .:-=+*#%@@"  # bright pixel -> dense char (face lit, black elsewhere)
    lines = []
    for r in range(rows):
        lines.append("".join(
            ramp[min(int(px[r, c]) * (len(ramp) - 1) // 255, len(ramp) - 1)] for c in range(cols)
        ))
    return lines


# ---------------------------------------------------------------- LED name
FONT5 = {
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    " ": ["00", "00", "00", "00", "00", "00", "00"],
}


def name_rects(x0, y0, cell=11, gap=2):
    pitch = cell + gap
    out, col0 = [], 0
    for ch in "DAVID LIU":
        bmp = FONT5[ch]
        for r, bits in enumerate(bmp):
            for c, bit in enumerate(bits):
                if bit == "1":
                    out.append(
                        f'<rect class="px" x="{x0 + (col0 + c) * pitch}" '
                        f'y="{y0 + r * pitch}" width="{cell}" height="{cell}" rx="2"/>'
                    )
        col0 += len(bmp[0]) + 1
    return "\n    ".join(out)


# ---------------------------------------------------------------- typing line
PHRASES = [
    "building bumbot: job hunt on autopilot",
    "shipping free software for nonprofits",
    "running a 24/7 agent on a mac mini",
    "open davidliu.work",
]


def typing_block(x, y, fs=13):
    """Independent repeating wipe loops, one 4s window each in a 16s cycle.
    Rest state: phrase 0 visible (fail-safe if SMIL never runs)."""
    out = []
    n = len(PHRASES)
    cycle = 4 * n
    for i, ph in enumerate(PHRASES):
        w = round(len(ph) * fs * 0.6) + 6
        rest = w if i == 0 else 0
        out.append(
            f'<clipPath id="tc{i}"><rect x="{x}" y="{y - fs}" width="{rest}" height="{fs + 8}">'
            f'<animate attributeName="width" values="0;{w};{w};0;0" keyTimes="0;0.09;0.22;0.25;1" '
            f'dur="{cycle}s" begin="{4 * i}s" repeatCount="indefinite"/></rect></clipPath>'
        )
    defs = "\n    ".join(out)
    texts = "\n  ".join(
        f'<g clip-path="url(#tc{i})"><text class="typ" x="{x}" y="{y}" xml:space="preserve">{esc(ph)}</text></g>'
        for i, ph in enumerate(PHRASES)
    )
    return defs, texts


# ---------------------------------------------------------------- themes
THEMES = {
    "dark": dict(
        head="#79c0ff", dim="#3f7fb8", menu="#274966", sel="#a5d6ff",
        px="#58a6ff", ok="#a5d6ff", okb="#58a6ff", live="#f0d861",
        portrait="#6cb6ff", rule="#1b3a5c", scan="#a5d6ff", scan_op=".07",
        glow=True,
    ),
    "light": dict(
        head="#0969da", dim="#57606a", menu="#8c959f", sel="#0550ae",
        px="#0969da", ok="#0550ae", okb="#218bff", live="#9a6700",
        portrait="#0a3069", rule="#d0d7de", scan="#0969da", scan_op=".06",
        glow=False,
    ),
}


def banner(theme_name):
    t = THEMES[theme_name]
    port = ascii_portrait()
    p_lines = "\n  ".join(
        f'<text class="port" x="36" y="{94 + i * 6.4:.1f}" xml:space="preserve">{esc(ln)}</text>'
        for i, ln in enumerate(port)
    )
    rects = name_rects(280, 84)
    tdefs, ttexts = typing_block(300, 316)

    l3 = f"{STATS['contributions']} contributions past year · {STATS['streak']} day streak"
    l4 = f"last push: {STATS['last_repo']} · {STATS['last_ago']}"

    glow_layer = (
        '<g filter="url(#glow)" opacity=".5"><use href="#pxname"/></g>' if t["glow"] else ""
    )

    css = f"""
    {FONT_FACE}
    text {{ font-family:{MONO}; }}
    .h    {{ fill:{t['head']}; font-size:13px; }}
    .dim  {{ fill:{t['dim']}; font-size:13px; }}
    .menu {{ fill:{t['menu']}; font-size:12px; letter-spacing:2px; }}
    .sel  {{ fill:{t['sel']}; font-size:12px; letter-spacing:2px; }}
    .px   {{ fill:{t['px']}; }}
    .port {{ fill:{t['portrait']}; font-size:6.4px; opacity:.95; }}
    .ok   {{ fill:{t['ok']}; font-size:13.5px; opacity:0; animation:on .01s steps(1) forwards; }}
    .okb  {{ fill:{t['okb']}; }}
    .liv  {{ fill:{t['live']}; }}
    .typ  {{ fill:{t['ok']}; font-size:13px; }}
    .pr   {{ fill:{t['okb']}; font-size:13px; }}
    .d1 {{ animation-delay:.7s; }} .d2 {{ animation-delay:.9s; }}
    .d3 {{ animation-delay:1.1s; }} .d4 {{ animation-delay:1.3s; }}
    .cur  {{ animation:blink 1.1s steps(1) infinite; }}
    .glitch {{ animation:glitch 7s steps(1) 3s infinite; }}
    .sweep  {{ animation:sweep 9s linear infinite; }}
    @keyframes on    {{ to {{ opacity:1; }} }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    @keyframes glitch {{
      0%,96.5%,98%,100% {{ transform:translate(0,0); }}
      97%   {{ transform:translate(3px,-1px); }}
      97.5% {{ transform:translate(-3px,1px); }}
    }}
    @keyframes sweep {{ from {{ transform:translateY(-40px); }} to {{ transform:translateY(390px); }} }}
    @media (prefers-reduced-motion) {{
      .ok {{ opacity:1; animation:none; }}
      .glitch, .sweep, .cur {{ animation:none; }}
    }}"""

    fr = FRAME[theme_name]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 380">
  <style>{css}
  </style>
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['scan']}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{t['scan']}" stop-opacity="{t['scan_op']}"/>
      <stop offset="1" stop-color="{t['scan']}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="frame"><rect x="0" y="0" width="960" height="380" rx="{RADIUS}"/></clipPath>
    {tdefs}
  </defs>

  <rect x="1" y="1" width="958" height="378" rx="{RADIUS}" fill="{fr['bg']}" stroke="{fr['border']}"/>
  <g clip-path="url(#frame)">
  <text class="h" x="36" y="26" xml:space="preserve">DAVIDLIU BIOS (TM)  COPYRIGHT (C) 2026</text>
  <text class="dim" x="924" y="26" text-anchor="end" xml:space="preserve">PORT......3000</text>
  <line x1="36" y1="40" x2="924" y2="40" stroke="{t['rule']}"/>
  <text class="sel" x="36" y="62">&gt; WHOAMI</text>
  <text class="menu" x="150" y="62">PROJECTS</text>
  <text class="menu" x="300" y="62">STACK</text>
  <text class="menu" x="400" y="62">COMMITS</text>
  <text class="menu" x="530" y="62">WALL</text>
  <text class="menu" x="924" y="62" text-anchor="end" xml:space="preserve">MEM TEST: 640K OK</text>

  {p_lines}
  <text class="dim" x="36" y="{94 + len(port) * 6.4 + 12:.0f}" xml:space="preserve">[ SELF TEST: PASS ]</text>

  <g class="glitch">
    {glow_layer}
    <g id="pxname">
    {rects}
    </g>
  </g>

  <text class="ok d1" x="280" y="210" xml:space="preserve"><tspan class="okb">[ OK ]</tspan>  swe @ western university · 4th year</text>
  <text class="ok d2" x="280" y="232" xml:space="preserve"><tspan class="okb">[ OK ]</tspan>  swe intern @ j.d. power · founder &amp; president @ tethos</text>
  <text class="ok d3" x="280" y="254" xml:space="preserve"><tspan class="liv">[LIVE]</tspan>  {esc(l3)}</text>
  <text class="ok d4" x="280" y="276" xml:space="preserve"><tspan class="liv">[LIVE]</tspan>  {esc(l4)}</text>

  <text class="pr" x="280" y="316">$</text>
  <rect class="cur" x="291" y="305" width="6" height="13" fill="{t['okb']}"/>
  {ttexts}

  <rect class="sweep" x="0" y="0" width="960" height="34" fill="url(#scan)"/>
  </g>
  <rect x="1" y="1" width="958" height="378" rx="{RADIUS}" fill="none" stroke="{fr['border']}"/>
</svg>
"""


# ---------------------------------------------------------------- card
def card():
    css = f"""
    {FONT_FACE}
    .lab {{ font-family:-apple-system,'Segoe UI',system-ui,sans-serif; font-weight:700; font-size:15px; fill:#e6edf3; }}
    .val {{ font-family:{MONO}; font-size:15px; fill:#c9d1d9; }}
    .logo{{ font-family:{MONO}; font-weight:700; font-size:22px; fill:#ffffff; }}
    .dot   {{ animation:pulse 2s ease infinite; }}
    .sheen {{ animation:sheen 6s linear infinite; }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.25; }} }}
    @keyframes sheen {{ from {{ transform:translateX(-500px); }} to {{ transform:translateX(1500px); }} }}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 350">
  <style>{css}
  </style>
  <defs>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#ffffff" stop-opacity=".05"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card"><rect x="8" y="8" width="944" height="334" rx="18"/></clipPath>
  </defs>
  <rect x="8" y="8" width="944" height="334" rx="18" fill="#05070a" stroke="#30363d"/>

  <text class="logo" x="48" y="70">▞▚ tethos</text>
  <line x1="230" y1="36" x2="230" y2="88" stroke="#30363d"/>
  <text class="lab" x="260" y="52">Org</text>
  <text class="val" x="260" y="76">~tethos-association</text>
  <line x1="560" y1="36" x2="560" y2="88" stroke="#30363d"/>
  <text class="lab" x="590" y="52">Class</text>
  <text class="val" x="590" y="76">Nonprofit · federally incorporated</text>

  <line x1="32" y1="108" x2="928" y2="108" stroke="#21262d"/>
  <text class="lab" x="48" y="140">Mission</text>
  <text class="val" x="48" y="163">students building free software for nonprofits</text>
  <text class="lab" x="48" y="196">Fleet</text>
  <text class="val" x="48" y="219">100+ student devs · 2 chapters (western · ubc) · 20+ projects · $300k+ saved</text>
  <text class="lab" x="48" y="252">Clients</text>
  <text class="val" x="48" y="275">world vision · plan international · fund homecare · london children's museum</text>

  <line x1="32" y1="295" x2="928" y2="295" stroke="#21262d"/>
  <text class="lab" x="48" y="318">Role</text>
  <text class="val" x="48" y="336">founder &amp; president</text>
  <line x1="268" y1="306" x2="268" y2="340" stroke="#30363d"/>
  <text class="lab" x="288" y="318">Incorporated</text>
  <text class="val" x="288" y="336">10/05/2025</text>
  <line x1="508" y1="306" x2="508" y2="340" stroke="#30363d"/>
  <text class="lab" x="528" y="318">Status</text>
  <circle class="dot" cx="536" cy="331" r="4" fill="#58a6ff"/>
  <text class="val" x="548" y="336">active</text>
  <line x1="748" y1="306" x2="748" y2="340" stroke="#30363d"/>
  <text class="lab" x="768" y="318">Endpoint</text>
  <text class="val" x="768" y="336">tethos.ca</text>

  <g clip-path="url(#card)">
    <rect class="sheen" x="0" y="8" width="300" height="334" fill="url(#shine)" transform="skewX(-20)"/>
  </g>
</svg>
"""


os.makedirs(ASSETS, exist_ok=True)
for name in ("dark", "light"):
    with open(os.path.join(ASSETS, f"banner-{name}.svg"), "w") as f:
        f.write(banner(name))
print("built: banner-dark.svg banner-light.svg")
print("stats:", STATS)
