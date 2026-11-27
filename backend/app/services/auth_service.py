from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password

class AuthService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def seed_default_users(db: Session) -> None:
        """Seeds default accounts for Administrator, Assessor, and Researcher personas."""
        defaults = [
            ("admin@neuroscreen.ai", "Admin@12345", "System Administrator", "Administrator"),
            ("assessor@neuroscreen.ai", "Assessor@12345", "Clinical Screening Specialist", "Assessor"),
            ("researcher@neuroscreen.ai", "Researcher@12345", "Neurodevelopmental Researcher", "Researcher")
        ]

        for email, pwd, name, role in defaults:
            existing = AuthService.get_by_email(db, email)
            if not existing:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=role,
                    is_active=True
                )
                db.add(user)
        db.commit()

