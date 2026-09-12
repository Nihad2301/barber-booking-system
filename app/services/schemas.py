# Service Pydantic schemas
from pydantic import BaseModel, field_validator, model_validator, Field
from typing import Optional

class ServiceRequest(BaseModel):
    name: str
    price: int
    is_active: bool = True

class ServiceResponse(BaseModel):
    id: int
    name: str
    price: int
    is_active: bool

    class Config:
        from_attributes = True

class ServiceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

    @field_validator('name')
    def check_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty if provided")
        return v.strip() if v else v
    
    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if all(
            [
                self.name is None,
                self.price is None,
                self.is_active is None,
            ]
        ):
            raise ValueError("At least one field must be provided for update")
        return self


