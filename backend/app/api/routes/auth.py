from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import clear_auth_cookie, create_access_token, hash_password, set_auth_cookie, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, MessageResponse, UserLoginRequest, UserRegistrationRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegistrationRequest, db: Session = Depends(get_db)) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    access_token = create_access_token(user.id)
    set_auth_cookie(response, access_token)
    return AuthResponse(message="Login successful.", user=UserResponse.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
def logout_user(response: Response) -> MessageResponse:
    clear_auth_cookie(response)
    return MessageResponse(message="Logout successful.")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
