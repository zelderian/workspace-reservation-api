import asyncio

from fastapi import HTTPException, Request, status
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def create_db_slots() -> asyncio.Semaphore:
    return asyncio.Semaphore(settings.db_pool_capacity)


async def get_db(request: Request):
    slots: asyncio.Semaphore = request.app.state.db_slots
    try:
        await asyncio.wait_for(slots.acquire(), timeout=settings.db_pool_timeout)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервер перевантажений, спробуйте пізніше",
            headers={"Retry-After": "5"},
        ) from None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        slots.release()
