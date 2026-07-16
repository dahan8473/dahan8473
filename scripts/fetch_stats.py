#!/usr/bin/env python3
"""Fetch live GitHub stats into scripts/stats.json for the banner build.

Runs in the telemetry workflow with GH_TOKEN set. Any failure leaves the
committed stats.json untouched so the banner never regresses to garbage.
"""
import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ["GH_TOKEN"]
USER = "dahan8473"


def gh(url, payload=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def contributions_and_streak():
    now = datetime.now(timezone.utc)
    frm = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = """
    query($login: String!, $from: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    data = gh(
        "https://api.github.com/graphql",
        {"query": q, "variables": {"login": USER, "from": frm}},
    )
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"], reverse=True)
    streak = 0
    for i, d in enumerate(days):
        if d["contributionCount"] > 0:
            streak += 1
        elif i == 0:
            continue  # today can still be zero without breaking the streak
        else:
            break
    return cal["totalContributions"], streak


def last_push():
    events = gh(f"https://api.github.com/users/{USER}/events/public?per_page=60")
    for e in events:
        if e["type"] == "PushEvent" and e["repo"]["name"] != f"{USER}/{USER}":
            repo = e["repo"]["name"].split("/")[-1]
            when = datetime.strptime(e["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
            delta = (date.today() - when).days
            ago = "today" if delta == 0 else "yesterday" if delta == 1 else f"{delta}d ago"
            return repo, ago
    return None, None


stats_path = os.path.join(HERE, "stats.json")
with open(stats_path) as f:
    stats = json.load(f)

try:
    total, streak = contributions_and_streak()
    stats["contributions"] = total
    stats["streak"] = max(streak, 1)
except Exception as e:
    print(f"contributions fetch failed, keeping previous: {e}")

try:
    repo, ago = last_push()
    if repo:
        stats["last_repo"] = repo
        stats["last_ago"] = ago
except Exception as e:
    print(f"events fetch failed, keeping previous: {e}")

with open(stats_path, "w") as f:
    json.dump(stats, f, indent=2)
print("stats:", stats)
