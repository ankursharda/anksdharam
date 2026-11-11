#!/usr/bin/env python3
"""Prepare platform-specific promotional drafts; never publish automatically."""
import datetime as dt
import json
from pathlib import Path

url = "https://youtu.be/3MHOr1g1N9M"
title = "Shani Dev Childhood Story | Why Did Surya Dev Reject His Son? | AI Mythology Film"
posts = {
    "facebook": (
        "Why did Surya Dev reject his own son, Shani Dev? Discover a powerful childhood story "
        "from Hindu mythology in this animated film by Anks Dharam AI Films. "
        "Watch the full story: " + url + "\n\n#ShaniDev #HinduMythology #AIAnimation"
    ),
    "instagram": (
        "A father. A son. A story of Shani Dev's childhood. ☀️\n"
        "Explore the full animated mythology film on YouTube — Anks Dharam AI Films. "
        "Link: " + url + "\n\n#ShaniDev #ShanidevStory #HinduMythology #AIAnimation #AnksDharam"
    ),
    "threads": (
        "Why did Surya Dev reject Shani Dev? A childhood story retold through AI-assisted "
        "mythological animation. Watch: " + url + " #ShaniDev #HinduMythology"
    ),
    "linkedin": (
        "Anks Dharam AI Films explores Hindu mythology through AI-assisted animation. "
        "Our Shani Dev childhood film tells the story of Shani Dev and Surya Dev. "
        "Watch the film: " + url + "\n\n#Animation #AIFilmmaking #Storytelling"
    ),
    "x": (
        "Why did Surya Dev reject Shani Dev? Explore the childhood story in an "
        "AI-assisted mythology film. " + url + " #ShaniDev #AIAnimation"
    ),
}
out = Path("growth-agents/output")
out.mkdir(parents=True, exist_ok=True)
stamp = dt.datetime.now(dt.timezone.utc).isoformat()
(out / "shani-distribution-drafts.json").write_text(
    json.dumps({"generated_at_utc": stamp, "video_url": url, "video_title": title,
                "status": "DRAFT_ONLY_NOT_PUBLISHED", "posts": posts},
               indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
lines = ["# Shani Dev distribution drafts", "", f"Generated: {stamp}",
         f"Video: {url}", "",
         "**Approval required before publishing.** These are draft captions only.",
         "Do not post identical text repeatedly or imply the video has a verified audience reach.",
         ""]
for platform, copy in posts.items():
    lines.extend([f"## {platform.title()}", "", copy, ""])
(out / "shani-distribution-drafts.md").write_text("\n".join(lines), encoding="utf-8")
print(f"Prepared {len(posts)} platform-specific drafts; no posts published.")
