# Pydantic schemas for authentication
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any
from enum import Enum
import re

class UserType(str, Enum):
    CLIENT = "client"
    BARBER = "barber"

class UserBuild(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # Proper email validation
    password: str = Field(..., min_length=8, max_length=128)
    user_type: UserType # "client" or "barber"

    @validator("username", "password")
    def validate_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @validator("username")
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @validator("password")
    def validate_password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    user_type: str
 
class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @validator("username", "password")
    def validate_fields(cls, v):
        if v and not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip() if v else v

    @validator("username")
    def validate_username(cls, v):
        if v:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @validator("password")
    def validate_password_complexity(cls, v):
        if v:
            if not re.search(r'[A-Z]', v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r'[a-z]', v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not re.search(r'\d', v):
                raise ValueError("Password must contain at least one number")
        return v

# Response schemas
class MessageResponse(BaseModel):
    message: str
 
class DataResponse(BaseModel):
    message: str
    data: Dict[str, Any]  # JSON-compatible dictionary    