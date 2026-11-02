from tests.conftest import PASSWORD


def test_register_creates_regular_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "New@Example.com", "full_name": "New", "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "user"
    assert "password" not in body and "hashed_password" not in body


def test_register_cannot_choose_admin_role(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "sneaky@example.com",
            "full_name": "Sneaky",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_register_duplicate_email_returns_409(client, user_a):
    response = client.post(
        "/auth/register",
        json={"email": "a@example.com", "full_name": "Dup", "password": PASSWORD},
    )
    assert response.status_code == 409


def test_register_validates_input(client):
    bad_email = client.post(
        "/auth/register",
        json={"email": "nope", "full_name": "X", "password": PASSWORD},
    )
    short_password = client.post(
        "/auth/register",
        json={"email": "x@example.com", "full_name": "X", "password": "123"},
    )
    assert bad_email.status_code == 422
    assert short_password.status_code == 422


def test_login_success_returns_token(client, user_a):
    response = client.post(
        "/auth/login", data={"username": "a@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password_returns_401(client, user_a):
    response = client.post(
        "/auth/login", data={"username": "a@example.com", "password": "wrong-pass"}
    )
    assert response.status_code == 401


def test_login_unknown_user_returns_401(client):
    response = client.post(
        "/auth/login", data={"username": "ghost@example.com", "password": PASSWORD}
    )
    assert response.status_code == 401


def test_me_with_valid_token_returns_200(client, headers_a):
    response = client.get("/users/me", headers=headers_a)
    assert response.status_code == 200
    assert response.json()["email"] == "a@example.com"


def test_invalid_token_returns_401(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
