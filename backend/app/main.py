import random
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="True or Trained API")

Label = Literal["real", "ai"]

# Placeholder image pool. Replaced by Postgres + R2 in later steps.
# Labels live here on the server only -- they are never sent with /round.
IMAGES: dict[str, dict] = {
    "img-001": {"url": "https://picsum.photos/id/10/512/512", "label": "real"},
    "img-002": {"url": "https://picsum.photos/id/20/512/512", "label": "ai"},
    "img-003": {"url": "https://picsum.photos/id/30/512/512", "label": "real"},
    "img-004": {"url": "https://picsum.photos/id/40/512/512", "label": "ai"},
    "img-005": {"url": "https://picsum.photos/id/50/512/512", "label": "real"},
}


class Round(BaseModel):
    image_id: str
    url: str


class Guess(BaseModel):
    image_id: str
    guess: Label


class GuessResult(BaseModel):
    correct: bool
    answer: Label


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/round", response_model=Round)
def get_round() -> Round:
    image_id = random.choice(list(IMAGES))
    return Round(image_id=image_id, url=IMAGES[image_id]["url"])


@app.post("/guess", response_model=GuessResult)
def submit_guess(body: Guess) -> GuessResult:
    image = IMAGES.get(body.image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Unknown image_id")
    return GuessResult(correct=body.guess == image["label"], answer=image["label"])
