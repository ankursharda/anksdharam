import json,os
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
vid="po_ZK0kqt9k"
url="https://www.googleapis.com/youtube/v3/commentThreads"
comments=[]
page=""
for _ in range(30):
    q={"part":"snippet,replies","videoId":vid,"maxResults":100,"order":"time","key":os.environ["YOUTUBE_API_KEY"]}
    if page:q["pageToken"]=page
    with urlopen(url+"?"+urlencode(q),timeout=30) as f: data=json.load(f)
    for t in data.get("items",[]):
        sn=t["snippet"]["topLevelComment"]["snippet"]
        comments.append({"comment_id":t["snippet"]["topLevelComment"]["id"],"text":sn.get("textOriginal",""),"author":sn.get("authorDisplayName",""),"reply_count":t["snippet"].get("totalReplyCount",0)})
    page=data.get("nextPageToken","")
    if not page:break
p=Path("growth-agents/output/own-video-comments.json")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({"video_id":vid,"comments":comments,"more":bool(page)},ensure_ascii=False,indent=2),encoding="utf-8")
print("Fetched",len(comments),"comments for one-time review; no replies posted")
