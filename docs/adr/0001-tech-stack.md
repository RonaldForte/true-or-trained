# ADR-0001: Core tech stack — React + FastAPI

**Status**: Accepted

## Context

Building a portfolio-grade web game to demonstrate shipping a real product end-to-end, for job hunting. Need a stack that's:
- Widely recognized by employers
- Fast to build solo
- Cheap to run (target $0–20/month total, ideally lower)

## Decision

- **Frontend**: React with Vite (fast dev server, standard build tooling)
- **Backend**: Python with FastAPI (async, auto-generated API docs, lightweight)

## Consequences

- React is the most in-demand frontend skill — directly useful for job applications.
- FastAPI keeps backend small and readable, good for a solo dev, plays well with Postgres via SQLAlchemy/asyncpg.
- Two languages (JS + Python) means two toolchains to maintain, but both are common enough that this isn't a real burden.
- Revisit if the project needs server-side rendering or SEO (would push toward Next.js) — not a concern for a logged-in game.
