from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Location, Resource

LOCATION_NAME = "LoadTest Hub"
RESOURCES = 20


def main() -> None:
    if settings.is_production:
        raise SystemExit("Seed для навантажувального тесту заборонено у production")
    with SessionLocal() as db:
        location = db.scalar(select(Location).where(Location.name == LOCATION_NAME))
        if location is None:
            location = Location(name=LOCATION_NAME, city="Kyiv", address="Test st 1")
            db.add(location)
            db.flush()
        existing = db.scalars(
            select(Resource).where(Resource.location_id == location.id)
        ).all()
        for i in range(len(existing), RESOURCES):
            db.add(
                Resource(
                    location_id=location.id,
                    name=f"Room {i + 1}",
                    type="meeting_room" if i % 2 else "desk",
                    capacity=4 + i % 8,
                    price_per_hour=Decimal("10.00") + i,
                )
            )
        db.commit()
        print(f"Локація id={location.id}, ресурсів: {RESOURCES}")


if __name__ == "__main__":
    main()
