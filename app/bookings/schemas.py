# Booking Pydantic schemas
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CreateBookingRequest(BaseModel):
    slot_id: int = Field(..., gt=0)
    service_id: int = Field(..., gt=0)

class BookingResponse(BaseModel):
    id: int
    slot_id: int
    client_id: int
    barber_id: int
    shop_id: int
    service_id: int
    status: str
    
    class Config:
        from_attributes = True

class CancelBookingResponse(BaseModel):
    booking_status: str
    slot_status: Optional[str] = None

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
