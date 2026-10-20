#!/usr/bin/env python3
"""Read-only public comment intelligence for own channel and relevant external channels."""
import ast
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    raise SystemExit("Missing YOUTUBE_API_KEY")
ROOT = Path("growth-agents/output")
ROOT.mkdir(parents=True, exist_ok=True)
OWN_HANDLE = "anksdharam"
KEYWORDS = ("shani", "shanidev", "surya", "narasimha", "narsimha", "shiv", "neelkanth",
            "vishnu", "parashuram", "kalki", "dashavatar", "mytholog", "vedic",
            "शनि", "नरसिंह", "शिव", "विष्णु", "परशुराम", "कल्कि", "अवतार", "कथा")

def api(endpoint, **params):
    params["key"] = KEY
    url = "https://www.googleapis.com/youtube/v3/" + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)

def competitor_handles():
    tree = ast.parse(Path("growth-agents/competitor_intelligence.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "HANDLES" for t in node.targets):
            return list(dict.fromkeys(ast.literal_eval(node.value)))
    raise RuntimeError("Competitor HANDLES list not found")

def fetch_channel(handle, own=False):
    result = api("channels", part="snippet,contentDetails", forHandle=handle).get("items", [])
    if not result:
        return {"handle": handle, "status": "NOT_FOUND", "source": "own" if own else "external", "comments": []}
    ch = result[0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    playlist = api("playlistItems", part="snippet", playlistId=uploads, maxResults=12 if own else 3)
    videos = playlist.get("items", [])
    comments = []
    for item in videos:
        video_id = item.get("snippet", {}).get("resourceId", {}).get("videoId")
        title = item.get("snippet", {}).get("title", "")
        if not video_id:
            continue
        # For external channels, focus the limited API budget on mythology-related titles.
        if not own and not any(k in title.casefold() for k in KEYWORDS):
            continue
        try:
            threads = api("commentThreads", part="snippet", videoId=video_id, maxResults=20,
                          order="relevance", textFormat="plainText").get("items", [])
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                continue  # comments disabled or video unavailable
            raise
        for thread in threads:
            top = thread["snippet"]["topLevelComment"]
            snip = top["snippet"]
            body = snip.get("textDisplay", "")
            relevance = sum(1 for k in KEYWORDS if k in (body + " " + title).casefold())
            if not own and relevance == 0:
                continue
            comments.append({
                "video_id": video_id, "video_title": title, "video_url": "https://youtu.be/" + video_id,
                "comment_id": top["id"], "comment_url": "https://www.youtube.com/watch?v=" + video_id + "&lc=" + top["id"],
                "author_display_name": snip.get("authorDisplayName", ""),
                "author_channel_url": snip.get("authorChannelUrl", ""),
                "comment_excerpt": body[:350], "likes": snip.get("likeCount", 0),
                "reply_count": thread["snippet"].get("totalReplyCount", 0),
                "published_at": snip.get("publishedAt"), "relevance_matches": relevance
            })
    comments.sort(key=lambda c: (c["relevance_matches"], c["likes"], c["reply_count"]), reverse=True)
    return {"handle": handle, "source": "own" if own else "external",
            "status": "OK", "channel_title": ch["snippet"]["title"], "channel_id": ch["id"],
            "sampled_uploads": len(videos), "relevant_public_comments": comments[:30]}

rows = []
for handle, own in [(OWN_HANDLE, True)] + [(h, False) for h in competitor_handles() if h.casefold() != OWN_HANDLE]:
    try:
        result = fetch_channel(handle, own)
        rows.append(result)
        print("Comments:", handle, result["status"], len(result.get("relevant_public_comments", [])), flush=True)
    except Exception as e:
        print("ERROR:", handle, type(e).__name__, str(e)[:180], flush=True)
        rows.append({"handle": handle, "source": "own" if own else "external",
                     "status": "ERROR", "error": str(e)[:180]})
if not any(r["status"] == "OK" for r in rows):
    raise SystemExit("No channels resolved; check YouTube API key/quota and logs")
now = dt.datetime.now(dt.timezone.utc).isoformat()
data = {"generated_at_utc": now, "method": "Public commentThreads from up to 12 own and 3 recent external uploads per channel; top 20 public comments per sampled video.",
        "limitations": "Public commenters are not a list of viewers or subscribers. Not an authorization to mass-message or post unsolicited links. Read-only; no replies sent.",
        "channels": rows}
(ROOT / "comment-intelligence.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = ["# Two-source YouTube comment intelligence", "", "Generated: " + now,
         "Read-only research; no comments posted. Public commenters are not verified viewers or subscribers.", ""]
for source in ("own", "external"):
    lines += ["## " + ("Anks Dharam — own audience" if source == "own" else "External channels — relevant public discussions"), ""]
    for row in (r for r in rows if r["source"] == source):
        comments = row.get("relevant_public_comments", [])
        lines += ["### @" + row["handle"] + " — " + row["status"] + " (" + str(len(comments)) + " comments)", ""]
        for c in comments[:5]:
            excerpt = re.sub(r"\\s+", " ", c["comment_excerpt"]).replace("\n", " ")[:170]
            lines.append("- " + excerpt + " | " + c["comment_url"])
        lines.append("")
(ROOT / "comment-intelligence.md").write_text("\n".join(lines), encoding="utf-8")
print("Comment intelligence generated:", sum(r["status"] == "OK" for r in rows),
      "channels resolved;", sum(len(r.get("relevant_public_comments", [])) for r in rows), "comments shortlisted")
