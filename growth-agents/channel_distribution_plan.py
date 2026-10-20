#!/usr/bin/env python3
"""Prepare cross-platform, channel-wide distribution plan (no unauthorized posting)."""
import json
from pathlib import Path
from datetime import datetime, timezone

root = Path("growth-agents")
catalog = json.loads((root / "channel-catalog.json").read_text(encoding="utf-8"))
videos = sorted((v for v in catalog["videos"] if v.get("privacy") == "public"),
                key=lambda v: v.get("opportunity_score", 0), reverse=True)
out = root / "output"
out.mkdir(exist_ok=True)
items = []
for v in videos:
    title = " ".join(v["title"].split())
    link = f'https://youtu.be/{v["video_id"]}'
    items.append({
        "video_id": v["video_id"],
        "category": v["category"],
        "opportunity_score": v["opportunity_score"],
        "youtube_url": link,
        "thumbnail_url": f'https://i.ytimg.com/vi/{v["video_id"]}/hqdefault.jpg',
        "instagram": {"caption": f'{title}\n\nExplore the full film on YouTube: @anksdharam\n#AnksDharam #HinduMythology #AIAnimation'},
        "facebook": {"text": f'{title}\n\nWatch the film on Anks Dharam: {link}\n#AnksDharam #HinduMythology'},
        "pinterest": {"title": title[:95], "description": f'Explore {title}. Watch Anks Dharam AI Films.', "destination_url": link},
        "publishing_status": {"instagram": "handled_by_separate_publisher", "facebook": "authorization_required", "pinterest": "authorization_required"}
    })
(out / "channel-distribution-plan.json").write_text(json.dumps({
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "videos": items
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Prepared platform-specific distribution drafts for {len(items)} public videos; no Facebook/Pinterest publication attempted.")
