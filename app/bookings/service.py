# Booking business logic
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.bookings.models import Booking
from app.bookings.schemas import CreateBookingRequest, BookingResponse, CancelBookingResponse
from app.slots.models import Slot
from app.clients.models import Client
from app.barbers.models import Barber
from app.services.models import Service
from app.auth.exceptions import AlreadyClaimedError, ForbiddenError, NotFoundError
from app.auth.models import User

def create_booking(
    db: Session,
    slot_id: int,
    service_id: int,
    user_id: int,
    user_type: str
) -> BookingResponse:
    """
    Create a booking with concurrency-safe atomic UPDATE pattern.
    Uses a single conditional UPDATE to claim the slot, then inserts the booking.
    """
    try:
        # Atomic conditional UPDATE to claim the slot
        result = db.execute(
            update(Slot)
            .where(Slot.id == slot_id, Slot.status == 'open')
            .values(status='claimed')
        )
        
        # Check rowcount - if 0, slot was already claimed
        if result.rowcount == 0:
            db.rollback()
            raise AlreadyClaimedError("Slot already claimed")
        
        # Get slot details for the booking
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if not slot:
            db.rollback()
            raise NotFoundError("Slot not found")
        
        # Verify service exists and belongs to the shop
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.shop_id == slot.shop_id,
            Service.is_active == True
        ).first()
        if not service:
            db.rollback()
            raise NotFoundError("Service not found")
        
        # Get client ID from user
        if user_type != 'client':
            db.rollback()
            raise ForbiddenError("Only clients can create bookings")
        
        client = db.query(Client).filter(Client.user_id == user_id).first()
        if not client:
            db.rollback()
            raise NotFoundError("Client profile not found")
        
        # Create the booking
        booking = Booking(
            slot_id=slot_id,
            client_id=client.id,
            barber_id=slot.barber_id,
            shop_id=slot.shop_id,
            service_id=service_id,
            status='confirmed'
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        return BookingResponse(
            id=booking.id,
            slot_id=booking.slot_id,
            client_id=booking.client_id,
            barber_id=booking.barber_id,
            shop_id=booking.shop_id,
            service_id=booking.service_id,
            status=booking.status
        )
        
    except AlreadyClaimedError:
        raise  # Already rolled back, just propagate
    except Exception as e:
        db.rollback()
        raise e

def cancel_booking(
    db: Session,
    booking_id: int,
    user_id: int,
    user_type: str
) -> CancelBookingResponse:
    """
    Cancel a booking with concurrency-safe atomic UPDATE pattern.
    Authorization is checked first, then atomic conditional UPDATE on booking,
    followed by atomic conditional UPDATE to release the slot.
    """
    # Get the booking first for authorization check
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundError("Booking not found")
    
    # Authorization check
    if user_type == 'client':
        client = db.query(Client).filter(Client.user_id == user_id).first()
        if not client or booking.client_id != client.id:
            raise ForbiddenError("You can only cancel your own bookings")
    elif user_type == 'barber':
        barber = db.query(Barber).filter(Barber.user_id == user_id).first()
        if not barber or booking.barber_id != barber.id:
            raise ForbiddenError("You can only cancel your own bookings")
    else:
        raise ForbiddenError("Invalid user type")
    
    # Determine new status based on role
    new_status = 'cancelled_by_client' if user_type == 'client' else 'cancelled_by_barber'
    
    try:
        # Atomic conditional UPDATE on booking
        result = db.execute(
            update(Booking)
            .where(Booking.id == booking_id, Booking.status == 'confirmed')
            .values(status=new_status)
        )
        
        # If rowcount == 0, booking was already cancelled/completed - benign race
        if result.rowcount == 0:
            # Get current status for response
            db.refresh(booking)
            return CancelBookingResponse(
                message="Booking was already cancelled or completed",
                booking_status=booking.status
            )
        
        # Atomic conditional UPDATE to release the slot back to open
        slot_result = db.execute(
            update(Slot)
            .where(Slot.id == booking.slot_id, Slot.status == 'claimed')
            .values(status='open')
        )
        
        # If slot rowcount == 0, slot was already changed for legitimate reason - benign
        slot_status = 'open' if slot_result.rowcount == 1 else None
        
        db.commit()
        
        return CancelBookingResponse(
            message="Booking cancelled successfully",
            booking_status=new_status,
            slot_status=slot_status
        )
        
    except AlreadyClaimedError:
        raise
    except Exception as e:
        db.rollback()
        raise e
