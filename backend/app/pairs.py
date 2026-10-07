from pathlib import Path

from pydantic import BaseModel, TypeAdapter


class Credit(BaseModel):
    source: str
    license: str
    license_url: str
    source_url: str


class Side(BaseModel):
    image_id: str
    credit: Credit


class Pair(BaseModel):
    id: str
    caption: str
    generator: str
    real: Side
    ai: Side


def load_pairs(path: Path) -> dict[str, Pair]:
    """Load and validate the pairs manifest written by scripts/build_image_set.py, keyed by pair id."""
    if not path.is_file():
        raise RuntimeError(
            f"Pairs manifest not found at {path}. Build it (see DEVELOPER.md) or set PAIRS_FILE."
        )
    pairs = TypeAdapter(list[Pair]).validate_json(path.read_bytes())
    if not pairs:
        raise RuntimeError(f"Pairs manifest at {path} is empty.")
    return {pair.id: pair for pair in pairs}
