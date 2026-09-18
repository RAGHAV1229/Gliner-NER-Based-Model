from __future__ import annotations

from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401
from app import batch_models  # noqa: F401
from app.models import User
from app.utils.auth_utils import hash_password


def upsert_user(db, email: str, password: str, role: str, full_name: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
    user.full_name = full_name
    user.hashed_password = hash_password(password)
    user.role = role
    user.is_approved = True
    user.is_active = True
    return user


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        upsert_user(db, "admin@test.com", "Admin@123", "admin", "Platform Admin")
        upsert_user(db, "user@test.com", "User@123", "user", "Demo User")
        db.commit()
        print("Users ready:")
        print("  admin@test.com / Admin@123")
        print("  user@test.com / User@123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
