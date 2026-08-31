# Barber Pydantic schemas
from pydantic import BaseModel

class BarberRegister(BaseModel):
    shop_id: int
    username: str
    password: str
    email: str
    name: str
    slot_duration: int = 30

class BarberResponse(BaseModel):
    id: int
    shop_id: int
    name: str
    slot_duration: int

    class Config:
        from_attributes = True        