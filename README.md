# True or Trained

A web game where you guess whether a presented image is **real** or **AI-generated**.

**Live at: https://trueortrained.com**

## Status

Playable end-to-end with a placeholder image pool. Next up: a real curated image set, then accounts and a leaderboard. Building in slow increments, one feature at a time — each lands as its own [pull request](https://github.com/RonaldForte/true-or-trained/pulls?q=is%3Apr+is%3Amerged), with CI required to pass. See `docs/adr/` for the reasoning behind each major decision.

> The backend runs on a free tier that sleeps when idle, so the first load can take up to a minute.

## Stack

- **Frontend**: React + TypeScript (Vite), hosted on Cloudflare Workers static assets (free)
- **Backend**: Python (FastAPI), hosted on Render (free tier) at `api.trueortrained.com`
- **Database**: Supabase Postgres (free tier) — user accounts, scores, leaderboard *(planned)*
- **Image storage**: Cloudflare R2 (free tier, no egress fees) *(planned)*
- **CI**: GitHub Actions — pytest, lint, type-check, and build on every PR
- **Domain**: trueortrained.com (Cloudflare Registrar)

Target running cost: **$0–5/month**. See [`docs/adr/0002-hosting-platform.md`](docs/adr/0002-hosting-platform.md) for why.

## Auth

- Email + password accounts for real users
- Shared guest password for employer/friend demo access (no signup needed)

See [`docs/adr/0003-auth-strategy.md`](docs/adr/0003-auth-strategy.md).

## Images

Small curated set (~300–500) pulled from existing public AI-vs-real datasets — no live image generation, no scraping. See [`docs/adr/0004-image-sourcing-storage.md`](docs/adr/0004-image-sourcing-storage.md).

## Development

See [`DEVELOPER.md`](DEVELOPER.md) for local setup and running the app.

## Docs

- [`docs/adr/`](docs/adr/) — Architecture Decision Records, one per major technical choice
