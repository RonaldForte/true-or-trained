# True or Trained

A web game where you guess whether a presented image is **real** or **AI-generated**.

Live at: https://trueortrained.com *(not deployed yet)*

## Status

Early scaffold. Building in slow increments, one feature at a time. See `docs/adr/` for the reasoning behind each major decision.

## Stack

- **Frontend**: React (Vite), hosted on Cloudflare Pages (free)
- **Backend**: Python (FastAPI), hosted on Render (free tier)
- **Database**: Supabase Postgres (free tier) — user accounts, scores, leaderboard
- **Image storage**: Cloudflare R2 (free tier, no egress fees)
- **Domain**: trueortrained.com (Cloudflare Registrar)

Target running cost: **$0–5/month**. See [`docs/adr/0002-hosting-platform.md`](docs/adr/0002-hosting-platform.md) for why.

## Auth

- Email + password accounts for real users
- Shared guest password for employer/friend demo access (no signup needed)

See [`docs/adr/0003-auth-strategy.md`](docs/adr/0003-auth-strategy.md).

## Images

Small curated set (~300–500) pulled from existing public AI-vs-real datasets — no live image generation, no scraping. See [`docs/adr/0004-image-sourcing-storage.md`](docs/adr/0004-image-sourcing-storage.md).

## Development

*(To be filled in as the project takes shape — local setup, env vars, running frontend/backend.)*

## Docs

- [`docs/adr/`](docs/adr/) — Architecture Decision Records, one per major technical choice
