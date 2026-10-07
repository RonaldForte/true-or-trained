# ADR-0003: Simple email/password auth + shared guest password

**Status**: Accepted

## Context

Need two kinds of access:
1. The project owner (and maybe future real users) with persistent accounts/scores.
2. Employers and friends who want to demo the game without creating an account.

Full OAuth (Google/GitHub login via a provider like Auth0 or Clerk) is more "production-grade" to show off, but adds setup time and, on some providers, cost past free-tier user limits.

## Decision

- Real accounts: email + password, hashed with bcrypt, stored in Supabase Postgres.
- Demo access: single shared password (`GUEST_PASSWORD` env var) that logs in as a read-only/limited "guest" session — no signup flow needed for employers.

## Consequences

- Minimal setup, no third-party auth dependency, no extra cost.
- Not as resume-flashy as "integrated OAuth," but correct, secure password hashing (bcrypt, no plaintext, no rolling your own crypto) is itself a legitimate thing to point to.
- If the game ever needs social login (e.g. for virality/sharing), revisit and layer in OAuth via a provider at that point — not needed for an initial demo-focused launch.
