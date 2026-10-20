# YouTube Engagement OAuth Setup

This agent is separate from vidIQ and the read-only YOUTUBE_API_KEY.

1. In Google Cloud Console, choose or create a project and enable YouTube Data API v3.
2. Configure the OAuth consent screen (external/testing is fine for the owner). Add your Google account as a test user if required.
3. Create an OAuth client for a desktop application.
4. Authorize the **Anks Dharam AI Films** YouTube identity with the scope `https://www.googleapis.com/auth/youtube.force-ssl` and obtain a refresh token using a trusted local OAuth flow. Never commit OAuth credentials or tokens to GitHub.
5. Add three GitHub Actions repository secrets: `YOUTUBE_OAUTH_CLIENT_ID`, `YOUTUBE_OAUTH_CLIENT_SECRET`, `YOUTUBE_OAUTH_REFRESH_TOKEN`.
6. Add one queue entry per individually approved comment. Each must include `approved: true`, `approval_reference`, `type` (`reply` or `top_level`), `video_id`, `text`, `target_author` (for replies), and `parent_comment_id` for replies.
7. Run **Approved YouTube Engagement** with publish=false first. Only set publish=true after reviewing the exact target, comment and final text.

Caution: The queue is deliberately empty. Never insert unapproved posts. A successful post remains in the queue unless manually removed; **remove published entries immediately** to avoid duplicate posts. For this reason, do not run publish=true repeatedly. GitHub Actions logs identify posted comment IDs; check them before retrying after any interruption.

The YouTube API can post top-level comments to other channels' videos only when that video allows comments and the authorized identity has permission. This does not grant access to viewer identities. Avoid unsolicited promotion, bulk commenting, and repetitive replies.
