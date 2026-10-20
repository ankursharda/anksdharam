#!/usr/bin/env python3
"""Rotate two verified Anks Dharam highlights without changing website HTML."""
import datetime
import json
from pathlib import Path

root = Path(__file__).resolve().parent
library = json.loads((root / "post-library.json").read_text(encoding="utf-8"))
items = library["posts"]
if len(items) < 2:
    raise ValueError("At least two curated posts are required")
for item in items:
    if not all(item.get(k) for k in ("category", "title", "description")):
        raise ValueError("Each post needs a category, title and description")
    if item.get("url") and not item["url"].startswith("https://"):
        raise ValueError("Links must use HTTPS")

today = datetime.datetime.now(datetime.timezone.utc).date()
# Rotate daily among the curated posts; never generate unverified announcements.
index = (today - datetime.date(2026, 10, 20)).days % len(items)
selected = [items[index], items[(index + 1) % len(items)]]
payload = {"updated": today.isoformat(), "posts": selected}
(root / "posts.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("Published highlights:", ", ".join(p["title"] for p in selected))
