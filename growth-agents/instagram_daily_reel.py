#!/usr/bin/env python3
"""Prepare a rights-approved devotional Reel candidate; never publishes."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path("growth-agents")
MANIFEST = ROOT / "instagram-reels-approved.json"
HISTORY = ROOT / "instagram-reels-history.json"
OUTPUT = ROOT / "output" / "instagram-daily-reel-preview.json"

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
    candidates = json.loads(MANIFEST.read_text(encoding="utf-8"))
    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    eligible = []
    for item in candidates:
        if not all(item.get(k) for k in ("id", "video_url", "caption_hi", "audio_rights_confirmed", "video_rights_confirmed")):
            continue
        if not item["video_url"].startswith("https://"):
            continue
        prior = [dt.date.fromisoformat(h["date"]) for h in history if h.get("id") == item["id"]]
        if prior and (today - max(prior)).days < 30:
            continue
        eligible.append(item)
    chosen = sorted(eligible, key=lambda i: i["id"])[today.toordinal() % len(eligible)] if eligible else None
    preview = {"date_ist": today.isoformat(), "account": "@anks_lifeon",
               "mode": "PREVIEW_ONLY", "published": False,
               "candidate": chosen,
               "message": "Approved Reel candidate ready for manual review." if chosen else
                          "No eligible rights-approved video. No post attempted."}
    OUTPUT.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(preview["message"])
    print("No Instagram post was published.")

if __name__ == "__main__":
    main()
