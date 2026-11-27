from typing import List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.schemas.auth import UserLogin, Token, UserResponse, UserCreate
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token, summary="Authenticate Clinician / Researcher / Admin")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning JWT bearer token."""
    user = AuthService.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )

@router.post("/token", response_model=Token, summary="OAuth2 Compatible Token Endpoint")
def oauth2_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Standard OAuth2 form-compatible login endpoint."""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )

@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User Profile")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserResponse], summary="List Registered Users (Administrator Only)")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(["Administrator"]))
):
    return db.query(User).all()

