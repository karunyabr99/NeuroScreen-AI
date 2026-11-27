from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: str = Field(..., description="Registered clinical or research email")
    password: str = Field(..., min_length=6, description="Password")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str
    full_name: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = Field("Assessor", description="'Administrator', 'Researcher', or 'Assessor'")

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

