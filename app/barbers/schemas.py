# Barber Pydantic schemas
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class BarberRegister(BaseModel):
    shop_id: int
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    slot_duration: int = Field(default=30, gt=0)

    @field_validator("username", "password", "name")
    @classmethod
    def validate_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        return v

class BarberResponse(BaseModel):
    id: int
    shop_id: int
    name: str
    slot_duration: int

    class Config:
        from_attributes = True        