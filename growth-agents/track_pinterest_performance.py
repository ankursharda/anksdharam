#!/usr/bin/env python3
"""Collect Pinterest Pin analytics for confirmed Anks Dharam promotions.

Runs safely without credentials; never prints tokens. Requires a Pinterest OAuth
token with pins:read and the appropriate analytics permissions.
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path("growth-agents")
LEDGER = ROOT / "pinterest-published.json"
OUTPUT = ROOT / "output" / "pinterest-tracking.json"
METRICS = "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK"

def main():
    token = os.getenv("PINTEREST_ACCESS_TOKEN", "").strip()
    if not token:
        print("Pinterest tracking pending: OAuth access token not configured.")
        return
    if not LEDGER.exists():
        print("Pinterest tracking pending: no confirmed published Pins.")
        return
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=29)
    rows = []
    for video_id, item in ledger.items():
        pin_id = item.get("pin_id")
        if not pin_id:
            continue
        params = urlencode({"start_date": start.isoformat(), "end_date": end.isoformat(), "metric_types": METRICS})
        req = Request(f"https://api.pinterest.com/v5/pins/{pin_id}/analytics?{params}",
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        try:
            with urlopen(req, timeout=30) as response:
                analytics = json.load(response)
            rows.append({"video_id": video_id, "pin_id": pin_id, "analytics": analytics})
        except HTTPError as error:
            rows.append({"video_id": video_id, "pin_id": pin_id, "error": f"HTTP {error.code}"})
        except (URLError, TimeoutError, ValueError) as error:
            rows.append({"video_id": video_id, "pin_id": pin_id, "error": type(error).__name__})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"start_date": start.isoformat(), "end_date": end.isoformat(), "pins": rows},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Pinterest analytics checked for {len(rows)} confirmed Pins; output: {OUTPUT}")

if __name__ == "__main__":
    main()
