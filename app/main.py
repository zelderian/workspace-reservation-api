import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import auth, bookings, pages, resources, users
from app.core.config import Settings, settings
from app.core.errors import register_exception_handlers
from app.db.session import create_db_slots, get_db

WEB_DIR = Path(__file__).parent / "web"


def configure_logging(config: Settings) -> None:
    logging.basicConfig(
        level=config.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app(config: Settings = settings) -> FastAPI:
    configure_logging(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db_slots = create_db_slots()
        yield

    application = FastAPI(
        lifespan=lifespan,
        title="Workspace Reservation API",
        debug=config.debug,
        docs_url="/docs" if config.docs_enabled else None,
        redoc_url="/redoc" if config.docs_enabled else None,
        openapi_url="/openapi.json" if config.docs_enabled else None,
    )
    register_exception_handlers(application)

    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(pages.router)
    application.include_router(resources.router)
    application.include_router(bookings.router)

    @application.get("/info")
    def info():
        return {"service": "Workspace Reservation API", "env": config.app_env.value}

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.get("/health/db")
    def health_db(db: Session = Depends(get_db)):
        db.execute(text("SELECT 1"))
        return {"database": "ok"}

    application.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

    return application


app = create_app()
