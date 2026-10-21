#!/usr/bin/env python3
"""Publish ONE manually approved, topical YouTube comment as the OAuth-authorized channel.
No auto-replies, no mass commenting, no links, no subscription requests.
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3/"
def request(url, payload, bearer=None):
    headers = {"Content-Type":"application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(req,timeout=30) as res:
            return json.load(res)
    except HTTPError as e:
        try:
            detail=json.load(e).get("error",{})
            if isinstance(detail,dict):
                detail=detail.get("message","Request rejected")
        except Exception:
            detail="Request rejected"
        raise SystemExit(f"YouTube API HTTP {e.code}: {str(detail)[:300]}") from None

def token():
    creds = {k:os.environ.get(k,"").strip() for k in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN")}
    if not all(creds.values()):
        raise SystemExit("Missing YouTube OAuth GitHub Actions secrets. No comment posted.")
    form=urlencode({"client_id":creds["YOUTUBE_CLIENT_ID"],
                    "client_secret":creds["YOUTUBE_CLIENT_SECRET"],
                    "refresh_token":creds["YOUTUBE_REFRESH_TOKEN"],
                    "grant_type":"refresh_token"}).encode()
    req=Request(TOKEN_URL,data=form,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    try:
        with urlopen(req,timeout=30) as response:
            return json.load(response)["access_token"]
    except HTTPError as e:
        raise SystemExit(f"OAuth refresh failed: HTTP {e.code}; no comment posted.") from None

def get_channel(access_token):
    req=Request(API+"channels?part=id&mine=true",headers={"Authorization":"Bearer "+access_token})
    with urlopen(req,timeout=30) as response:
        data=json.load(response)
    items=data.get("items",[])
    return items[0]["id"] if len(items)==1 else ""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video-id",required=True)
    p.add_argument("--parent-id",default="")
    p.add_argument("--text",required=True)
    args=p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",args.video_id):
        p.error("Invalid YouTube video ID")
    message=args.text.strip()
    if not 10<=len(message)<=1000:
        p.error("Comment must be 10–1000 characters")
    if re.search(r"https?://|www\\.|@anksdharam|subscribe|sub4sub|चैनल सब्सक्राइब",message,re.I):
        p.error("No links, channel mentions, or subscription requests")
    if args.parent_id and not re.fullmatch(r"[A-Za-z0-9_-]{8,200}",args.parent_id):
        p.error("Invalid parent comment ID")
    access=token()
    channel=get_channel(access)
    if channel!="UCIFarx_Xs-20fTL26nseYmQ":
        raise SystemExit("OAuth account is not Anks Dharam. No comment posted.")
    if args.parent_id:
        endpoint="comments?part=snippet"
        payload={"snippet":{"parentId":args.parent_id,"textOriginal":message}}
    else:
        endpoint="commentThreads?part=snippet"
        payload={"snippet":{"videoId":args.video_id,"topLevelComment":{"snippet":{"textOriginal":message}}}}
    result=request(API+endpoint,payload,access)
    print("Approved comment published successfully. Comment ID:",result.get("id","unknown"))
    print("Video: https://www.youtube.com/watch?v="+args.video_id)

if __name__=="__main__":
    main()
