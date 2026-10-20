#!/usr/bin/env python3
"""Discover Anks Dharam public uploads and produce ready-to-use promotional packs.
Read-only YouTube API; never publishes comments or social posts.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path("growth-agents")
STATE = ROOT / "upload-monitor-state.json"
OUT = ROOT / "output" / "weekly-upload-promotion.md"
QUEUE = ROOT / "output" / "instagram-new-uploads.json"
CHANNEL = "UCIFarx_Xs-20fTL26nseYmQ"

def youtube(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = "https://www.googleapis.com/youtube/v3/" + endpoint + "?" + urlencode(params)
    with urlopen(url, timeout=25) as resp:
        return json.load(resp)

def pack(item):
    snippet = item["snippet"]
    title = snippet["title"].strip()
    video = snippet["resourceId"]["videoId"]
    link = "https://www.youtube.com/watch?v=" + video
    desc = snippet.get("description", "").strip().replace("\\r", "")
    excerpt = " ".join(desc.split())[:220]
    return f"""## {title}
Published: {snippet.get('publishedAt', 'unknown')} | Video: {link}

**Facebook draft**
New on Anks Dharam AI Films: {title}
Explore the story through our AI-assisted mythological film.
Watch: {link}
#AnksDharam #HinduMythology #AIAnimation

**Pinterest pin draft** (requires a poster image and board selection)
Title: {title[:95]}
Description: Explore {title}. An AI-assisted mythological film from Anks Dharam. {link}
Destination: {link}

**Instagram caption draft** (requires a visual asset)
{title}
A new cinematic mythology story from Anks Dharam AI Films. Watch on YouTube: @anksdharam
#AnksDharam #HinduMythology #AIAnimation

**Short-form teaser suggestion**
Use an original 10–20 second dramatic moment from the film with a clear ending invitation to watch the full story. No clip is automatically generated or uploaded.

**Description excerpt for review**
{excerpt or 'No public description available.'}
"""

def main():
    if not os.getenv("YOUTUBE_API_KEY"):
        raise SystemExit("Missing YOUTUBE_API_KEY secret")
    channel = youtube("channels", part="contentDetails", id=CHANNEL)
    items = channel.get("items", [])
    if len(items) != 1:
        raise SystemExit("Unable to identify channel")
    playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    payload = youtube("playlistItems", part="snippet", playlistId=playlist, maxResults=15)
    videos = [x for x in payload.get("items", []) if x.get("snippet", {}).get("resourceId", {}).get("videoId")]
    previous = json.loads(STATE.read_text()) if STATE.exists() else {"seen":[]}
    seen = set(previous.get("seen", []))
    fresh = [v for v in reversed(videos) if v["snippet"]["resourceId"]["videoId"] not in seen]
    # First run establishes a baseline; does not flood the promotion queue.
    if not STATE.exists():
        fresh = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if fresh:
        content = "# New Anks Dharam uploads — promotional drafts\n\n" + "\n\n".join(pack(v) for v in fresh)
    else:
        content = "# Anks Dharam upload monitor\n\nNo new public uploads since the previous scan.\n"
    OUT.write_text(content, encoding="utf-8")
    QUEUE.write_text(json.dumps([{"video_id": v["snippet"]["resourceId"]["videoId"], "title": v["snippet"]["title"].strip()} for v in fresh], indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    latest = [v["snippet"]["resourceId"]["videoId"] for v in videos]
    STATE.write_text(json.dumps({"seen":list(dict.fromkeys(latest + previous.get("seen", [])))[:250], "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2)+"\n")
    print(f"Scanned {len(videos)} recent uploads; found {len(fresh)} new uploads; promotional draft: {OUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
