import pytest


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/user/home"),
        ("get", "/admin/home"),
        ("get", "/users/me"),
        ("get", "/users"),
        ("get", "/locations"),
        ("get", "/resources"),
        ("get", "/bookings/my"),
        ("get", "/bookings"),
    ],
)
def test_anonymous_gets_401_on_protected_routes(client, method, url):
    response = getattr(client, method)(url)
    assert response.status_code == 401


def test_user_home_available_for_user(client, headers_a):
    response = client.get("/user/home", headers=headers_a)
    assert response.status_code == 200
    assert response.json()["page"] == "user_home"


def test_admin_home_available_for_admin(client, headers_admin):
    response = client.get("/admin/home", headers=headers_admin)
    assert response.status_code == 200
    assert response.json()["page"] == "admin_home"


@pytest.mark.parametrize(
    "method,url",
    [("get", "/admin/home"), ("get", "/users"), ("get", "/bookings")],
)
def test_regular_user_gets_403_on_admin_routes(client, headers_a, method, url):
    response = getattr(client, method)(url, headers=headers_a)
    assert response.status_code == 403


def test_regular_user_cannot_create_location(client, headers_a):
    response = client.post(
        "/locations",
        json={"name": "X", "city": "Y", "address": "Z"},
        headers=headers_a,
    )
    assert response.status_code == 403


def test_regular_user_cannot_create_resource(client, headers_a):
    response = client.post(
        "/resources",
        json={
            "location_id": 1,
            "name": "R",
            "type": "desk",
            "capacity": 1,
            "price_per_hour": "1.00",
        },
        headers=headers_a,
    )
    assert response.status_code == 403


def test_idor_user_cannot_update_other_profile(client, headers_a, user_b):
    response = client.patch(
        f"/users/{user_b.id}", json={"full_name": "Hacked"}, headers=headers_a
    )
    assert response.status_code == 403


def test_user_can_update_own_profile(client, headers_a, user_a):
    response = client.patch(
        f"/users/{user_a.id}", json={"full_name": "Renamed"}, headers=headers_a
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Renamed"


def test_admin_can_update_any_profile(client, headers_admin, user_b):
    response = client.patch(
        f"/users/{user_b.id}", json={"full_name": "ByAdmin"}, headers=headers_admin
    )
    assert response.status_code == 200


def test_web_pages_are_served(client):
    for page in ("/", "/login.html", "/dashboard.html", "/admin.html"):
        response = client.get(page)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    assert client.get("/info").json()["env"] == "sandbox"
