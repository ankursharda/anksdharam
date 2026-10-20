#!/usr/bin/env python3
"""Human-approved YouTube comment publisher. No automated discovery or posting."""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

CHANNEL_ID = "UCIFarx_Xs-20fTL26nseYmQ"
EXCLUDED = {"@anksvodcast", "@anksdharam", "@jinnicasharda9991", "@harshsharda9336"}
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_URL = "https://www.googleapis.com/youtube/v3"

def post_json(url, data, bearer=None):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def access_token():
    for name in ("YOUTUBE_OAUTH_CLIENT_ID", "YOUTUBE_OAUTH_CLIENT_SECRET", "YOUTUBE_OAUTH_REFRESH_TOKEN"):
        if not os.environ.get(name):
            raise SystemExit("Missing GitHub secret: " + name)
    payload = urlencode({
        "client_id": os.environ["YOUTUBE_OAUTH_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_OAUTH_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_OAUTH_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = Request(TOKEN_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=30) as response:
        return json.load(response)["access_token"]

def get_json(path, token):
    req = Request(API_URL + path, headers={"Authorization": "Bearer " + token})
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="growth-agents/engagement-queue.json")
    parser.add_argument("--publish", action="store_true", help="Publish only individually approved entries")
    parser.add_argument("--check-auth", action="store_true", help="Verify OAuth and channel without posting")
    args = parser.parse_args()
    if args.check_auth:
        token = access_token()
        identity = get_json("/channels?part=id&mine=true", token)
        ids = [c["id"] for c in identity.get("items", [])]
        if CHANNEL_ID not in ids:
            raise SystemExit("OAuth channel mismatch. Expected Anks Dharam AI Films; no comments posted.")
        print("SUCCESS: GitHub OAuth credentials verified for Anks Dharam AI Films. No comments posted.")
        return
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    entries = queue.get("comments", [])
    approved = [e for e in entries if e.get("approved") is True]
    for e in approved:
        assert e.get("video_id") and e.get("text"), "Missing video_id or text"
        assert e.get("type") in ("reply", "top_level"), "Invalid type"
        assert e.get("type") != "reply" or e.get("parent_comment_id"), "Reply needs parent_comment_id"
        assert e.get("target_author", "").strip().lower() not in EXCLUDED, "Excluded account"
        assert not re.search(r"https?://|www\\.|youtu\\.be|youtube\\.com", e["text"], re.I), "URLs prohibited"
        assert len(e["text"]) <= 1000, "Comment too long"
        assert e.get("approval_reference"), "Approval reference required"
    print(f"Queue: {len(entries)} entries; {len(approved)} individually approved.")
    if not args.publish:
        print("DRY RUN ONLY. No comments posted.")
        return
    if not approved:
        print("Nothing approved; no comments posted.")
        return
    token = access_token()
    identity = get_json("/channels?part=id&mine=true", token)
    ids = [c["id"] for c in identity.get("items", [])]
    if CHANNEL_ID not in ids:
        raise SystemExit("OAuth token does not belong to Anks Dharam. Refusing to publish.")
    for e in approved:
        if e["type"] != "reply":
            raise SystemExit("Automatic publishing supports approved replies only.")
    for e in approved:
        # A human must explicitly approve each final text and target in the queue.
        if e["type"] == "reply":
            # Re-check existing replies before each post to avoid duplicates on workflow retries.
            page = ""
            duplicate = False
            for _ in range(20):
                query = "/comments?part=snippet&maxResults=100&parentId=" + quote(e["parent_comment_id"], safe="")
                if page:
                    query += "&pageToken=" + quote(page, safe="")
                existing = get_json(query, token)
                for item in existing.get("items", []):
                    sn = item.get("snippet", {})
                    if sn.get("authorChannelId", {}).get("value") == CHANNEL_ID and sn.get("textOriginal") == e["text"]:
                        duplicate = True
                        break
                if duplicate or not existing.get("nextPageToken"):
                    break
                page = existing["nextPageToken"]
            else:
                raise SystemExit("Too many replies to verify duplicates; refusing to publish.")
            if duplicate:
                print(json.dumps({"approval_reference": e["approval_reference"], "status": "already_posted"}))
                continue
            payload = {"snippet": {"parentId": e["parent_comment_id"], "textOriginal": e["text"]}}
            path = "/comments?part=snippet"
        else:
            payload = {"snippet": {"videoId": e["video_id"], "topLevelComment": {"snippet": {"textOriginal": e["text"]}}}}
            path = "/commentThreads?part=snippet"
        try:
            result = post_json(API_URL + path, payload, token)
            print(json.dumps({"approval_reference": e["approval_reference"], "comment_id": result.get("id"), "status": "posted"}))
        except HTTPError as exc:
            raise SystemExit(f"Publishing stopped after API error {exc.code}; inspect YouTube before retrying to avoid duplicates.")
if __name__ == "__main__":
    main()
