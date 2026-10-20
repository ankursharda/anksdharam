#!/usr/bin/env python3
"""Prepare or publish an Instagram image post for an Anks Dharam YouTube film.

Default is preview-only. Publishing requires --publish and a valid Instagram
Business Login token with instagram_business_content_publish permission.
"""
import argparse
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GRAPH = "https://graph.instagram.com/v24.0"

def api(method, path, token, params):
    body = dict(params)
    body["access_token"] = token
    url = GRAPH + path
    if method == "GET":
        url += "?" + urlencode(body)
        payload = None
    else:
        payload = urlencode(body).encode()
    try:
        with urlopen(Request(url, data=payload, method=method), timeout=35) as response:
            return json.load(response)
    except HTTPError as exc:
        # Do not print the request URL, response body, or token.
        raise RuntimeError(f"Instagram API returned HTTP {exc.code} at {path}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Instagram API request failed at {path}: {type(exc).__name__}") from None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video-id", required=True, help="11-character YouTube video ID")
    p.add_argument("--title", required=True)
    p.add_argument("--publish", action="store_true", help="Publish publicly; default is preview only")
    args = p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", args.video_id):
        p.error("Invalid YouTube video ID")
    title = " ".join(args.title.split())[:180]
    if not title:
        p.error("Title must not be empty")
    image_url = f"https://i.ytimg.com/vi/{args.video_id}/hqdefault.jpg"
    video_url = f"https://www.youtube.com/watch?v={args.video_id}"
    caption = (f"{title}\n\nA new AI-assisted mythological film from Anks Dharam. "
               f"Watch the full film on YouTube: @anksdharam (link in bio).\n\n"
               f"#AnksDharam #HinduMythology #AIAnimation")
    print("YouTube film:", video_url)
    print("Thumbnail:", image_url)
    print("Instagram caption:\n" + caption)
    if not args.publish:
        print("PREVIEW ONLY. Nothing was published.")
        return 0
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        print("Missing INSTAGRAM_ACCESS_TOKEN secret.")
        return 1
    me = api("GET", "/me", token, {"fields": "user_id,username"})
    if me.get("username", "").lower().lstrip("@") != "anks_lifeon":
        print("Token is not for @anks_lifeon. Refusing to publish.")
        return 1
    user_id = me.get("user_id") or me.get("id")
    if not user_id:
        print("Instagram API did not return a user ID.")
        return 1
    container = api("POST", f"/{user_id}/media", token, {
        "image_url": image_url, "caption": caption
    })
    container_id = container.get("id")
    if not container_id:
        print("Instagram did not return a media container ID.")
        return 1
    for attempt in range(12):
        status = api("GET", f"/{container_id}", token, {"fields": "status_code"})
        state = status.get("status_code")
        if state == "FINISHED":
            break
        if state in ("ERROR", "EXPIRED"):
            print("Instagram rejected the media container:", state)
            return 1
        time.sleep(5)
    else:
        print("Media container not ready; nothing published.")
        return 1
    published = api("POST", f"/{user_id}/media_publish", token, {
        "creation_id": container_id
    })
    print("Published Instagram media ID:", published.get("id", "(not returned)"))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print("ERROR:", exc)
        sys.exit(1)
