#!/usr/bin/env python3
"""Append a sanitized guestbook entry to README between WALL markers.

Env: WALL_USER (issue author login), WALL_TITLE (issue title 'wall|message').
Keeps the newest 8 entries. Everything renders inside a code fence, so the
sanitizer only needs to kill backticks and control chars.
"""
import os
import re
from datetime import date

README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
START, END = "<!--WALL:START-->", "<!--WALL:END-->"
MAX_ENTRIES = 8
MAX_LEN = 48

user = re.sub(r"[^A-Za-z0-9-]", "", os.environ["WALL_USER"])[:39]
title = os.environ["WALL_TITLE"]
msg = title.split("|", 1)[1] if "|" in title else ""
msg = re.sub(r"[`\x00-\x1f\x7f]", "", msg)
msg = re.sub(r"\s+", " ", msg).strip()[:MAX_LEN]
if not msg:
    msg = "was here"

with open(README) as f:
    src = f.read()

block = src.split(START)[1].split(END)[0]
old = [ln for ln in block.splitlines() if ln.startswith("  @")]
entry = f"  @{user}: {msg}  ({date.today().strftime('%b %d')})"
lines = [entry] + old[: MAX_ENTRIES - 1]

new_block = "\n```text\n$ cat /var/log/wall\n" + "\n".join(lines) + "\n```\n"
out = src.split(START)[0] + START + new_block + END + src.split(END)[1]
with open(README, "w") as f:
    f.write(out)
print(f"added: {entry}")
