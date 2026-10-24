#!/usr/bin/env python3
"""Daily 06:00 IST Geeta Press Gorakhpur devotional YouTube link post."""
import json, os, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path("growth-agents")
PAGE_ID = os.environ["FACEBOOK_GEETA_PAGE_ID"].strip()
TOKEN = os.environ["FACEBOOK_GEETA_PAGE_TOKEN"].strip()
CATALOG = ROOT / "channel-catalog.json"
LEDGER = ROOT / "geeta-daily-published.json"
IST = timezone(timedelta(hours=5, minutes=30))
today = datetime.now(IST).date().isoformat()
if not re.fullmatch(r"[0-9]+", PAGE_ID):
    raise SystemExit("Invalid Geeta Press Page ID")
def api(method, path, values):
    values = dict(values)
    values["access_token"] = TOKEN
    url = "https://graph.facebook.com/v24.0" + path
    body = None if method == "GET" else urlencode(values).encode()
    if method == "GET":
        url += "?" + urlencode(values)
    with urlopen(Request(url, data=body, method=method), timeout=35) as response:
        return json.load(response)
page = api("GET", "/" + PAGE_ID, {"fields":"id,name"})
if str(page.get("id")) != PAGE_ID or "Geeta Press" not in page.get("name", ""):
    raise SystemExit("Geeta Press Page identity mismatch")
ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"posts":[]}
posts = ledger.get("posts", [])
if any(p.get("date") == today for p in posts):
    print("Already published for " + today)
    raise SystemExit(0)
videos = json.loads(CATALOG.read_text(encoding="utf-8")).get("videos", [])
eligible = [v for v in videos if v.get("privacy") == "public" and v.get("video_id")]
if not eligible:
    raise SystemExit("No public videos in catalog")
recent = {p["video_id"] for p in posts if (datetime.fromisoformat(today).date() - datetime.fromisoformat(p["date"]).date()).days < 30}
previous = {p["video_id"] for p in posts}
choices = [v for v in eligible if v["video_id"] not in recent]
if not choices:
    raise SystemExit("No video outside 30-day rotation; no duplicate post made")
choices.sort(key=lambda v: (v["video_id"] in previous, -float(v.get("opportunity_score") or 0)))
video = choices[0]
vid = video["video_id"]
title = " ".join(video.get("title", "").split())
t = title.lower()
if any(s in t for s in ("shani", "शन")):
    caption = "जय शनिदेव! प्रभु की कृपा से जीवन में न्याय, धैर्य और सद्बुद्धि बनी रहे। 🙏"
elif any(s in t for s in ("shiv", "mahadev", "शिव", "महादेव")):
    caption = "हर हर महादेव! भगवान शिव की कृपा सभी भक्तों पर बनी रहे। 🔱🙏"
elif any(s in t for s in ("krishna", "कृष्ण")):
    caption = "जय श्री कृष्ण! प्रभु का स्मरण जीवन में प्रेम और शांति का संचार करे। 🙏"
elif any(s in t for s in ("durga", "devi", "दुर्गा", "देवी")):
    caption = "जय माता दी! माँ भगवती सभी भक्तों को शक्ति और मंगल प्रदान करें। 🙏"
elif any(s in t for s in ("ram", "राम")):
    caption = "जय श्री राम! प्रभु श्रीराम के आदर्श हमें धर्म के मार्ग पर प्रेरित करें। 🙏"
else:
    caption = "सनातन धर्म की दिव्य कथाओं और भक्ति का स्मरण करें। ईश्वर सभी का कल्याण करें। 🙏"
link = "https://www.youtube.com/watch?v=" + vid
message = caption + "\n\n" + title + "\n" + link + "\n\n#AnksDharam #सनातनधर्म #भक्ति"
result = api("POST", "/" + PAGE_ID + "/feed", {"message":message, "link":link, "published":"true"})
post_id = result.get("id")
if not post_id:
    raise SystemExit("Facebook did not confirm a post ID")
posts.append({"date":today, "video_id":vid, "facebook_post_id":post_id})
ledger["posts"] = posts
LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Geeta Press published:", vid, "post ID:", post_id)
