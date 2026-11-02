from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import auth, bookings, pages, resources, users
from app.db.session import get_db

app = FastAPI(title="Workspace Reservation API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pages.router)
app.include_router(resources.router)
app.include_router(bookings.router)


@app.get("/")
def root():
    return {"service": "Workspace Reservation API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "ok"}
