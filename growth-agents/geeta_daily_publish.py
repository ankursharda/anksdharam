#!/usr/bin/env python3
"""Daily 06:00 IST Geeta Press Gorakhpur devotional YouTube link post."""
import json, os, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path("growth-agents")
PAGE_ID = os.environ["FACEBOOK_GEETA_PAGE_ID"].strip()
TOKEN = os.environ["FACEBOOK_GEETA_PAGE_TOKEN"].strip()
PLAYLISTS = ("PLdp9v6qShEfS93Chcvyq9YAfR9qpLFYGs", "PLdp9v6qShEfRlIBnxkKVTtvn9jkUoOIQV")
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
    try:
        with urlopen(Request(url, data=body, method=method), timeout=35) as response:
            return json.load(response)
    except HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            err = json.loads(raw).get('error', {})
            print('Facebook API error: HTTP', exc.code, 'code', err.get('code'), 'subcode', err.get('error_subcode'), 'type', err.get('type'))
            print('Facebook message:', err.get('message', 'Unavailable').replace(TOKEN, '[REDACTED]'))
        except (ValueError, AttributeError):
            print('Facebook API error: HTTP', exc.code, '(unparseable response)')
        raise SystemExit('Facebook API request failed; publication not confirmed') from None
print("Checking Geeta Press Page identity and API access", flush=True)
page = api("GET", "/" + PAGE_ID, {"fields":"id,name"})
if str(page.get("id")) != PAGE_ID or "Geeta Press" not in page.get("name", ""):
    raise SystemExit("Geeta Press Page identity mismatch")
ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"posts":[]}
posts = ledger.get("posts", [])
if any(p.get("date") == today for p in posts):
    print("Already published for " + today)
    raise SystemExit(0)
videos = []
for playlist_id in PLAYLISTS:
    url = "https://www.youtube.com/playlist?list=" + playlist_id
    command = ["yt-dlp", "--flat-playlist", "--dump-single-json", "--no-warnings", "--ignore-errors", url]
    try:
        output = subprocess.run(command, capture_output=True, text=True, timeout=150)
        if output.returncode != 0:
            print("Playlist retrieval failed:", playlist_id, output.stderr[-600:], flush=True)
            continue
        data = json.loads(output.stdout)
        for item in data.get("entries", []):
            if not item:
                continue
            vid_id = item.get("id")
            title = item.get("title") or ""
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid_id or "") and title and item.get("live_status") not in ("is_upcoming", "is_live") and item.get("availability") not in ("private", "premium_only", "subscriber_only"):
                videos.append({"video_id": vid_id, "title": title, "privacy": "public"})
        print("Loaded playlist:", playlist_id, "entries:", len(data.get("entries", [])), flush=True)
    except (subprocess.TimeoutExpired, ValueError, OSError) as exc:
        print("Playlist retrieval error:", playlist_id, type(exc).__name__, flush=True)
eligible = list({v["video_id"]: v for v in videos if v.get("privacy") == "public" and v.get("video_id")}.values())
if not eligible:
    raise SystemExit("No eligible videos retrieved from configured playlists; no Facebook post attempted")
recent = {p["video_id"] for p in posts if (datetime.fromisoformat(today).date() - datetime.fromisoformat(p["date"]).date()).days < 30}
previous = {p["video_id"] for p in posts}
choices = [v for v in eligible if v["video_id"] not in recent]
if not choices:
    raise SystemExit("No video outside 30-day rotation; no duplicate post made")
choices.sort(key=lambda v: (v["video_id"] in previous, -float(v.get("opportunity_score") or 0)))
video = choices[0]
# Diwali 2026: feature the released Maha Lakshmi Mantra on 7 November,
# safely after its announced 6 November release date.
if today == "2026-11-07" and not any(p.get("video_id") == "ON2hITR2vzA" for p in posts):
    video = {"video_id": "ON2hITR2vzA", "title": "Maha Lakshmi Mantra | Diwali Special"}
vid = video["video_id"]
title = " ".join(video.get("title", "").split())
t = title.lower()
if "ON2hITR2vzA" == vid:
    caption = "🪷 जय माँ महालक्ष्मी! दीपावली के पावन अवसर पर माँ लक्ष्मी के दिव्य मंत्र का श्रवण करें। माता रानी की कृपा से सभी के जीवन में सुख, शांति और समृद्धि बनी रहे। 🪔🙏"
elif any(s in t for s in ("shani", "शन")):
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
print("Attempting Facebook publication for video:", vid, flush=True)
result = api("POST", "/" + PAGE_ID + "/feed", {"message":message, "link":link, "published":"true"})
post_id = result.get("id")
if not post_id:
    raise SystemExit("Facebook did not confirm a post ID")
posts.append({"date":today, "video_id":vid, "facebook_post_id":post_id})
ledger["posts"] = posts
LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Geeta Press published:", vid, "post ID:", post_id, flush=True)
