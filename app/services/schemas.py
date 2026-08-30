# Service Pydantic schemas
from pydantic import BaseModel

class ServiceResponse(BaseModel):
    id: int
    name: str
    price: int

    class Config:
        from_attributes = True
