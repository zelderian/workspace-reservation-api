import asyncio

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import session as db_session_module
from app.main import create_app


def test_db_slots_match_pool_capacity():
    app = create_app()
    with TestClient(app):
        assert app.state.db_slots._value == settings.db_pool_capacity


def test_overloaded_db_returns_503_instead_of_hanging(monkeypatch):
    monkeypatch.setattr(db_session_module.settings, "db_pool_timeout", 0.1)
    app = create_app()
    with TestClient(app) as client:
        app.state.db_slots = asyncio.Semaphore(0)
        response = client.get("/health/db")
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
