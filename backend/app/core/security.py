import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt

from app.core.config import settings

def get_password_hash(password: str) -> str:
    """Secure bcrypt password hashing with salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode signed JWT token. Returns payload dict or None."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except (jwt.PyJWTError, Exception):
        return None

def generate_anonymized_id(prefix: str = "NS") -> str:
    """Generate research identifier using De-identified Research Identifier Scheme (e.g. NS-2026-A8F2)."""
    current_year = datetime.utcnow().year
    random_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{current_year}-{random_token}"

def calculate_payload_hash(payload_str: str) -> str:
    """Generate SHA-256 hash for screening audit trail verification."""
    return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
