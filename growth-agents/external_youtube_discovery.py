#!/usr/bin/env python3
"""Read-only discovery exclusively from user-selected Hindu mythology channels."""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, HTTPError

API = "https://www.googleapis.com/youtube/v3/"
OUT = Path("growth-agents/output")
# User's exclusive channel list; do not search or recommend outside these handles.
HANDLES = [
    "@devimaa3728", "@TrueRealms01", "@TheDivineTales", "@IndianMonk",
    "@epicaifilms2024", "@VedicKathaYT", "@sarvatrahindutva",
    "@Bhaktavatsal3", "@sanatanlegendsai", "@LostEchos27",
    "@PuranicCodex", "@dhalpritam1", "@HINDUSTORIES",
]
TOPICS = ("dashavatar", "dashavtar", "vishnu", "narasimha", "narsimha",
          "vaman", "vamana", "parashuram", "parshuram", "kalki",
          "shani", "shanidev", "shiv", "shiva", "mahadev",
          "mythology", "avatar", "dharma", "hindu", "bhakti",
          "दशावतार", "विष्णु", "नरसिंह", "वामन", "परशुराम", "कल्कि", "शनि", "शिव")

def get(endpoint, **kwargs):
    kwargs["key"] = os.environ["YOUTUBE_API_KEY"]
    with urlopen(API + endpoint + "?" + urlencode(kwargs), timeout=30) as response:
        return json.load(response)

def main():
    if not os.environ.get("YOUTUBE_API_KEY"):
        raise SystemExit("YOUTUBE_API_KEY required")
    OUT.mkdir(parents=True, exist_ok=True)
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=120)
    videos = {}
    for handle in HANDLES:
        try:
            ch = get("channels", part="id,contentDetails", forHandle=handle).get("items", [])
            if not ch:
                print("Unresolved allowed channel: " + handle)
                continue
            channel = ch[0]
            channel_id = channel["id"]
            playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
            page = get("playlistItems", part="snippet,contentDetails", playlistId=playlist, maxResults=35)
            for item in page.get("items", []):
                sn = item.get("snippet", {})
                vid = item.get("contentDetails", {}).get("videoId")
                if not vid or sn.get("channelId") != channel_id:
                    continue
                title = sn.get("title", "")
                if not any(word in title.lower() for word in TOPICS):
                    continue
                published = sn.get("publishedAt", "")
                try:
                    if dt.datetime.fromisoformat(published.replace("Z","+00:00")) < cutoff:
                        continue
                except ValueError:
                    continue
                videos[vid] = {"video_id":vid, "video_url":"https://www.youtube.com/watch?v="+vid,
                    "video_title":title, "channel":sn.get("channelTitle",""),
                    "channel_handle":handle, "channel_id":channel_id,
                    "published_at":published, "discussion":[]}
        except (HTTPError, KeyError) as exc:
            print("Channel unavailable " + handle + ": " + str(exc))
    ids = list(videos)
    for start in range(0,len(ids),50):
        try:
            stats = get("videos", part="snippet,statistics", id=",".join(ids[start:start+50]))
            for item in stats.get("items",[]):
                vid = item["id"]
                if vid not in videos or item["snippet"].get("channelId") != videos[vid]["channel_id"]:
                    continue
                s = item.get("statistics",{})
                videos[vid]["view_count"] = int(s.get("viewCount",0))
                videos[vid]["comment_count"] = int(s.get("commentCount",0))
        except HTTPError as exc:
            print("Video statistics unavailable: " + str(exc))
    # Do not select low-view videos or videos without confirmed statistics.
    eligible = [v for v in videos.values() if v.get("view_count",0)>=20000 and v.get("comment_count",0)>0]
    eligible.sort(key=lambda v:(v["view_count"]>=100000, v["view_count"],v["published_at"]),reverse=True)
    selected=[]
    for entry in eligible[:25]:
        try:
            comments=get("commentThreads",part="snippet",videoId=entry["video_id"],
                         order="time",maxResults=10,textFormat="plainText")
            for thread in comments.get("items",[]):
                top=thread["snippet"]["topLevelComment"]
                entry["discussion"].append({"comment_id":top["id"],
                    "author":top["snippet"].get("authorDisplayName",""),
                    "text":top["snippet"].get("textDisplay","")[:900],
                    "published_at":top["snippet"].get("publishedAt","")})
        except HTTPError as exc:
            print("Comments unavailable " + entry["video_id"] + ": " + str(exc))
        if entry["discussion"]:
            selected.append(entry)
        if len(selected)>=15:
            break
    (OUT/"external-youtube-discussions.json").write_text(
        json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Anks Dharam — Exclusive Channel Discussion Review","",
        "Read-only. Only user-selected channels, verified channel IDs and video statistics.",
        "Minimum 20,000 views; prefer 100,000+. No comments posted.",""]
    for i,v in enumerate(selected,1):
        lines.extend(["## "+str(i)+". "+v["video_title"],
            "Channel: "+v["channel"]+" ("+v["channel_handle"]+")",
            "Views: "+str(v["view_count"])+" | Comments: "+str(v["comment_count"]),
            "Video: "+v["video_url"],""])
        for c in v["discussion"][:3]:
            lines.append("- "+c["author"]+": "+c["text"].replace("\n"," ")[:350])
        lines.append("")
    (OUT/"external-youtube-review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Prepared "+str(len(selected))+" exclusive-channel candidates; no comments posted.")

if __name__=="__main__":
    main()
