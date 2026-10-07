import os
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pairs import Credit, load_pairs

app = FastAPI(title="True or Trained API")

# Comma-separated list of frontend origins allowed to call this API from a browser.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# The manifest says which image in each pair is real, so it lives outside the public repo:
# data/build/ locally (gitignored), a Render Secret File in production.
PAIRS_FILE = Path(
    os.environ.get("PAIRS_FILE", Path(__file__).resolve().parents[2] / "data" / "build" / "manifest.json")
)
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL", "https://images.trueortrained.com").rstrip("/")

PAIRS = load_pairs(PAIRS_FILE)


def image_url(image_id: str) -> str:
    return f"{IMAGE_BASE_URL}/{image_id}.webp"


class RoundImage(BaseModel):
    image_id: str
    url: str


class Round(BaseModel):
    pair_id: str
    caption: str
    images: list[RoundImage]


class Guess(BaseModel):
    pair_id: str
    image_id: str


class RevealedImage(BaseModel):
    image_id: str
    credit: Credit


class GuessResult(BaseModel):
    correct: bool
    generator: str
    real: RevealedImage
    ai: RevealedImage


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/round", response_model=Round)
def get_round() -> Round:
    pair = random.choice(list(PAIRS.values()))
    sides = [pair.real, pair.ai]
    # Random order on every request, so position can't give the answer away.
    random.shuffle(sides)
    return Round(
        pair_id=pair.id,
        caption=pair.caption,
        images=[RoundImage(image_id=side.image_id, url=image_url(side.image_id)) for side in sides],
    )


@app.post("/guess", response_model=GuessResult)
def submit_guess(body: Guess) -> GuessResult:
    pair = PAIRS.get(body.pair_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Unknown pair_id")
    if body.image_id not in (pair.real.image_id, pair.ai.image_id):
        raise HTTPException(status_code=400, detail="image_id is not part of this pair")
    return GuessResult(
        correct=body.image_id == pair.real.image_id,
        generator=pair.generator,
        real=RevealedImage(image_id=pair.real.image_id, credit=pair.real.credit),
        ai=RevealedImage(image_id=pair.ai.image_id, credit=pair.ai.credit),
    )
