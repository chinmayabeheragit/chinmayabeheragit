"""Scrape the public contribution calendar (no token needed) -> data/contributions.json"""
import json, os, re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "chinmayabeheragit"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_days(user):
    r = requests.get(f"https://github.com/users/{user}/contributions",
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"(\d+) contributions?", tip.get_text(strip=True))
        counts[tip.get("for")] = int(m.group(1)) if m else 0
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        if not td.get("data-date"):
            continue
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": counts.get(td.get("id"), 0),
        })
    days.sort(key=lambda d: d["date"])
    return days


def stats(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"]) if days else None
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"] > 0:
            current += 1
        elif i == 0:
            continue  # today may still be empty
        else:
            break
    return {"total": total, "longest_streak": longest, "current_streak": current,
            "best_day": best}


if __name__ == "__main__":
    days = fetch_days(USER)
    if not days:
        raise SystemExit("No days parsed - GitHub markup may have changed.")
    OUT.parent.mkdir(exist_ok=True)
    s = stats(days)
    OUT.write_text(json.dumps({"user": USER, "days": days, "stats": s}, indent=1))
    print(f"{USER}: {len(days)} days, {s['total']} contributions")
