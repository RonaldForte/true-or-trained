# ADR-0005: Frontend on Cloudflare Workers static assets, not Pages

**Status**: Accepted (supersedes the frontend part of ADR-0002)

## Context

ADR-0002 chose Cloudflare Pages for the frontend. When connecting the repo, Cloudflare's dashboard steered new projects to Workers instead — Cloudflare now positions Workers with static assets as the successor to Pages, with new features landing there first.

The frontend is a static Vite build (HTML, JS, CSS). It needs no server-side code.

## Decision

Host the frontend as a Worker serving static assets only, configured in `frontend/wrangler.jsonc`:

- `assets.directory: ./dist` — serves the Vite build output, no Worker script
- `not_found_handling: single-page-application` — unknown paths serve `index.html` for client-side routing
- Built and deployed by Workers Builds on every push to `main`
- Custom domain `trueortrained.com` attached to the Worker

Everything else in ADR-0002 (Render, Supabase, R2) is unchanged.

## Consequences

- Still free: static asset requests on Workers are free and unmetered.
- Deployment config lives in the repo (`wrangler.jsonc`) rather than only in a dashboard, and the `wrangler` version is pinned in `package-lock.json`.
- Same Cloudflare account and dashboard as the domain and DNS — ADR-0002's "one provider" reasoning still holds.
- Adding server-side logic later (e.g. an API proxy, edge caching rules) is possible in the same Worker without migrating hosts.
- A static-assets-only Worker can't have runtime variables or bindings; build-time variables like `VITE_API_URL` are set under Builds instead. If server-side code is ever added, those features become available.
