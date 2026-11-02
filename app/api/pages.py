from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_admin
from app.models.user import User

router = APIRouter(tags=["pages"])


@router.get("/user/home")
def user_home(user: User = Depends(get_current_user)):
    return {"page": "user_home", "message": f"Вітаємо, {user.full_name}!"}


@router.get("/admin/home")
def admin_home(admin: User = Depends(require_admin)):
    return {"page": "admin_home", "message": f"Панель адміністратора: {admin.email}"}
