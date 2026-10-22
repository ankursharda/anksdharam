# Anks Lifeon daily devotional Reels

Daily 08:00 IST GitHub Actions workflow currently runs in PREVIEW-ONLY mode.
It does not upload or publish Instagram media.

Add approved entries to `instagram-reels-approved.json` with fields:
`id`, `video_url` (public HTTPS URL of a vertical video file, not a YouTube watch page),
`caption_hi` (Devanagari Hindi), `audio_rights_confirmed` (true),
`video_rights_confirmed` (true).
Only enter true after independently verifying the rights.
A Reel must be a real video, not a still image URL.

`instagram-reels-history.json` holds confirmed publications as
`{"id":"...", "date":"YYYY-MM-DD"}` to prevent reuse within 30 days.
Do not add a history record for previews or failed posts.

The preview artifact shows the selected candidate. Empty manifest means
a successful no-op, not a published Reel.

Before enabling live publication: validate @anks_lifeon credentials and
content publishing permission; validate playable vertical video URL and
audio rights; add idempotent publish code and verified media ID/permalink
logging; persist confirmed history reliably. Never expose tokens in logs.
