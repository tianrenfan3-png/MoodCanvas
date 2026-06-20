import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.config import get_settings
from app.main import create_app
from app.services.analyzer.factory import reset_analyzer
from app.services.firebase import init_firebase, reset_repositories
from app.services.storage import get_memory_store


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ANALYZER_TYPE", "mock")
    get_settings.cache_clear()
    reset_analyzer()
    reset_repositories()
    get_memory_store().clear()
    init_firebase(get_settings())
    yield
    get_settings.cache_clear()
    reset_analyzer()
    reset_repositories()


@pytest.fixture
async def client():
    app = create_app()
    # Warm up mock analyzer
    from app.services.analyzer.factory import get_analyzer

    analyzer = get_analyzer()
    if not analyzer.is_ready():
        analyzer.warmup()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_test_image(color=(100, 150, 200)) -> bytes:
    img = Image.new("RGB", (200, 200), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def auth_headers(user_id: str = "test-user-123") -> dict:
    return {"X-Test-User-Id": user_id}


@pytest.mark.asyncio
async def test_ping(client):
    resp = await client.get("/ping")
    assert resp.status_code == 200
    assert resp.json()["message"] == "pong"


@pytest.mark.asyncio
async def test_cors_allows_github_pages(client):
    resp = await client.options(
        "/predict",
        headers={
            "Origin": "https://tianrenfan3-png.github.io",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://tianrenfan3-png.github.io"


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["analyzer_ready"] is True


@pytest.mark.asyncio
async def test_moods(client):
    resp = await client.get("/moods")
    assert resp.status_code == 200
    moods = resp.json()["moods"]
    assert len(moods) == 6
    assert "Happy" in moods
    assert "Calm" in moods


@pytest.mark.asyncio
async def test_predict_requires_auth(client):
    image = make_test_image()
    resp = await client.post("/predict", files={"file": ("draw.png", image, "image/png")})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_predict_success(client):
    image = make_test_image()
    resp = await client.post(
        "/predict",
        files={"file": ("draw.png", image, "image/png")},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mood"] in ["Happy", "Sad", "Calm", "Angry", "Anxious", "Excited"]
    assert 0 <= data["confidence"] <= 1
    assert abs(sum(data["scores"].values()) - 1.0) < 0.01
    assert data["history_id"] is not None
    assert "explanation" in data["analysis_details"]


@pytest.mark.asyncio
async def test_predict_rejects_blank(client):
    image = make_test_image(color=(255, 255, 255))
    resp = await client.post(
        "/predict",
        files={"file": ("draw.png", image, "image/png")},
        headers=auth_headers(),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_history_crud(client):
    image = make_test_image()
    predict_resp = await client.post(
        "/predict",
        files={"file": ("draw.png", image, "image/png")},
        headers=auth_headers("user-a"),
    )
    history_id = predict_resp.json()["history_id"]

    list_resp = await client.get("/history", headers=auth_headers("user-a"))
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    get_resp = await client.get(f"/history/{history_id}", headers=auth_headers("user-a"))
    assert get_resp.status_code == 200

    # Other user cannot access
    other_resp = await client.get(f"/history/{history_id}", headers=auth_headers("user-b"))
    assert other_resp.status_code == 404

    del_resp = await client.delete(f"/history/{history_id}", headers=auth_headers("user-a"))
    assert del_resp.status_code == 200

    get_after = await client.get(f"/history/{history_id}", headers=auth_headers("user-a"))
    assert get_after.status_code == 404


@pytest.mark.asyncio
async def test_clear_history(client):
    image = make_test_image()
    await client.post(
        "/predict",
        files={"file": ("draw.png", image, "image/png")},
        headers=auth_headers("clear-user"),
    )
    resp = await client.delete("/history", headers=auth_headers("clear-user"))
    assert resp.status_code == 200
    assert resp.json()["deleted_count"] >= 1

    list_resp = await client.get("/history", headers=auth_headers("clear-user"))
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_rewards_status(client):
    resp = await client.get("/rewards/status", headers=auth_headers("reward-user"))
    assert resp.status_code == 200
    data = resp.json()
    assert "coins" in data
    assert "streak" in data
    assert data["can_claim_today"] is True


@pytest.mark.asyncio
async def test_rewards_claim_on_predict(client):
    image = make_test_image()
    await client.post(
        "/predict",
        files={"file": ("draw.png", image, "image/png")},
        headers=auth_headers("reward-user-2"),
    )
    resp = await client.get("/rewards/status", headers=auth_headers("reward-user-2"))
    data = resp.json()
    assert data["coins"] >= 10
    assert data["streak"] >= 1
