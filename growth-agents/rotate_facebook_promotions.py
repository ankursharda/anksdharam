#!/usr/bin/env python3
"""Publish one unpromoted YouTube film link daily to an authorized Facebook Page.

Required GitHub Actions secrets: FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN.
Never print tokens. Never publish to a personal profile. Never mark failed posts done.
"""
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path("growth-agents")
CATALOG = ROOT / "channel-catalog.json"
LEDGER = ROOT / "facebook-published.json"
GRAPH = "https://graph.facebook.com/v24.0"

def api(method, path, token, params):
    values = dict(params)
    values["access_token"] = token
    url = GRAPH + path
    data = None if method == "GET" else urlencode(values).encode("utf-8")
    if method == "GET":
        url += "?" + urlencode(values)
    try:
        with urlopen(Request(url, data=data, method=method), timeout=35) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Facebook Graph API HTTP {exc.code} at {path}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Facebook API error at {path}: {type(exc).__name__}") from None

def main():
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        print("Facebook Page ID or Page access token not configured; skipping without publishing.")
        return
    if not re.fullmatch(r"[0-9]+", page_id):
        raise SystemExit("FACEBOOK_PAGE_ID must be a numeric Page ID.")
    page = api("GET", f"/{page_id}", token, {"fields": "id,name"})
    if str(page.get("id")) != page_id:
        raise SystemExit("Token could not verify the configured Facebook Page.")
    print("Verified Facebook Page:", page.get("name", page_id))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    posted = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    videos = sorted(catalog["videos"], key=lambda v: v.get("opportunity_score", 0), reverse=True)
    for video in videos:
        vid = video["video_id"]
        if video.get("privacy") != "public" or vid in posted:
            continue
        title = " ".join(video["title"].split())[:240]
        link = f"https://www.youtube.com/watch?v={vid}"
        message = f"{title}\n\nWatch on Anks Dharam: {link}\n\n#AnksDharam #HinduMythology"
        result = api("POST", f"/{page_id}/feed", token, {"message": message, "link": link, "published": "true"})
        post_id = result.get("id")
        if not post_id:
            raise SystemExit("Facebook did not confirm a published Page post; ledger unchanged.")
        posted[vid] = {"title": title, "facebook_post_id": post_id, "origin": "whole-channel-rotation"}
        LEDGER.write_text(json.dumps(posted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Facebook published one video promotion: {vid}; post ID {post_id}")
        return
    print("All public videos already promoted on Facebook; nothing published.")

if __name__ == "__main__":
    main()
