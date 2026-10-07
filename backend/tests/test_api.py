import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import PAIRS, app
from app.pairs import load_pairs


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_round_returns_both_images_of_a_pair(client: TestClient) -> None:
    response = client.get("/round")

    assert response.status_code == 200
    body = response.json()
    pair = PAIRS[body["pair_id"]]
    assert body["caption"] == pair.caption
    assert {img["image_id"] for img in body["images"]} == {pair.real.image_id, pair.ai.image_id}
    for img in body["images"]:
        assert img["url"] == f"https://images.test/{img['image_id']}.webp"


def test_round_never_reveals_the_answer(client: TestClient) -> None:
    body = client.get("/round").json()

    # Exact key match: nothing that says which image is real may reach the client.
    assert set(body) == {"pair_id", "caption", "images"}
    for img in body["images"]:
        assert set(img) == {"image_id", "url"}


def test_round_order_is_randomized(client: TestClient) -> None:
    # The real image must not always be in the same position. 50 rounds all in the same
    # order would happen by chance with probability ~1e-15.
    first_is_real = set()
    for _ in range(50):
        body = client.get("/round").json()
        first_is_real.add(body["images"][0]["image_id"] == PAIRS[body["pair_id"]].real.image_id)
    assert first_is_real == {True, False}


def test_guess_real_image_is_correct(client: TestClient) -> None:
    response = client.post("/guess", json={"pair_id": "pair-1", "image_id": "real-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["generator"] == "Stable Diffusion XL"
    assert body["real"]["image_id"] == "real-1"
    assert body["ai"]["image_id"] == "ai-1"
    assert body["real"]["credit"]["license"] == "CC BY 2.0"


def test_guess_ai_image_is_wrong(client: TestClient) -> None:
    response = client.post("/guess", json={"pair_id": "pair-1", "image_id": "ai-1"})

    assert response.status_code == 200
    assert response.json()["correct"] is False


def test_guess_unknown_pair_returns_404(client: TestClient) -> None:
    response = client.post("/guess", json={"pair_id": "nope", "image_id": "real-1"})

    assert response.status_code == 404


def test_guess_image_from_another_pair_returns_400(client: TestClient) -> None:
    response = client.post("/guess", json={"pair_id": "pair-1", "image_id": "real-2"})

    assert response.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {"pair_id": "pair-1"},
        {"image_id": "real-1"},
        {"pair_id": 1, "image_id": ["real-1"]},
    ],
)
def test_guess_invalid_body_returns_422(client: TestClient, payload: dict) -> None:
    response = client.post("/guess", json=payload)

    assert response.status_code == 422


def test_cors_allows_local_frontend(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_load_pairs_missing_file_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not found"):
        load_pairs(tmp_path / "missing.json")


def test_load_pairs_empty_manifest_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text(json.dumps([]))

    with pytest.raises(RuntimeError, match="empty"):
        load_pairs(path)
