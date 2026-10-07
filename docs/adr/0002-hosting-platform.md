# ADR-0002: Hosting on Cloudflare Pages + Render + Supabase, not AWS

**Status**: Accepted

## Context

Only user is the project owner plus a handful of friends/employers demoing. Traffic will be near-zero. Budget ceiling is $10–20/month, ideally much less. AWS was the initial instinct (S3, EC2) since it's a common resume keyword, but:
- AWS free tier expires after 12 months
- S3 charges for egress (data leaving the bucket) — easy to rack up cost without noticing
- EC2/IAM/VPC setup has real time cost for a solo dev at this scale

Domain was purchased through Cloudflare Registrar, which makes Cloudflare's own hosting products (Pages, R2) a natural fit — one dashboard, one account, no cross-provider DNS fiddling.

## Decision

- **Frontend**: Cloudflare Pages (free, pairs with the Cloudflare-registered domain)
- **Backend**: Render free tier (simple Python app hosting, no server management)
- **Database**: Supabase Postgres free tier (real Postgres, free dashboard, generous free quota)
- **Image storage**: Cloudflare R2 (S3-compatible API, free egress — unlike S3)

## Consequences

- Expected cost: $0–5/month at current scale (domain renewal ~$10-12/**year** is the only near-certain cost).
- Free tiers on Render/Supabase can mean cold starts (first request after idle is slow) — acceptable for a demo project, would need a paid tier if traffic grew.
- Less AWS hands-on experience to show off directly, but the architecture (object storage, managed Postgres, static hosting + API backend) is the same shape as an AWS-based version — the concepts transfer, and this can be mentioned in interviews.
- Revisit if real user growth happens and free-tier limits (requests/month, storage, cold starts) start to bind.
