#!/usr/bin/env python3
"""Read-only Shani Dev YouTube analytics snapshot. Requires YOUTUBE_API_KEY."""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

VIDEO_ID = "3MHOr1g1N9M"
OUT = pathlib.Path("growth-agents/output/latest.json")

def main():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("YOUTUBE_API_KEY is missing. Add it as a GitHub Actions repository secret; no data fetched.", file=sys.stderr)
        return 2
    query = urllib.parse.urlencode({"part": "snippet,statistics,contentDetails", "id": VIDEO_ID, "key": key})
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?" + query, headers={"User-Agent": "AnksDharamGrowthAgent/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.load(response)
    except Exception as exc:
        print(f"YouTube API request failed: {exc}", file=sys.stderr)
        return 1
    if not payload.get("items"):
        print("Video not found or unavailable to this API key.", file=sys.stderr)
        return 1
    item = payload["items"][0]
    stats = item.get("statistics", {})
    result = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "video_id": VIDEO_ID,
        "title": item.get("snippet", {}).get("title"),
        "channel_title": item.get("snippet", {}).get("channelTitle"),
        "views": int(stats["viewCount"]) if "viewCount" in stats else None,
        "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
        "comments": int(stats["commentCount"]) if "commentCount" in stats else None,
        "source": "YouTube Data API v3 (public video statistics)",
        "limitations": "This does not provide private audience retention, traffic sources, watch time, or paid-vs-organic breakdown."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
