import random
import uuid
from datetime import datetime, timedelta, timezone

from locust import HttpUser, between, task

PASSWORD = "LoadTest12345"


def random_slot() -> dict:
    day = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=random.randint(1, 365))
    start = day + timedelta(hours=random.randint(8, 20))
    end = start + timedelta(hours=random.choice([1, 2]))
    return {"starts_at": start.isoformat(), "ends_at": end.isoformat()}


class CoworkingClient(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.email = f"lt_{uuid.uuid4().hex[:12]}@example.com"
        self.client.post(
            "/auth/register",
            json={"email": self.email, "full_name": "Load Test", "password": PASSWORD},
            name="POST /auth/register",
        )
        response = self.client.post(
            "/auth/login",
            data={"username": self.email, "password": PASSWORD},
            name="POST /auth/login",
        )
        token = response.json().get("access_token") if response.ok else None
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.resource_ids: list[int] = []
        self.my_bookings: list[int] = []

    @task(5)
    def list_resources(self) -> None:
        response = self.client.get("/resources", name="GET /resources")
        if response.ok:
            self.resource_ids = [r["id"] for r in response.json()]

    @task(3)
    def list_locations(self) -> None:
        self.client.get("/locations", name="GET /locations")

    @task(2)
    def profile(self) -> None:
        self.client.get("/users/me", name="GET /users/me")

    @task(3)
    def my_bookings_list(self) -> None:
        self.client.get("/bookings/my", name="GET /bookings/my")

    @task(2)
    def create_booking(self) -> None:
        if not self.resource_ids:
            return
        payload = {"resource_id": random.choice(self.resource_ids), **random_slot()}
        with self.client.post(
            "/bookings", json=payload, name="POST /bookings", catch_response=True
        ) as response:
            if response.status_code == 201:
                self.my_bookings.append(response.json()["id"])
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def cancel_booking(self) -> None:
        if self.my_bookings:
            booking_id = self.my_bookings.pop()
            self.client.post(
                f"/bookings/{booking_id}/cancel", name="POST /bookings/{id}/cancel"
            )
