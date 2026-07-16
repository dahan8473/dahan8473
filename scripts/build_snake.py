#!/usr/bin/env python3
"""Growth snake: eats the contribution graph, grows with commit density.

Custom renderer (no snk dependency). The snake serpentines through the
year's grid; every cell with contributions gets eaten and fades; the snake
starts at 3 segments and gains a tail segment every K eats, where K is
derived from how dense the year is. Fail-safe: with animations off you see
a static contribution grid.

Outputs dist/snake-dark.svg and dist/snake-light.svg.
Needs GH_TOKEN (or falls back to `gh auth token` locally).
"""
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone

USER = "dahan8473"
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "..", "dist")

CELL, GAP, M = 11, 3, 16
PITCH = CELL + GAP
STEPS_PER_SEC = 9
PAUSE_STEPS = 24
BASE_LEN = 3

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
         "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "dark": dict(
        empty="#161b22", levels=["#161b22", "#0f4526", "#166534", "#22a04a", "#3fdd78"],
        eaten="#05070a", snake="#7ee787", head="#c8ffdb", stroke="#04140a",
    ),
    "light": dict(
        empty="#ebedf0", levels=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        eaten="#fbfcfd", snake="#116329", head="#042810", stroke="#ffffff",
    ),
}


def token():
    if os.environ.get("GH_TOKEN"):
        return os.environ["GH_TOKEN"]
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def fetch_grid():
    now = datetime.now(timezone.utc)
    frm = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = """
    query($login: String!, $from: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from) {
          contributionCalendar {
            weeks { contributionDays { contributionCount contributionLevel } }
          }
        }
      }
    }"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": USER, "from": frm}}).encode(),
        headers={"Authorization": f"Bearer {token()}", "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[LEVEL[d["contributionLevel"]] for d in w["contributionDays"]] for w in weeks]


def build(theme_name, grid):
    t = THEMES[theme_name]
    ncols = len(grid)

    # serpentine route over every cell
    route = []
    for c in range(ncols):
        rows = range(7) if c % 2 == 0 else range(6, -1, -1)
        for r in rows:
            if r < len(grid[c]):
                route.append((c, r))
    n = len(route)
    total = n + PAUSE_STEPS
    dur = total / STEPS_PER_SEC

    def pct(step):
        return round(step / total * 100, 3)

    def xy(cr):
        c, r = cr
        return M + c * PITCH, M + r * PITCH

    # eat events: step -> cell, in route order
    eats = [(i, cr) for i, cr in enumerate(route) if grid[cr[0]][cr[1]] > 0]
    total_eats = len(eats)

    # density-driven growth: bigger year -> longer snake, faster fattening
    max_len = BASE_LEN + max(4, min(13, total_eats // 10))
    slots = max_len - BASE_LEN
    per_seg = max(1, total_eats // slots) if slots else total_eats

    css, body = [], []

    # --- cells
    for c in range(ncols):
        for r in range(len(grid[c])):
            x, y = xy((c, r))
            lv = grid[c][r]
            fill = t["levels"][lv] if lv else t["empty"]
            body.append(
                f'<rect class="cell c{c}_{r}" x="{x}" y="{y}" width="{CELL}" '
                f'height="{CELL}" rx="2.5" fill="{fill}"/>'
            )
    for i, (step, (c, r)) in enumerate(eats):
        p = pct(step)
        lv = grid[c][r]
        css.append(
            f"@keyframes e{c}_{r} {{ 0%,{p}% {{ fill:{t['levels'][lv]}; }} "
            f"{min(p + 0.4, 100)}%,100% {{ fill:{t['eaten']}; }} }}\n"
            f".c{c}_{r} {{ animation: e{c}_{r} {dur:.1f}s linear infinite; }}"
        )

    # --- snake segments
    def seg_keyframes(offset):
        """transform keyframes at direction changes for path shifted by offset."""
        pts = []
        prev_dir = None
        for step in range(n):
            here = route[max(step - offset, 0)]
            nxt = route[max(min(step + 1, n - 1) - offset, 0)]
            d = (nxt[0] - here[0], nxt[1] - here[1])
            if d != prev_dir or step in (0, n - 1):
                x, y = xy(here)
                pts.append((pct(step), x, y))
                prev_dir = d
        x, y = xy(route[n - 1 - offset if n - 1 - offset >= 0 else 0])
        pts.append((100.0, x, y))
        return pts

    for i in range(max_len):
        pts = seg_keyframes(i)
        frames = " ".join(f"{p}% {{ transform:translate({x}px,{y}px); }}" for p, x, y in pts)
        color = t["head"] if i == 0 else t["snake"]
        size = CELL + 2 if i == 0 else CELL
        off = -1 if i == 0 else 0
        anims = f"m{i} {dur:.1f}s linear infinite"
        if i >= BASE_LEN:
            spawn_idx = min((i - BASE_LEN + 1) * per_seg - 1, total_eats - 1)
            sp = pct(eats[spawn_idx][0]) if eats else 0
            css.append(
                f"@keyframes g{i} {{ 0%,{sp}% {{ opacity:0; }} {min(sp + 0.3, 100)}%,100% {{ opacity:1; }} }}"
            )
            anims += f", g{i} {dur:.1f}s linear infinite"
        css.append(f"@keyframes m{i} {{ {frames} }}\n.s{i} {{ animation: {anims}; }}")
        body.append(
            f'<rect class="s{i}" x="{off}" y="{off}" width="{size}" height="{size}" '
            f'rx="3" fill="{color}" stroke="{t["stroke"]}" stroke-width="1.5"/>'
        )

    w = M * 2 + ncols * PITCH - GAP
    h = M * 2 + 7 * PITCH - GAP
    style = "\n".join(css)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">
  <style>
    @media (prefers-reduced-motion) {{ * {{ animation: none !important; }} }}
    {style}
  </style>
  {chr(10).join('  ' + b for b in body)}
</svg>
""", total_eats, max_len, per_seg


grid = fetch_grid()
os.makedirs(DIST, exist_ok=True)
for name in ("dark", "light"):
    svg, eats_n, max_len, per_seg = build(name, grid)
    with open(os.path.join(DIST, f"snake-{name}.svg"), "w") as f:
        f.write(svg)
print(f"built: {eats_n} cells to eat, grows {BASE_LEN}->{max_len} (+1 per {per_seg} eats)")
