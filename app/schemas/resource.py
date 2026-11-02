from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)


class LocationOut(LocationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ResourceCreate(BaseModel):
    location_id: int
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=50)
    capacity: int = Field(gt=0)
    price_per_hour: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class ResourceOut(ResourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
