"""Створення адміністратора з командного рядка.

Запуск з кореня проєкту:
    python -m scripts.create_admin admin@example.com StrongPass123 "Admin Name"
"""

import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    if len(sys.argv) < 3:
        print("Використання: python -m scripts.create_admin EMAIL PASSWORD [ІМ'Я]")
        raise SystemExit(1)
    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Administrator"

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            print(f"Користувач {email} вже існує")
            raise SystemExit(1)
        db.add(
            User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
            )
        )
        db.commit()
    print(f"Адміністратора {email} створено")


if __name__ == "__main__":
    main()
