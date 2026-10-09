"""Database connection, configured from the DATABASE_URL environment variable."""

import os

from sqlalchemy import Engine, create_engine


def make_engine(url: str | None = None) -> Engine:
    """Create an engine for `url`, defaulting to DATABASE_URL. Fails loudly if neither is set."""
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. See DEVELOPER.md for the local database setup.")
    # pool_pre_ping checks a connection is alive before using it, since poolers and Render's
    # sleep/wake cycle can leave stale connections in the pool.
    return create_engine(url, pool_pre_ping=True)
