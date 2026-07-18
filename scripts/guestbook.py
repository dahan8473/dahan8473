#!/usr/bin/env python3
"""Append a sanitized guestbook entry to wall.json, then rebuild the profile
SVG so the wall shows inside the single-image profile.

Env: WALL_USER (issue author login), WALL_TITLE (issue title 'wall|message').
"""
import json
import os
import re
import subprocess
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
WALL = os.path.join(HERE, "wall.json")
MAX_ENTRIES = 8
MAX_LEN = 48

user = re.sub(r"[^A-Za-z0-9-]", "", os.environ["WALL_USER"])[:39]
title = os.environ["WALL_TITLE"]
msg = title.split("|", 1)[1] if "|" in title else ""
msg = re.sub(r"[`\x00-\x1f\x7f]", "", msg)
msg = re.sub(r"\s+", " ", msg).strip()[:MAX_LEN] or "was here"

entries = json.load(open(WALL)) if os.path.exists(WALL) else []
entries.append({"user": user, "msg": msg, "date": date.today().strftime("%b %d")})
entries = entries[-MAX_ENTRIES:]
json.dump(entries, open(WALL, "w"), indent=2)
print(f"added @{user}: {msg}")

subprocess.run(["python", os.path.join(HERE, "build_profile.py")], check=True)
