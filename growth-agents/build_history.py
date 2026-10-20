#!/usr/bin/env python3
"""Append today's public YouTube statistics to the previous artifact history."""
import csv
import datetime as dt
import json
from pathlib import Path

root = Path("growth-agents/output")
latest = json.loads((root / "latest.json").read_text(encoding="utf-8"))
history = root / "history.csv"
previous = Path("growth-agents/previous/history.csv")
fields = ["date_utc", "views", "likes", "comments", "daily_view_change"]
rows = []
if previous.exists():
    with previous.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
today = latest["checked_at_utc"][:10]
rows = [r for r in rows if r["date_utc"] != today]
last = rows[-1] if rows else None
change = latest["views"] - int(last["views"]) if last and latest["views"] is not None and last["views"] else ""
rows.append({
    "date_utc": today,
    "views": latest["views"] if latest["views"] is not None else "",
    "likes": latest["likes"] if latest["likes"] is not None else "",
    "comments": latest["comments"] if latest["comments"] is not None else "",
    "daily_view_change": change,
})
with history.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"Daily snapshot: {today}; views={latest['views']}; change since last recorded date={change if change != '' else 'N/A'}")
print("Daily view change compares snapshots and may cover more than 24 hours if a run was missed.")
