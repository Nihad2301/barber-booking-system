# Booking endpoints
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user, require_verified_email
from app.bookings.service import create_booking, cancel_booking, list_bookings
from app.bookings.schemas import CreateBookingRequest, BookingResponse, CancelBookingResponse, BookingListResponse
from app.auth.schemas import DataResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=DataResponse[BookingResponse])
def create_booking_endpoint(
    request: CreateBookingRequest,
    current_user: dict = Depends(require_verified_email),
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
    current_user: dict = Depends(require_verified_email),
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

@router.get("", response_model=DataResponse[BookingListResponse])
def list_bookings_endpoint(
    include_cancelled: bool = Query(False, description="Include cancelled bookings (barber only)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List bookings with role-based branching behavior.
    
    Client branch:
    - Returns only bookings belonging to this client
    - ALWAYS excludes cancelled bookings (fixed behavior, not configurable)
    
    Barber branch:
    - Regular barber sees only their own bookings
    - Owner-flagged barber sees ALL bookings across their shop
    - Accepts optional include_cancelled parameter (default False)
    """
    user_id = current_user.get("user_id")
    user_type = current_user.get("user_type")
    
    # For client branch, ignore include_cancelled parameter entirely
    if user_type == 'client':
        include_cancelled = False
    
    bookings = list_bookings(
        db=db,
        user_id=user_id,
        user_type=user_type,
        include_cancelled=include_cancelled
    )
    
    return DataResponse(data=bookings, message="Bookings retrieved successfully")
