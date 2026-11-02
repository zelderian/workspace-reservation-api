from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.resource import Resource
from app.models.user import User, UserRole, utcnow


class BookingError(Exception):
    """Помилка бізнес-логіки бронювання."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def create_booking(
    db: Session, user: User, resource_id: int, starts_at: datetime, ends_at: datetime
) -> Booking:
    if starts_at < utcnow():
        raise BookingError(400, "Не можна бронювати час у минулому")

    # Блокуємо рядок ресурсу до кінця транзакції: два одночасні запити
    # на той самий ресурс виконуються по черзі (захист від race condition).
    resource = db.scalar(
        select(Resource).where(Resource.id == resource_id).with_for_update()
    )
    if resource is None:
        raise BookingError(404, "Ресурс не знайдено")

    overlap = db.scalar(
        select(Booking.id).where(
            Booking.resource_id == resource_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
    )
    if overlap is not None:
        db.rollback()
        raise BookingError(409, "Цей час уже зайнято")

    booking = Booking(
        user_id=user.id,
        resource_id=resource_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, user: User, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise BookingError(404, "Бронювання не знайдено")
    if booking.user_id != user.id and user.role != UserRole.ADMIN:
        raise BookingError(403, "Не можна скасувати чуже бронювання")
    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking
