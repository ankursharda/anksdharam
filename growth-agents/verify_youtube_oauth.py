#!/usr/bin/env python3
"""Read-only YouTube OAuth identity verification. Never publishes comments."""
import json,os
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
needed=["YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN"]
missing=[k for k in needed if not os.environ.get(k)]
if missing:
    raise SystemExit("Missing GitHub Actions secrets: "+", ".join(missing))
data=urlencode({"client_id":os.environ["YOUTUBE_CLIENT_ID"],"client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],"refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
try:
    with urlopen(Request("https://oauth2.googleapis.com/token",data=data,headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=30) as response:
        token=json.load(response)["access_token"]
except HTTPError as e:
    raise SystemExit(f"Google OAuth refresh failed: HTTP {e.code} (no secrets printed)") from None
req=Request("https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true",headers={"Authorization":"Bearer "+token})
try:
    with urlopen(req,timeout=30) as response:
        channels=json.load(response).get("items",[])
except HTTPError as e:
    raise SystemExit(f"YouTube channel lookup failed: HTTP {e.code}") from None
if len(channels)!=1:
    raise SystemExit(f"Expected one authorized YouTube channel; found {len(channels)}")
channel=channels[0]
print("Authorized YouTube channel:",channel["snippet"].get("title","Unknown"))
print("Authorized channel ID:",channel["id"])
if channel["id"]!="UCIFarx_Xs-20fTL26nseYmQ":
    raise SystemExit("Channel does not match Anks Dharam. Commenting remains disabled.")
print("PASS: OAuth refresh and Anks Dharam identity verified. NO COMMENTS POSTED.")
