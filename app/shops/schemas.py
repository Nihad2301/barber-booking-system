# Shop Pydantic schemas
from pydantic import BaseModel
from typing import List
from app.services.schemas import ServiceResponse

class ShopResponse(BaseModel):
    id: int
    name: str
    location: str
    barber_count: int
    services: List[ServiceResponse]

    class Config:
        from_attributes = True