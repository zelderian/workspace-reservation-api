import os

os.environ["APP_ENV"] = "sandbox"
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core import security  # noqa: E402
from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402

PASSWORD = "StrongPass123"


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    """Для тестів знижуємо кількість ітерацій PBKDF2, щоб вони працювали швидко."""
    monkeypatch.setattr(security, "PBKDF2_ITERATIONS", 1000)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user(db, email, role):
    user = User(
        email=email,
        full_name=email.split("@")[0],
        hashed_password=security.hash_password(PASSWORD),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, email):
    response = client.post(
        "/auth/login", data={"username": email, "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def user_a(db_session):
    return _create_user(db_session, "a@example.com", UserRole.USER)


@pytest.fixture()
def user_b(db_session):
    return _create_user(db_session, "b@example.com", UserRole.USER)


@pytest.fixture()
def admin(db_session):
    return _create_user(db_session, "admin@example.com", UserRole.ADMIN)


@pytest.fixture()
def headers_a(client, user_a):
    return _headers(client, "a@example.com")


@pytest.fixture()
def headers_b(client, user_b):
    return _headers(client, "b@example.com")


@pytest.fixture()
def headers_admin(client, admin):
    return _headers(client, "admin@example.com")


@pytest.fixture()
def resource_id(client, headers_admin):
    location = client.post(
        "/locations",
        json={"name": "Hub", "city": "Chernivtsi", "address": "Main st 1"},
        headers=headers_admin,
    ).json()
    resource = client.post(
        "/resources",
        json={
            "location_id": location["id"],
            "name": "Room 1",
            "type": "meeting_room",
            "capacity": 8,
            "price_per_hour": "15.50",
        },
        headers=headers_admin,
    ).json()
    return resource["id"]


@pytest.fixture()
def slot():
    """Фабрика часових інтервалів у майбутньому (години від завтрашнього дня)."""

    def make(start_hour: int, end_hour: int) -> dict:
        base = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            minute=0, second=0, microsecond=0
        )
        day = base.replace(hour=0)
        return {
            "starts_at": (day + timedelta(hours=start_hour)).isoformat(),
            "ends_at": (day + timedelta(hours=end_hour)).isoformat(),
        }

    return make
