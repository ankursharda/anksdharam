#!/usr/bin/env python3
"""Discover relevant public YouTube discussions for human-reviewed Anks Dharam engagement.
Read-only: NEVER posts comments, replies, or performs engagement.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, HTTPError

API = "https://www.googleapis.com/youtube/v3/"
OUT = Path("growth-agents/output")
TOPICS = [
    "Shani Dev childhood story", "Shiv Neelkanth samudra manthan",
    "Narasimha Prahlad story", "Vishnu Dashavatar mythology",
    "Parashuram Ramayana story", "Hindu mythology animated film",
    "शनि देव कथा", "भगवान शिव की कथा", "नरसिंह अवतार",
]
def get(endpoint, **kwargs):
    kwargs["key"] = os.environ["YOUTUBE_API_KEY"]
    url = API + endpoint + "?" + urlencode(kwargs)
    with urlopen(url, timeout=30) as response:
        return json.load(response)

def main():
    if not os.environ.get("YOUTUBE_API_KEY"):
        raise SystemExit("YOUTUBE_API_KEY required for read-only discovery")
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = []
    seen = set()
    for topic in TOPICS:
        try:
            results = get("search", part="snippet", q=topic, type="video", order="date",
                          publishedAfter=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          maxResults=5)
            for item in results.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                sn = item["snippet"]
                if sn.get("channelId") == "UCIFarx_Xs-20fTL26nseYmQ":
                    continue
                entry = {"topic":topic,"video_id":vid,"video_url":"https://www.youtube.com/watch?v="+vid,
                         "video_title":sn.get("title",""),"channel":sn.get("channelTitle",""),
                         "published_at":sn.get("publishedAt",""),"discussion":[]}
                try:
                    comments = get("commentThreads", part="snippet", videoId=vid,
                                   order="relevance", maxResults=5, textFormat="plainText")
                    for thread in comments.get("items", []):
                        top = thread["snippet"]["topLevelComment"]
                        entry["discussion"].append({"comment_id":top["id"],
                            "author":top["snippet"].get("authorDisplayName",""),
                            "text":top["snippet"].get("textDisplay","")[:900],
                            "reply_count":thread["snippet"].get("totalReplyCount",0)})
                except HTTPError as exc:
                    if exc.code not in (400,403,404):
                        print(f"Comments unavailable for {vid}: HTTP {exc.code}")
                candidates.append(entry)
        except HTTPError as exc:
            print(f"Search unavailable for {topic}: HTTP {exc.code}")
    candidates.sort(key=lambda x:(bool(x["discussion"]),len(x["discussion"]),x["published_at"]),reverse=True)
    selected = candidates[:15]
    (OUT/"external-youtube-discussions.json").write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines = ["# Anks Dharam — External YouTube Engagement Review","",
             "Read-only discovery. No comments were posted. Review the actual video and discussion before drafting or approving a reply.",""]
    for idx,item in enumerate(selected,1):
        lines.extend([f"## {idx}. {item['video_title']}",f"Channel: {item['channel']}",
                      f"Topic: {item['topic']}",f"Video: {item['video_url']}",""])
        for c in item["discussion"][:3]:
            lines.extend([f"- {c['author']}: {c['text'].replace(chr(10),' ')[:350]}",
                          f"  Comment ID: \`{c['comment_id']}\`"])
        lines.extend(["","Suggested action: watch, verify context, and write one original, helpful comment or reply. No links or calls to subscribe.",""])
    (OUT/"external-youtube-review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Prepared {len(selected)} review candidates; no comments posted.")
if __name__ == "__main__":
    main()
