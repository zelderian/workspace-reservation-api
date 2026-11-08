import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import config as config_module
from app.core.config import Environment, Settings, env_files
from app.main import create_app

STRONG_KEY = "x" * 48


def make_settings(**overrides) -> Settings:
    values = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_db": "db",
        "secret_key": STRONG_KEY,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def failing_client(settings: Settings) -> TestClient:
    app = create_app(settings)

    @app.get("/boom")
    def boom():
        raise ZeroDivisionError("secret internal detail")

    app.router.routes.insert(0, app.router.routes.pop())
    return TestClient(app, raise_server_exceptions=False)


def test_env_file_is_chosen_by_app_env():
    assert env_files(Environment.SANDBOX) == (".env", ".env.sandbox")
    assert env_files(Environment.PRODUCTION) == (".env", ".env.production")


def test_app_env_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert config_module.current_env() == Environment.PRODUCTION


def test_sandbox_and_production_use_different_databases():
    sandbox = make_settings(app_env="sandbox", postgres_db="workspace_sandbox")
    production = make_settings(app_env="production", postgres_db="workspace_production")
    assert sandbox.database_url != production.database_url
    assert production.database_url.endswith("/workspace_production")


def test_production_forbids_debug():
    with pytest.raises(ValidationError):
        make_settings(app_env="production", debug=True)


@pytest.mark.parametrize("key", ["short-key", "change-me-to-a-long-random-string!!"])
def test_production_requires_strong_secret_key(key):
    with pytest.raises(ValidationError):
        make_settings(app_env="production", secret_key=key)


def test_production_500_hides_stacktrace():
    client = failing_client(make_settings(app_env="production"))
    response = client.get("/boom")
    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"detail", "error_id"}
    assert "Traceback" not in response.text
    assert "ZeroDivisionError" not in response.text
    assert "secret internal detail" not in response.text


def test_sandbox_debug_shows_stacktrace_to_developer():
    client = failing_client(make_settings(app_env="sandbox", debug=True))
    response = client.get("/boom")
    assert response.status_code == 500
    assert "ZeroDivisionError" in response.text


def test_docs_can_be_disabled():
    client = TestClient(create_app(make_settings(docs_enabled=False)))
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
