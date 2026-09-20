# Booking endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.bookings.service import create_booking, cancel_booking
from app.bookings.schemas import CreateBookingRequest, BookingResponse, CancelBookingResponse
from app.auth.schemas import DataResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=DataResponse[BookingResponse])
def create_booking_endpoint(
    request: CreateBookingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new booking.
    Uses atomic conditional UPDATE for concurrency safety.
    """
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    booking = create_booking(
        db=db,
        slot_id=request.slot_id,
        service_id=request.service_id,
        user_id=user_id,
        user_type=user_type
    )
    
    return DataResponse(data=booking, message="Booking created successfully")

@router.patch("/{booking_id}/cancel", response_model=DataResponse[CancelBookingResponse])
def cancel_booking_endpoint(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a booking.
    Authorization is checked first, then atomic conditional UPDATE for concurrency safety.
    """
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    result = cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=user_id,
        user_type=user_type
    )
    
    return DataResponse(data=result, message="Booking cancelled successfully")
