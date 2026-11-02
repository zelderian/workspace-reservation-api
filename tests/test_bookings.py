def _book(client, headers, resource_id, interval):
    return client.post(
        "/bookings", json={"resource_id": resource_id, **interval}, headers=headers
    )


def test_user_can_book_free_slot(client, headers_a, resource_id, slot):
    response = _book(client, headers_a, resource_id, slot(10, 12))
    assert response.status_code == 201
    assert response.json()["status"] == "confirmed"


def test_overlapping_booking_returns_409(
    client, headers_a, headers_b, resource_id, slot
):
    assert _book(client, headers_a, resource_id, slot(10, 12)).status_code == 201
    response = _book(client, headers_b, resource_id, slot(11, 13))
    assert response.status_code == 409


def test_adjacent_booking_is_allowed(client, headers_a, headers_b, resource_id, slot):
    assert _book(client, headers_a, resource_id, slot(10, 12)).status_code == 201
    assert _book(client, headers_b, resource_id, slot(12, 14)).status_code == 201


def test_cancelled_slot_can_be_booked_again(
    client, headers_a, headers_b, resource_id, slot
):
    first = _book(client, headers_a, resource_id, slot(10, 12)).json()
    cancel = client.post(f"/bookings/{first['id']}/cancel", headers=headers_a)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert _book(client, headers_b, resource_id, slot(10, 12)).status_code == 201


def test_booking_in_the_past_returns_400(client, headers_a, resource_id):
    interval = {
        "starts_at": "2000-01-01T10:00:00+00:00",
        "ends_at": "2000-01-01T11:00:00+00:00",
    }
    assert _book(client, headers_a, resource_id, interval).status_code == 400


def test_end_before_start_returns_422(client, headers_a, resource_id, slot):
    interval = slot(12, 10)
    assert _book(client, headers_a, resource_id, interval).status_code == 422


def test_unknown_resource_returns_404(client, headers_a, slot):
    assert _book(client, headers_a, 9999, slot(10, 12)).status_code == 404


def test_idor_user_cannot_cancel_other_booking(
    client, headers_a, headers_b, resource_id, slot
):
    booking = _book(client, headers_a, resource_id, slot(10, 12)).json()
    response = client.post(f"/bookings/{booking['id']}/cancel", headers=headers_b)
    assert response.status_code == 403


def test_admin_can_cancel_any_booking(
    client, headers_a, headers_admin, resource_id, slot
):
    booking = _book(client, headers_a, resource_id, slot(10, 12)).json()
    response = client.post(f"/bookings/{booking['id']}/cancel", headers=headers_admin)
    assert response.status_code == 200


def test_my_bookings_returns_only_own(client, headers_a, headers_b, resource_id, slot):
    _book(client, headers_a, resource_id, slot(10, 12))
    _book(client, headers_b, resource_id, slot(14, 16))
    mine = client.get("/bookings/my", headers=headers_a).json()
    assert len(mine) == 1
    assert client.get("/bookings", headers=headers_a).status_code == 403
