#!/usr/bin/env python3
"""Weekly read-only competitor snapshot using public YouTube Data API v3."""
import csv
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

HANDLES = [
    "devimaa3728", "TrueRealms01", "TheDivineTales", "IndianMonk",
    "epicaifilms2024", "VedicKathaYT", "sarvatrahindutva",
    "Bhaktavatsal3", "sanatanlegendsai", "LostEchos27",
    "PuranicCodex", "dhalpritam1", "HINDUSTORIES",
]
KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    raise SystemExit("Missing YOUTUBE_API_KEY")
BASE = "https://www.googleapis.com/youtube/v3/"

def api(endpoint, **kwargs):
    kwargs["key"] = KEY
    url = BASE + endpoint + "?" + urllib.parse.urlencode(kwargs)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)

results = []
for handle in HANDLES:
    try:
        channel = api("channels", part="snippet,statistics,contentDetails", forHandle=handle)
        items = channel.get("items", [])
        if not items:
            results.append({"handle": handle, "status": "NOT_FOUND"})
            continue
        ch = items[0]
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist = api("playlistItems", part="contentDetails", playlistId=uploads, maxResults=15)
        ids = [i["contentDetails"]["videoId"] for i in playlist.get("items", [])]
        videos = api("videos", part="snippet,statistics,contentDetails", id=",".join(ids)).get("items", []) if ids else []
        ranked = sorted(videos, key=lambda v: int(v.get("statistics", {}).get("viewCount", 0)), reverse=True)
        results.append({
            "handle": handle, "status": "OK", "channel_id": ch["id"],
            "channel_title": ch["snippet"]["title"],
            "subscribers": ch["statistics"].get("subscriberCount"),
            "channel_views": ch["statistics"].get("viewCount"),
            "recent_videos_sampled": len(videos),
            "top_recent_videos": [
                {"title": v["snippet"]["title"], "video_id": v["id"],
                 "published_at": v["snippet"]["publishedAt"],
                 "views": int(v.get("statistics", {}).get("viewCount", 0))}
                for v in ranked[:5]
            ],
        })
    except Exception as exc:
        results.append({"handle": handle, "status": "ERROR", "error": str(exc)[:180]})

out = Path("growth-agents/output")
out.mkdir(parents=True, exist_ok=True)
now = dt.datetime.now(dt.timezone.utc).isoformat()
(out / "competitor-intelligence.json").write_text(
    json.dumps({"generated_at_utc": now, "sample": "latest 15 uploaded videos per channel",
                "limitations": "Public data only; recent sample is not lifetime top videos, audience overlap, CTR, or ad placement eligibility.",
                "channels": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
lines = ["# Weekly competitor intelligence", "", f"Generated: {now}",
         "Sample: up to 15 latest uploads per channel; top five ranked by public views.",
         "Not a measurement of shared audiences or advertising placement availability.", ""]
for x in results:
    lines.extend([f"## @{x['handle']} — {x['status']}", ""])
    if x["status"] == "OK":
        lines.extend([f"Channel: {x['channel_title']}", f"Subscribers: {x['subscribers']}",
                      f"Recent videos sampled: {x['recent_videos_sampled']}", ""])
        for v in x["top_recent_videos"]:
            lines.append(f"- {v['views']:,} views — {v['title']} — https://youtu.be/{v['video_id']}")
    elif x["status"] == "ERROR":
        lines.append("Temporary API error; retry next week.")
    else:
        lines.append("Handle not resolved; verify spelling.")
    lines.append("")
(out / "competitor-intelligence.md").write_text("\n".join(lines), encoding="utf-8")
print("Competitor snapshot:", len(results), "channels;", sum(x["status"] == "OK" for x in results), "resolved.")
