from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut
from app.services import booking as booking_service
from app.services.booking import BookingError

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(
    data: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return booking_service.create_booking(
            db, user, data.resource_id, data.starts_at, data.ends_at
        )
    except BookingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/my", response_model=list[BookingOut])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Booking).where(Booking.user_id == user.id).order_by(Booking.id)
    return db.scalars(query).all()


@router.get("", response_model=list[BookingOut])
def all_bookings(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(Booking).order_by(Booking.id)).all()


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return booking_service.cancel_booking(db, user, booking_id)
    except BookingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
