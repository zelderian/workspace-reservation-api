from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.resource import Location, Resource
from app.models.user import User
from app.schemas.resource import (
    LocationCreate,
    LocationOut,
    ResourceCreate,
    ResourceOut,
)

router = APIRouter(tags=["resources"])


@router.get("/locations", response_model=list[LocationOut])
def list_locations(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Location).order_by(Location.id)).all()


@router.post("/locations", response_model=LocationOut, status_code=201)
def create_location(
    data: LocationCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    location = Location(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/resources", response_model=list[ResourceOut])
def list_resources(
    location_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Resource).order_by(Resource.id)
    if location_id is not None:
        query = query.where(Resource.location_id == location_id)
    return db.scalars(query).all()


@router.post("/resources", response_model=ResourceOut, status_code=201)
def create_resource(
    data: ResourceCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.get(Location, data.location_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Локацію не знайдено"
        )
    resource = Resource(**data.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource
