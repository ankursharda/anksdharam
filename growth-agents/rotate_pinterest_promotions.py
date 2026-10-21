#!/usr/bin/env python3
"""Publish one eligible video Pin to the owner's board, only when explicitly enabled."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path("growth-agents")
LEDGER = ROOT / "pinterest-published.json"
CATALOG = ROOT / "channel-catalog.json"
API = "https://api.pinterest.com/v5"

def request(method, path, token, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(API + path, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=40) as res:
            return json.load(res)
    except HTTPError as exc:
        # Do not expose request headers or bearer tokens.
        raise RuntimeError(f"Pinterest API HTTP {exc.code} on {path}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Pinterest request failed: {type(exc).__name__}") from None

def main():
    if os.getenv("PINTEREST_PUBLISH_ENABLED", "").lower() != "true":
        print("Pinterest publishing disabled until write access and production approval are verified.")
        return
    token = os.getenv("PINTEREST_ACCESS_TOKEN", "").strip()
    board_id = os.getenv("PINTEREST_BOARD_ID", "").strip()
    if not token or not board_id:
        raise SystemExit("Pinterest enabled but PINTEREST_ACCESS_TOKEN or PINTEREST_BOARD_ID is missing.")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    posted = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    videos = sorted((v for v in catalog["videos"] if v.get("privacy") == "public"),
                    key=lambda v: v.get("opportunity_score", 0), reverse=True)
    for video in videos:
        vid = video["video_id"]
        if vid in posted:
            continue
        title = " ".join(video["title"].split())
        result = request("POST", "/pins", token, {
            "board_id": board_id,
            "title": title[:100],
            "description": (f"{title}\nAI-assisted films, devotional stories and Hindu mythology by Anks Dharam. Watch on YouTube.")[:500],
            "link": f"https://www.youtube.com/watch?v={vid}",
            "media_source": {"source_type": "image_url", "url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"},
        })
        pin_id = result.get("id")
        if not pin_id:
            raise SystemExit("Pinterest did not confirm a Pin ID; publishing ledger unchanged.")
        posted[vid] = {"title": title, "pin_id": pin_id, "board_id": board_id}
        LEDGER.write_text(json.dumps(posted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Published one Pinterest Pin for {vid}; Pin ID {pin_id}")
        return
    print("All eligible public videos have been promoted on Pinterest.")

if __name__ == "__main__":
    main()
