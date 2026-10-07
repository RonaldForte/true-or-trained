# ADR-0004: Image sourcing — small curated set from public datasets

**Status**: Accepted

## Context

The game needs a pool of images labeled "real" or "AI-generated." Options considered:
1. Generate AI images live via an API (Stable Diffusion, DALL-E, etc.)
2. Scrape images from the web
3. Use existing public, labeled AI-vs-real datasets

Live generation costs money per image and adds API dependency/latency. Scraping has copyright and provenance risk — can't always verify a scraped "real" photo is actually real, or that a scraped "AI" image is legally reusable. Budget and simplicity favor a one-time, free, pre-labeled source.

## Decision

Use a small curated set (~300–500 images) pulled once from existing public AI-vs-real datasets (e.g. CIFAKE, or similar Kaggle datasets with clear licensing), stored in Cloudflare R2.

## Consequences

- Zero ongoing generation cost, zero API dependency for serving images.
- Fixed pool size means repeat players will eventually see repeats — acceptable for a demo-scale game; can expand the pool later without changing the architecture.
- Must check dataset licensing before use/redistribution (even for a non-commercial demo) — a step to do before import, not after.
- Revisit if the game needs fresh/unique images per session (would require live generation or a much larger dataset, raising cost).
