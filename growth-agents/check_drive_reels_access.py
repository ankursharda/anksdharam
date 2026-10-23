#!/usr/bin/env python3
"""Read-only Google Drive folder connectivity check; never publishes content."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

FOLDERS = {
    "music": "1UsrcZLZQGyEclDwzd3yPQDSg9G6ihzCg",
    "thumbnails": "1fAWzh16reJb5ttg9wHfMwmPCWbVJkghY",
    "ready_shorts": "1yZqNWrvoymkXvgQuebiKig7s9bXISdmo",
}

def main():
    keys = ("GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET", "GOOGLE_DRIVE_REFRESH_TOKEN")
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError("Missing GitHub secrets: " + ", ".join(missing))
    payload = urlencode({
        "client_id": os.environ[keys[0]],
        "client_secret": os.environ[keys[1]],
        "refresh_token": os.environ[keys[2]],
        "grant_type": "refresh_token",
    }).encode()
    with urlopen(Request("https://oauth2.googleapis.com/token", data=payload, method="POST"), timeout=30) as resp:
        token = json.load(resp)["access_token"]
    for label, folder_id in FOLDERS.items():
        params = urlencode({
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": "nextPageToken,files(id,name,mimeType,size)",
            "page_size": 100,
        })
        req = Request("https://www.googleapis.com/drive/v3/files?" + params,
                      headers={"Authorization": "Bearer " + token})
        with urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        print(f"{label}: {len(data.get('files', []))} files (first page)")
        for file in data.get("files", [])[:5]:
            print(" -", file["name"], file.get("mimeType", ""))
        if data.get("nextPageToken"):
            print(" - Additional files exist")
    print("PASS: Google Drive read-only connectivity verified. Nothing was published.")

if __name__ == "__main__":
    try:
        main()
    except HTTPError as exc:
        # Do not print token-bearing request URLs or response bodies.
        raise SystemExit(f"Google API HTTP {exc.code}; check Drive credentials and folder access.") from None
