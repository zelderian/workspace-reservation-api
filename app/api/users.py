from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Змінювати профіль може сам власник або адміністратор (захист від IDOR)."""
    if current.id != user_id and current.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Не можна змінювати чужий профіль",
        )
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    target.full_name = data.full_name
    db.commit()
    db.refresh(target)
    return target
