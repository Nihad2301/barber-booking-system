# Shop Pydantic schemas
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional
from app.services.schemas import ServiceResponse

class ShopRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    accepting_new_barbers: bool = True

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
        if not any([self.name, self.location, self.accepting_new_barbers is not None]):
            raise ValueError("At least one field must be provided")
        return self
