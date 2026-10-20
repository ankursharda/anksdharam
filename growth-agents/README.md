# Anks Dharam Growth Agents

Status: scaffold only; not deployed or scheduled. This work lives on the `ai-growth-agents` branch and does not alter the published website.

## Target
- Video: https://youtu.be/3MHOr1g1N9M
- Goal: grow genuine engaged YouTube views; no guaranteed count, artificial views, spam, or fake engagement.

## Agents
1. **Analytics:** Read YouTube performance; report views, watch time, retention, sources, and day-over-day changes where accessible.
2. **SEO:** Review video title, description, thumbnail, and discovery signals; prepare suggested changes, not automatic edits.
3. **Distribution:** Draft differentiated Facebook/Instagram/Pinterest posts and check duplicates. Publishing requires prior user approval.
4. **Ads:** Analyze Google Ads placement costs and quality signals; recommend experiments. Never change budgets or campaigns automatically.
5. **Reporter:** Compile daily findings and prioritize one measurable next step.

## Data sources
- Windsor.ai: YouTube, Google Ads, Facebook Organic (connected in ChatGPT; API credentials for GitHub/Cloudflare not yet configured).
- Metricool and vidIQ: connected in ChatGPT; unattended GitHub access is not yet configured.

## Deployment prerequisites
- Configure approved API credentials as GitHub Actions secrets or Cloudflare secrets; do not commit secrets.
- Implement connectors and test read-only analytics before scheduling.
- Establish human approval for posting and ads changes.

## Isolation
No edits to website files, content sections, or the current website deployment workflow.
