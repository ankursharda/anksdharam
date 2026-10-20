#!/usr/bin/env python3
"""Rate-limited evergreen Instagram promotion: one unposted public video per day.
Preserves publishing history; never manufactures engagement.
"""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path("growth-agents")
QUEUE = ROOT / "output/channel-growth-opportunities.json"
LEDGER = ROOT / "instagram-published.json"

def main():
    ranked = json.loads(QUEUE.read_text(encoding="utf-8"))
    posted = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    if not os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
        raise SystemExit("Missing INSTAGRAM_ACCESS_TOKEN; no publication attempted.")
    for video in ranked:
        vid = video["video_id"]
        if vid in posted or video.get("privacy") != "public":
            continue
        print(f"Selecting one unpromoted catalog video: {vid}")
        result = subprocess.run(["python", "growth-agents/instagram_thumbnail_post.py",
                                 "--video-id", vid, "--title", video["title"], "--publish"])
        if result.returncode != 0:
            raise SystemExit(f"Instagram publication failed for {vid}; will retry in a later run.")
        posted[vid] = {"title": video["title"], "origin": "whole-channel-rotation"}
        LEDGER.write_text(json.dumps(posted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Exactly one evergreen promotion published and recorded.")
        return
    print("No unpromoted public video in current shortlist; no post created.")

if __name__ == "__main__":
    main()
