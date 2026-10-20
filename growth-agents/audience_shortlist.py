#!/usr/bin/env python3
"""Rank the user's 13 competitor channels for Shani Dev audience research.

This is an editorial relevance heuristic, NOT a prediction of clicks or a verified
Google Ads placement eligibility check.
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

HANDLES = ["devimaa3728", "TrueRealms01", "TheDivineTales", "IndianMonk",
           "epicaifilms2024", "VedicKathaYT", "sarvatrahindutva",
           "Bhaktavatsal3", "sanatanlegendsai", "LostEchos27",
           "PuranicCodex", "dhalpritam1", "HINDUSTORIES"]
KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    raise SystemExit("Missing YOUTUBE_API_KEY")

def api(endpoint, **params):
    params["key"] = KEY
    url = "https://www.googleapis.com/youtube/v3/" + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)

keywords = [
    ("shani dev", 12), ("shanidev", 12), ("shani", 8), ("शनिदेव", 12),
    ("surya dev", 10), ("suryadev", 10), ("सूर्य देव", 10),
    ("hindu mythology", 5), ("mythology", 3), ("puran", 4),
    ("animated", 4), ("animation", 4), ("ai film", 4),
    ("vedic", 3), ("sanatan", 3), ("कथा", 2),
]
rows = []
for handle in HANDLES:
    try:
        chs = api("channels", part="snippet,statistics,contentDetails", forHandle=handle).get("items", [])
        if not chs:
            rows.append({"handle": handle, "status": "NOT_FOUND"})
            continue
        ch = chs[0]
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        pl = api("playlistItems", part="contentDetails", playlistId=uploads, maxResults=30)
        ids = [x["contentDetails"]["videoId"] for x in pl.get("items", [])]
        videos = api("videos", part="snippet,statistics", id=",".join(ids)).get("items", []) if ids else []
        matches = []
        score = 0
        for v in videos:
            title = v["snippet"].get("title", "")
            desc = v["snippet"].get("description", "")[:350]
            title_l = title.casefold()
            desc_l = desc.casefold()
            points = sum(weight for word, weight in keywords if word in title_l)
            points += sum(max(1, weight // 4) for word, weight in keywords if word in desc_l and word not in title_l)
            if points:
                score += points
                matches.append({"title": title, "video_id": v["id"], "views": int(v.get("statistics", {}).get("viewCount", 0)), "relevance_points": points})
        matches.sort(key=lambda x: (x["relevance_points"], x["views"]), reverse=True)
        rows.append({"handle": handle, "status": "OK", "channel_id": ch["id"],
                     "title": ch["snippet"]["title"], "score": score,
                     "sample_size": len(videos), "matched_video_count": len(matches),
                     "matching_videos": matches[:5],
                     "channel_url": "https://www.youtube.com/channel/" + ch["id"]})
    except Exception as e:
        rows.append({"handle": handle, "status": "ERROR", "error": str(e)[:180]})

ranked = sorted([x for x in rows if x["status"] == "OK"],
                key=lambda x: (x["score"], x["matched_video_count"]), reverse=True)
out = Path("growth-agents/output")
out.mkdir(parents=True, exist_ok=True)
now = dt.datetime.now(dt.timezone.utc).isoformat()
payload = {"generated_at_utc": now, "method": "Keyword-weighted relevance across 30 latest uploads per channel",
           "caveats": "Heuristic only; not audience overlap, actual click probability, lifetime ranking, or Google Ads eligibility.",
           "ranked_channels": ranked, "unresolved": [x for x in rows if x["status"] != "OK"]}
(out / "shani-audience-shortlist.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
lines = ["# Shani Dev audience research shortlist", "", f"Generated: {now}",
         "Ranked by keyword relevance in up to 30 recent public videos per channel.",
         "**Scores are not predicted click-through rates or verified Google Ads placements.**", "",
         "## Top five candidates", ""]
for idx, row in enumerate(ranked[:5], 1):
    lines.extend([f"### {idx}. {row['title']} (@{row['handle']})",
                  f"Relevance score: {row['score']} | Matched videos: {row['matched_video_count']}/{row['sample_size']}",
                  f"Channel: {row['channel_url']}", ""])
    for video in row["matching_videos"][:3]:
        lines.append(f"- {video['views']:,} views | {video['title']} | https://youtu.be/{video['video_id']}")
    lines.append("")
lines.extend(["## Full channel ranking", ""])
for i, row in enumerate(ranked, 1):
    lines.append(f"{i}. @{row['handle']} — score {row['score']} — {row['matched_video_count']} matching uploads")
for row in payload["unresolved"]:
    lines.append(f"- @{row['handle']}: {row['status']} (manual review required)")
lines.extend(["", "## Next steps", "",
              "Review the top channels' matching videos manually, then check Google Ads placement availability.",
              "Start with a small approved budget and monitor actual engaged views, watch time, and subscribers.",
              "No advertising campaign has been created or launched by this agent."])
(out / "shani-audience-shortlist.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Audience shortlist generated: {len(ranked)} channels ranked; top handles: {', '.join('@'+r['handle'] for r in ranked[:5])}")
