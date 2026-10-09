"""Load a pairs manifest (written by scripts/build_image_set.py) into the database.

Usage, from backend/ with DATABASE_URL set:

    .venv\\Scripts\\python -m app.seed ..\\data\\build\\manifest.json

Safe to re-run: rows that already exist are left untouched, so a pair's status (e.g. one an
admin rejected) is never reset by seeding again.
"""

import argparse
from pathlib import Path

from sqlalchemy import Connection, func, select
from sqlalchemy.dialects.postgresql import insert

from app.db import make_engine
from app.models import Image, Pair
from app.pairs import Pair as ManifestPair, load_pairs


def image_row(side) -> dict:
    return {
        "id": side.image_id,
        "credit_source": side.credit.source,
        "license": side.credit.license,
        "license_url": side.credit.license_url,
        "source_url": side.credit.source_url,
    }


def seed(conn: Connection, pairs: list[ManifestPair]) -> tuple[int, int]:
    """Insert any missing images and pairs. Returns (images added, pairs added)."""
    images = [image_row(side) for pair in pairs for side in (pair.real, pair.ai)]
    added_images = conn.execute(
        insert(Image).values(images).on_conflict_do_nothing().returning(Image.id)
    ).all()

    rows = [
        {
            "id": pair.id,
            "caption": pair.caption,
            "generator": pair.generator,
            "real_image_id": pair.real.image_id,
            "ai_image_id": pair.ai.image_id,
            "source": "dataset",
            # The dataset was reviewed on the contact sheet before upload, so it starts approved.
            "status": "approved",
        }
        for pair in pairs
    ]
    added_pairs = conn.execute(insert(Pair).values(rows).on_conflict_do_nothing().returning(Pair.id)).all()
    return len(added_images), len(added_pairs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path, help="path to manifest.json")
    args = parser.parse_args()

    pairs = list(load_pairs(args.manifest).values())
    engine = make_engine()
    # engine.begin() wraps everything in one transaction: all rows land, or none do.
    with engine.begin() as conn:
        added_images, added_pairs = seed(conn, pairs)
        total = conn.execute(select(func.count()).select_from(Pair)).scalar_one()
    print(f"Added {added_images} images and {added_pairs} pairs ({total} pairs in database).")


if __name__ == "__main__":
    main()
