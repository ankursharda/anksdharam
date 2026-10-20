#!/usr/bin/env python3
"""Whole-library discovery and opportunity ranking for Anks Dharam.
Uses public YouTube Data API only. No artificial views or public posting.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path("growth-agents")
CATALOG = ROOT / "channel-catalog.json"
REPORT = ROOT / "output" / "channel-growth-report.md"
QUEUE = ROOT / "output" / "channel-growth-opportunities.json"
CHANNEL = "UCIFarx_Xs-20fTL26nseYmQ"

def get(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = "https://www.googleapis.com/youtube/v3/" + endpoint + "?" + urlencode(params)
    with urlopen(url, timeout=40) as resp:
        return json.load(resp)

def category(title):
    s = title.lower()
    if any(x in s for x in ("mantra", "stotram", "chant", "jaap", "aarti", "bhajan", "kavach", "स्तुति", "मंत्र", "आरती")):
        return "Devotional music & prayers"
    if any(x in s for x in ("avatar", "dashavatar", "narasimha", "narsimha", "parashuram", "vamana", "matsya", "kurma", "kalki")):
        return "Dashavatar & Vishnu mythology"
    if any(x in s for x in ("shiv", "shiva", "mahadev", "neelkanth", "ganesh", "ganesha")):
        return "Shiva & Ganesha mythology"
    if any(x in s for x in ("shani", "shanidev", "surya", "karma")):
        return "Shani Dev & planetary mythology"
    return "Other Vedic stories"

def main():
    channel = get("channels", part="contentDetails", id=CHANNEL)
    items = channel.get("items", [])
    if not items:
        raise SystemExit("Channel not found")
    playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    records = []
    page = None
    while True:
        payload = get("playlistItems", part="snippet", playlistId=playlist, maxResults=50, **({"pageToken": page} if page else {}))
        for item in payload.get("items", []):
            sn = item.get("snippet", {})
            vid = sn.get("resourceId", {}).get("videoId")
            if vid:
                records.append({"video_id": vid, "title": sn.get("title", ""), "published_at": sn.get("publishedAt", "")})
        page = payload.get("nextPageToken")
        if not page:
            break
    now = dt.datetime.now(dt.timezone.utc)
    for offset in range(0, len(records), 50):
        batch = records[offset:offset + 50]
        data = get("videos", part="statistics,contentDetails,status,snippet", id=",".join(x["video_id"] for x in batch))
        indexed = {v["id"]: v for v in data.get("items", [])}
        for rec in batch:
            v = indexed.get(rec["video_id"], {})
            stats = v.get("statistics", {})
            rec["views"] = int(stats.get("viewCount", 0))
            rec["likes"] = int(stats.get("likeCount", 0))
            rec["comments"] = int(stats.get("commentCount", 0))
            rec["category"] = category(rec["title"])
            rec["privacy"] = v.get("status", {}).get("privacyStatus", "unknown")
            rec["duration"] = v.get("contentDetails", {}).get("duration", "")
            try:
                days = max(1, (now - dt.datetime.fromisoformat(rec["published_at"].replace("Z", "+00:00"))).days)
            except (ValueError, TypeError):
                days = 1
            rec["age_days"] = days
            rec["views_per_day"] = round(rec["views"] / days, 2)
            # Heuristic for review, not a prediction of future growth.
            rec["opportunity_score"] = round((rec["views"] + 1) ** 0.35 / (days + 14) ** 0.2 + (rec["likes"] + rec["comments"]) / max(rec["views"], 1) * 4, 3)
    public = [r for r in records if r["privacy"] == "public"]
    ranked = sorted(public, key=lambda r: r["opportunity_score"], reverse=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps({"channel_id": CHANNEL, "checked_at": now.isoformat(), "videos": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUEUE.write_text(json.dumps(ranked[:30], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Anks Dharam — Whole-channel growth intelligence", "",
             f"Catalogued **{len(records)}** uploads; **{len(public)}** currently public.",
             "Opportunity ranking uses public views, age and engagement. It cannot measure CTR, impressions or retention without YouTube Analytics OAuth.",
             "", "## Top 30 opportunities", "",
             "| Rank | Film | Category | Views | Views/day | Score |", "|---:|---|---|---:|---:|---:|"]
    for i, rec in enumerate(ranked[:30], 1):
        title = rec["title"].replace("|", "–").replace("\n", " ")
        lines.append(f'| {i} | [{title}](https://youtu.be/{rec["video_id"]}) | {rec["category"]} | {rec["views"]:,} | {rec["views_per_day"]:.2f} | {rec["opportunity_score"]:.2f} |')
    lines.extend(["", "## Distribution policy", "",
                  "This report is an opportunity shortlist, not an instruction to spam. Do not republish the same creative repeatedly. Public posting must use verified platform permissions and a persistent cross-platform ledger.",
                  ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Catalogued {len(records)} uploads; {len(public)} public; ranked {len(ranked)} opportunities.")
if __name__ == "__main__":
    main()
