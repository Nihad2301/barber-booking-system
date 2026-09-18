# Shop Pydantic schemas
from pydantic import BaseModel, Field, model_validator, field_validator, EmailStr
from typing import List, Optional
from app.services.schemas import ServiceResponse
from app.auth.schemas import UserType
import re

class ShopRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    accepting_new_barbers: bool = True

    @field_validator("username", "password")
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

class ShopResponse(BaseModel):
    id: int
    name: str
    location: str
    barber_count: int
    accepting_new_barbers: bool
    services: List[ServiceResponse] = []

    class Config:
        from_attributes = True

class ShopUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    accepting_new_barbers: Optional[bool] = None

    @field_validator('name', 'location')
    @classmethod
    def validate_string_fields(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty if provided")
        return v.strip() if v else v

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if all(
            [
                self.name is None,
                self.location is None,
                self.accepting_new_barbers is None,
            ]
        ):
            raise ValueError("At least one field must be provided")
        return self
