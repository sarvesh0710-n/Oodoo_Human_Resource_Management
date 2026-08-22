import os
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas import LoginRequest, Token, UserRead
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

_env = os.getenv("DAYFLOW_ENV", "").lower()
_is_dev = (
    _env in ("dev", "development")
    or os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    or os.getenv("DEV", "").lower() in ("true", "1", "yes")
)
_cookie_secure = not _is_dev


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    # FIX 2: Set HttpOnly, SameSite=lax cookie server-side with raw token (no "Bearer " prefix)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure,
        max_age=86400,
        path="/",
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
    )


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
