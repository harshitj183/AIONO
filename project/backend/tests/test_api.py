"""
Integration tests for the FastAPI REST API.
Tests the full HTTP request/response cycle including auth, investigations, and analytics.

Run: pytest tests/test_api.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


pytestmark = pytest.mark.asyncio(loop_scope="session")


# ── Shared async client ───────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def analyst_token(client):
    resp = await client.post("/api/auth/login", data={
        "username": "analyst", "password": "Analyst@123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def admin_token(client):
    resp = await client.post("/api/auth/login", data={
        "username": "admin", "password": "Admin@123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def viewer_token(client):
    resp = await client.post("/api/auth/login", data={
        "username": "viewer", "password": "Viewer@123"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── Health ────────────────────────────────────────────────────

async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("healthy", "degraded")
    assert "version" in body
    assert "database" in body


async def test_root_endpoint(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "app" in resp.json()


# ── Auth ──────────────────────────────────────────────────────

async def test_login_valid_credentials(client):
    resp = await client.post("/api/auth/login", data={
        "username": "analyst", "password": "Analyst@123"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "analyst"
    assert body["user"]["role"] == "analyst"


async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", data={
        "username": "analyst", "password": "WrongPassword"
    })
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post("/api/auth/login", data={
        "username": "ghost_user", "password": "anything"
    })
    assert resp.status_code == 401


async def test_get_me_with_valid_token(client, analyst_token):
    resp = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "analyst"
    assert body["role"] == "analyst"


async def test_get_me_without_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_get_me_with_invalid_token(client):
    resp = await client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalidtoken123"
    })
    assert resp.status_code == 401


# ── Analytics ─────────────────────────────────────────────────

async def test_dashboard_requires_auth(client):
    resp = await client.get("/api/analytics/dashboard")
    assert resp.status_code == 401


async def test_dashboard_returns_metrics(client, analyst_token):
    resp = await client.get("/api/analytics/dashboard", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "tickets_30d" in body["summary"]
    assert "revenue_30d" in body["summary"]
    assert "top_categories" in body
    assert "daily_ticket_trend" in body


async def test_schema_endpoint_returns_tables(client, analyst_token):
    resp = await client.get("/api/analytics/schema", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "tables" in body
    table_names = [t["name"] for t in body["tables"]]
    for expected in ["sales", "support_tickets", "employees", "expenses", "documents"]:
        assert expected in table_names
    assert body["db_size_kb"] > 0


# ── Investigations ────────────────────────────────────────────

async def test_submit_investigation_requires_auth(client):
    resp = await client.post("/api/investigations", json={
        "question": "Why did complaints increase this month?"
    })
    assert resp.status_code == 401


async def test_viewer_cannot_submit_investigation(client, viewer_token):
    resp = await client.post("/api/investigations", json={
        "question": "Why did complaints increase this month?"
    }, headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 403


async def test_question_too_short_rejected(client, analyst_token):
    resp = await client.post("/api/investigations", json={
        "question": "Hi?"
    }, headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp.status_code == 422


async def test_question_too_long_rejected(client, analyst_token):
    resp = await client.post("/api/investigations", json={
        "question": "x" * 501
    }, headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp.status_code == 422


async def test_submit_investigation_returns_id(client, analyst_token):
    resp = await client.post("/api/investigations", json={
        "question": "What products have the highest support ticket volume?"
    }, headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp.status_code == 202
    body = resp.json()
    assert "investigation_id" in body
    assert body["status"] == "running"
    assert isinstance(body["investigation_id"], int)


async def test_list_investigations_returns_own_only(client, analyst_token):
    resp = await client.get("/api/investigations", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "investigations" in body
    assert isinstance(body["investigations"], list)


async def test_admin_can_list_all_investigations(client, admin_token):
    resp = await client.get("/api/investigations", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "investigations" in body


async def test_get_nonexistent_investigation_returns_404(client, analyst_token):
    resp = await client.get("/api/investigations/999999", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp.status_code == 404


async def test_analyst_cannot_access_admin_investigations(client, analyst_token, admin_token):
    # Submit as admin
    resp = await client.post("/api/investigations", json={
        "question": "Are infrastructure costs above budget this quarter?"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 202
    admin_inv_id = resp.json()["investigation_id"]

    # Try to access as analyst — should be forbidden
    resp2 = await client.get(f"/api/investigations/{admin_inv_id}", headers={
        "Authorization": f"Bearer {analyst_token}"
    })
    assert resp2.status_code == 403
