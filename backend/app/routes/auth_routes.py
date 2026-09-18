from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.batch_models import ActivityLog
from app.utils.auth_utils import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_approved: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending admin approval")

    token = create_access_token(user.email, user.role)
    db.add(ActivityLog(user_id=user.id, action="login", detail=f"User {user.email} logged in"))
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=email,
        full_name=payload.full_name or email.split("@")[0],
        hashed_password=hash_password(payload.password),
        role="user",
        is_approved=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.add(
        ActivityLog(
            user_id=admin.id,
            action="approve_user",
            detail=f"Approved {user.email}",
        )
    )
    db.commit()
    db.refresh(user)
    return user
