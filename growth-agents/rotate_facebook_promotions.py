#!/usr/bin/env python3
"""Publish one unpromoted YouTube film link daily to an authorized Facebook Page.

Required GitHub Actions secrets: FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN.
Never print tokens. Never publish to a personal profile. Never mark failed posts done.
"""
import json
from datetime import datetime, timezone
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
        # Facebook's JSON error describes missing permissions or Page restrictions.
        # Do not include the request URL or access token in logs.
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            err = payload.get("error", {})
            detail = f"code={err.get('code', 'unknown')} subcode={err.get('error_subcode', 'none')} message={err.get('message', 'unknown')}"
        except (ValueError, UnicodeError):
            detail = "Response body was not valid JSON"
        raise RuntimeError(f"Facebook Graph API HTTP {exc.code} at {path}: {detail}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Facebook API error at {path}: {type(exc).__name__}") from None

def main():
    pages = [
        ("Ankur’s Life On", os.environ.get("FACEBOOK_ANKURS_PAGE_ID", "").strip(), os.environ.get("FACEBOOK_ANKURS_PAGE_TOKEN", "").strip()),
        ("Geeta Press Gorakhpur", os.environ.get("FACEBOOK_GEETA_PAGE_ID", "").strip(), os.environ.get("FACEBOOK_GEETA_PAGE_TOKEN", "").strip()),
    ]
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    posted = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    videos = sorted(catalog["videos"], key=lambda v: v.get("opportunity_score", 0), reverse=True)
    failures = []
    for label, page_id, token in pages:
        if label == "Geeta Press Gorakhpur":
            print("Geeta Press handled by dedicated 06:00 IST workflow; skipping here.")
            continue
        is_shared_page = label == "Geeta Press Gorakhpur"
        # Limit shared-admin Page promotions to Wednesdays (UTC/IST same weekday at 09:45 IST).
        if is_shared_page and datetime.now(timezone.utc).weekday() != 2:
            print(f"{label}: weekly Wednesday schedule; skipping today.")
            continue
        if not page_id or not token:
            print(f"{label}: credentials not configured; skipping.")
            continue
        if not re.fullmatch(r"[0-9]+", page_id):
            failures.append(f"{label}: invalid Page ID")
            continue
        try:
            page = api("GET", f"/{page_id}", token, {"fields": "id,name"})
            if str(page.get("id")) != page_id:
                raise RuntimeError("Page identity verification failed")
            print("Verified Facebook Page:", page.get("name", label))
            page_posts = posted.get(page_id, {})
            for video in videos:
                vid = video["video_id"]
                if video.get("privacy") != "public" or vid in page_posts:
                    continue
                title = " ".join(video["title"].split())[:240]
                link = f"https://www.youtube.com/watch?v={vid}"
                message = f"{title}\n\nWatch on Anks Dharam: {link}\n\n#AnksDharam #HinduMythology"
                if is_shared_page:
                    # Upload a visible YouTube thumbnail as the Page photo, with the video link in its caption.
                    thumbnail = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                    result = api("POST", f"/{page_id}/photos", token, {"url": thumbnail, "caption": message, "published": "true"})
                else:
                    result = api("POST", f"/{page_id}/feed", token, {"message": message, "link": link, "published": "true"})
                post_id = result.get("post_id") or result.get("id")
                if not post_id:
                    raise RuntimeError("No confirmed Facebook post ID")
                page_posts[vid] = {"title": title, "facebook_post_id": post_id}
                posted[page_id] = page_posts
                LEDGER.write_text(json.dumps(posted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"{label}: published {vid} as {post_id}")
                break
            else:
                print(f"{label}: all public videos already promoted.")
        except RuntimeError as exc:
            detail = str(exc)
            if "code=190" in detail and "subcode=463" in detail:
                print(f"::error title=Facebook credential expired::{label} Page token has expired. Renew the Page access token and replace its GitHub Actions secret. No Facebook post was published.")
                failures.append(f"{label}: expired Facebook Page token; replace its GitHub Actions secret")
            else:
                failures.append(f"{label}: {exc}")
    if failures:
        raise SystemExit("; ".join(failures))

if __name__ == "__main__":
    main()
