#!/usr/bin/env python3
"""Growth snake over the contribution graph, classic LED style.

No moving rects: grid cells light up and dim as the snake occupies them,
exactly like an LED board, so segments can never visually overlap. The
snake hunts cells sparse-to-dense (level 1 first, level 4 last), BFS
shortest path with its own body as an obstacle. Growth is intensity-
weighted: eating a brighter cell adds more growth points; every P points
adds a tail segment. Month labels and the less/more legend match the
native graph. Fail-safe: animations off = static contribution graph.

Outputs dist/snake-dark.svg and dist/snake-light.svg.
Needs GH_TOKEN (or falls back to `gh auth token` locally).
"""
import json
import os
import subprocess
import urllib.request
from bisect import bisect_right
from collections import deque
from datetime import datetime, timedelta, timezone

USER = "dahan8473"
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "..", "dist")

CELL, GAP = 11, 3
PITCH = CELL + GAP
MX, MTOP, MBOT = 16, 26, 30
STEPS_PER_SEC = 10
PAUSE_STEPS = 26
BASE_LEN = 3

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
         "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
MONTHS = ["", "jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]

THEMES = {
    "dark": dict(
        empty="#161b22", levels=["#161b22", "#0f4526", "#166534", "#22a04a", "#3fdd78"],
        eaten="#05070a", snake="#7ee787", head="#d6ffe4", text="#3fa060",
    ),
    "light": dict(
        empty="#ebedf0", levels=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        eaten="#fbfcfd", snake="#116329", head="#042810", text="#57606a",
    ),
}


def token():
    if os.environ.get("GH_TOKEN"):
        return os.environ["GH_TOKEN"]
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def fetch_weeks():
    now = datetime.now(timezone.utc)
    frm = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = """
    query($login: String!, $from: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from) {
          contributionCalendar {
            weeks { contributionDays { date contributionLevel } }
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
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def solve(grid):
    """Route sparse-to-dense with BFS body avoidance. Returns route, eats, growth."""
    ncols = len(grid)

    def neighbors(cr):
        c, r = cr
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < ncols and 0 <= nr < len(grid[nc]):
                yield (nc, nr)

    def bfs(start, goal, blocked):
        if start == goal:
            return [start]
        q, seen = deque([(start, [start])]), {start}
        while q:
            cur, path = q.popleft()
            for nb in neighbors(cur):
                if nb in seen or (nb in blocked and nb != goal):
                    continue
                if nb == goal:
                    return path + [nb]
                seen.add(nb)
                q.append((nb, path + [nb]))
        return None

    remaining = {(c, r) for c in range(ncols) for r in range(len(grid[c])) if grid[c][r] > 0}
    total_points = sum(grid[c][r] for c, r in remaining)
    max_len = BASE_LEN + max(6, min(15, total_points // 12))
    per_seg = max(2, total_points // (max_len - BASE_LEN))

    pos = min(remaining, key=lambda cr: cr[0] * 10 + abs(cr[1] - 3)) if remaining else (0, 3)
    route, eats, points = [pos], [], 0
    growth_steps = []
    if pos in remaining:
        remaining.discard(pos)
        eats.append((0, pos))
        points += grid[pos[0]][pos[1]]
    while remaining:
        cur_len = BASE_LEN + len(growth_steps)
        target = min(
            remaining,
            key=lambda cr: (grid[cr[0]][cr[1]], abs(cr[0] - pos[0]) + abs(cr[1] - pos[1])),
        )
        body = set(route[-cur_len:])
        hop = bfs(pos, target, body) or bfs(pos, target, set())
        for step in hop[1:]:
            route.append(step)
            if step in remaining:
                remaining.discard(step)
                eats.append((len(route) - 1, step))
                points += grid[step[0]][step[1]]
                while points >= (len(growth_steps) + 1) * per_seg and \
                        BASE_LEN + len(growth_steps) < max_len:
                    growth_steps.append(len(route) - 1)
        pos = route[-1]
    return route, eats, growth_steps, max_len, per_seg


def build(theme_name, grid, months, route, eats, growth_steps, max_len):
    t = THEMES[theme_name]
    ncols = len(grid)
    n = len(route)
    total = n + PAUSE_STEPS
    dur = total / STEPS_PER_SEC

    def pct(step):
        return round(step / total * 100, 3)

    def xy(c, r):
        return MX + c * PITCH, MTOP + r * PITCH

    def length_at(step):
        return BASE_LEN + bisect_right(growth_steps, step)

    # occupancy simulation -> intervals per cell
    intervals = {}
    open_iv = {}
    prev = set()
    for step in range(n):
        body = set(route[max(0, step - length_at(step) + 1): step + 1])
        for cell in body - prev:
            open_iv[cell] = step
        for cell in prev - body:
            intervals.setdefault(cell, []).append((open_iv.pop(cell), step))
        prev = body
    for cell, start in open_iv.items():
        intervals.setdefault(cell, []).append((start, total))  # hold through pause

    eaten_step = {cell: step for step, cell in eats}

    css, body_svg = [], []
    for c in range(ncols):
        for r in range(len(grid[c])):
            x, y = xy(c, r)
            lv = grid[c][r]
            base = t["levels"][lv] if lv else t["empty"]
            cell = (c, r)
            ivs = intervals.get(cell, [])
            cls = f"c{c}_{r}"
            body_svg.append(
                f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{base}"/>'
            )
            if not ivs:
                continue
            stops = [(0.0, base)]
            for a, b in ivs:
                post = t["eaten"] if (cell in eaten_step and eaten_step[cell] <= b) else base
                pa = pct(a)
                stops.append((max(pa - 0.05, 0.0), None))  # hold previous color until here
                stops.append((pa, t["head"]))
                stops.append((min(pa + 0.18, 99.9), t["snake"]))
                if b < total:
                    pb = pct(b)
                    stops.append((max(pb - 0.05, 0.0), None))
                    stops.append((pb, post))
            frames, last_color = [], base
            for p, color in stops:
                if color is None:
                    frames.append(f"{p}% {{ fill:{last_color}; }}")
                else:
                    frames.append(f"{p}% {{ fill:{color}; }}")
                    last_color = color
            frames.append(f"100% {{ fill:{last_color}; }}")
            css.append(
                f"@keyframes k{cls} {{ {' '.join(frames)} }}\n"
                f".{cls} {{ animation: k{cls} {dur:.1f}s linear infinite; }}"
            )

    # month labels
    for c, label in months:
        x, _ = xy(c, 0)
        body_svg.append(f'<text class="lab" x="{x}" y="14">{label}</text>')
    # legend
    lx = MX + ncols * PITCH - GAP - 5 * (CELL + 3) - 62
    ly = MTOP + 7 * PITCH + 8
    body_svg.append(f'<text class="lab" x="{lx - 30}" y="{ly + 9}">less</text>')
    for i in range(5):
        body_svg.append(
            f'<rect x="{lx + i * (CELL + 3)}" y="{ly}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{t["levels"][i]}"/>'
        )
    body_svg.append(f'<text class="lab" x="{lx + 5 * (CELL + 3) + 8}" y="{ly + 9}">more</text>')

    w = MX * 2 + ncols * PITCH - GAP
    h = MTOP + 7 * PITCH - GAP + MBOT
    style = "\n".join(css)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">
  <style>
    .lab {{ font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace; font-size:9.5px; fill:{t['text']}; }}
    @media (prefers-reduced-motion) {{ * {{ animation: none !important; }} }}
    {style}
  </style>
  {chr(10).join('  ' + b for b in body_svg)}
</svg>
"""


weeks = fetch_weeks()
grid = [[LEVEL[d["contributionLevel"]] for d in w["contributionDays"]] for w in weeks]
months, seen_month = [], None
for c, w in enumerate(weeks):
    m = int(w["contributionDays"][0]["date"].split("-")[1])
    if m != seen_month:
        months.append((c, MONTHS[m]))
        seen_month = m
if months and months[0][0] == 0 and len(months) > 1 and months[1][0] <= 2:
    months = months[1:]  # avoid label collision at the left edge

route, eats, growth_steps, max_len, per_seg = solve(grid)
os.makedirs(DIST, exist_ok=True)
for name in ("dark", "light"):
    svg = build(name, grid, months, route, eats, growth_steps, max_len)
    with open(os.path.join(DIST, f"snake-{name}.svg"), "w") as f:
        f.write(svg)
print(f"built: {len(eats)} cells, route {len(route)} steps, "
      f"grows {BASE_LEN}->{BASE_LEN + len(growth_steps)} (cap {max_len}, {per_seg} pts/seg)")
