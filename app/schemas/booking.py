from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.booking import BookingStatus


def to_naive_utc(value: datetime) -> datetime:
    """Приводить час до UTC без tzinfo; час без пояса вважається UTC."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


class BookingCreate(BaseModel):
    resource_id: int
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def normalize_time(cls, value: datetime) -> datetime:
        return to_naive_utc(value)

    @model_validator(mode="after")
    def check_interval(self) -> "BookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at має бути пізніше за starts_at")
        return self


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    resource_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    created_at: datetime
