# Shop Pydantic schemas
from pydantic import BaseModel, Field
from typing import List
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
    services: List[ServiceResponse] = []

    class Config:
        from_attributes = True