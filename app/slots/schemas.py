# Slot Pydantic schemas
from pydantic import BaseModel
from datetime import datetime

class SlotResponse(BaseModel):
    id: int
    barber_id: int
    shop_id: int
    start_time: datetime
    end_time: datetime
    status: str
    
    class Config:
        from_attributes = True
