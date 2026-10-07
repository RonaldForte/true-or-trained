import pytest
from fastapi.testclient import TestClient

from app.main import IMAGES, app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def image_with_label(label: str) -> str:
    """Return the id of some image with the given label, so tests don't hardcode data."""
    return next(image_id for image_id, image in IMAGES.items() if image["label"] == label)


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_round_returns_image_without_label(client: TestClient) -> None:
    response = client.get("/round")

    assert response.status_code == 200
    body = response.json()
    # Exact key match: the label must never reach the client, or players could cheat.
    assert set(body) == {"image_id", "url"}
    assert body["image_id"] in IMAGES
    assert body["url"] == IMAGES[body["image_id"]]["url"]


@pytest.mark.parametrize("label", ["real", "ai"])
def test_correct_guess(client: TestClient, label: str) -> None:
    response = client.post("/guess", json={"image_id": image_with_label(label), "guess": label})

    assert response.status_code == 200
    assert response.json() == {"correct": True, "answer": label}


def test_wrong_guess_reveals_answer(client: TestClient) -> None:
    response = client.post("/guess", json={"image_id": image_with_label("real"), "guess": "ai"})

    assert response.status_code == 200
    assert response.json() == {"correct": False, "answer": "real"}


def test_guess_unknown_image_returns_404(client: TestClient) -> None:
    response = client.post("/guess", json={"image_id": "does-not-exist", "guess": "real"})

    assert response.status_code == 404


def test_cors_allows_local_frontend(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "payload",
    [
        {"image_id": "img-001", "guess": "maybe"},
        {"image_id": "img-001"},
        {"guess": "real"},
    ],
)
def test_guess_invalid_body_returns_422(client: TestClient, payload: dict) -> None:
    response = client.post("/guess", json=payload)

    assert response.status_code == 422
