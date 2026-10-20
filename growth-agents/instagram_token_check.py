#!/usr/bin/env python3
"""Validate Instagram Login token without publishing anything or printing secrets."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def main():
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        print("ERROR: INSTAGRAM_ACCESS_TOKEN secret is missing.")
        return 1
    # Instagram API with Instagram Login: account identity endpoint.
    url = "https://graph.instagram.com/me?" + urlencode({
        "fields": "user_id,username,account_type",
        "access_token": token,
    })
    try:
        with urlopen(Request(url), timeout=20) as response:
            data = json.load(response)
    except HTTPError as exc:
        # Avoid echoing response body: it could contain sensitive metadata.
        print(f"Instagram token validation failed: HTTP {exc.code}. Check token and permissions.")
        return 1
    except (URLError, TimeoutError, ValueError) as exc:
        print(f"Instagram token validation failed: {type(exc).__name__}.")
        return 1
    username = data.get("username", "")
    if username.lower().lstrip("@") != "anks_lifeon":
        print("ERROR: token belongs to a different Instagram account.")
        return 1
    print("SUCCESS: Instagram token works for @anks_lifeon. No content was published.")
    print("Next requirements: hosted public image/video URL, publishing permission, and token renewal plan.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
