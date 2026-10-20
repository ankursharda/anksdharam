#!/usr/bin/env python3
"""Read-only SEO review for the Shani Dev film using public YouTube metadata."""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

video_id = "3MHOr1g1N9M"
key = os.environ.get("YOUTUBE_API_KEY")
if not key:
    raise SystemExit("Missing YOUTUBE_API_KEY repository secret")
params = urllib.parse.urlencode({"part": "snippet,statistics", "id": video_id, "key": key})
url = "https://www.googleapis.com/youtube/v3/videos?" + params
with urllib.request.urlopen(url, timeout=30) as response:
    data = json.load(response)
if not data.get("items"):
    raise SystemExit("Video not found or unavailable")
item = data["items"][0]
snippet = item["snippet"]
title = snippet.get("title", "")
description = snippet.get("description", "")
tags = snippet.get("tags", [])
stats = item.get("statistics", {})
date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
lines = [
    "# Shani Dev Part 1 — SEO review",
    "",
    f"Generated: {date}",
    f"Video: https://www.youtube.com/watch?v={video_id}",
    "",
    "## Current public metadata",
    f"- Title ({len(title)} characters): {title}",
    f"- Description length: {len(description)} characters",
    f"- Public tags count: {len(tags)}",
    f"- Public views: {stats.get('viewCount', 'unavailable')}",
    "",
    "## Rule-based checks (recommendations only)",
]
if len(title) > 70:
    lines.append("- Consider a shorter title with the primary story and character earlier; preserve the festival-selection distinction in the description.")
else:
    lines.append("- Title length is reasonably compact; prioritize relevance and clarity rather than changing it merely for length.")
if "shani" not in title.lower() and "shanidev" not in title.lower():
    lines.append("- Put Shani Dev in the title so the subject is immediately recognizable.")
else:
    lines.append("- The title already identifies Shani Dev.")
if len(description.strip()) < 300:
    lines.append("- Consider expanding the description with a unique 2-sentence synopsis, film credits, official selection, and links to related episodes.")
else:
    lines.append("- Description has substantive length; manually check that the opening 2 lines summarize the story and film.")
if not any(term in description.lower() for term in ("shani", "shanidev", "शनिदेव")):
    lines.append("- Mention the Shani Dev childhood story naturally in the first two lines of the description.")
lines += [
    "- Use the film-festival official selection claim only with its accurate festival name and supporting evidence.",
    "- Test alternate thumbnail/title combinations only when YouTube Studio provides reliable impressions and CTR data.",
    "- Avoid keyword stuffing, misleading promises, or claims that SEO alone guarantees reach.",
    "",
    "## Suggested title for manual consideration",
    "Shani Dev Childhood Story | Why Did Surya Dev Reject His Son? | AI Mythology Film",
    "",
    "## Suggested opening description (draft; verify story details)",
    "Discover the childhood story of Shani Dev and his relationship with Surya Dev in this AI-assisted Hindu mythology animated film by Anks Dharam AI Films.",
    "",
    "## Limitations",
    "This report uses public metadata only. It does not measure YouTube search rankings, impressions, CTR, audience retention, or actual keyword volume.",
    "Nothing is published or edited on YouTube by this agent.",
]
output = Path("growth-agents/output/shani-seo-review.md")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Created {output}; title length={len(title)}; description length={len(description)}")
