from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False
)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT Bearer token and returns the authenticated User.
    Raises HTTP 401 without exposing internal system details if token is invalid or expired.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload["sub"]
    user = AuthService.get_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account is inactive or not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns authenticated user if a valid token is provided, otherwise None.
    Does not raise 401 when unauthenticated.
    """
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            return None
        return AuthService.get_by_email(db, payload["sub"])
    except Exception:
        return None

def require_roles(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces minimum necessary access for Administrator, Researcher, and Assessor roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient privileges. Required role in {allowed_roles}."
            )
        return current_user

    return role_checker
