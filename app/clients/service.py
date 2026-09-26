# Client business logic
from .models import Client
from app.auth.service import _build_user
from app.auth.exceptions import NotFoundError, ForbiddenError
from app.bookings.service import cancel_booking
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.slots.models import Slot

def _client_to_response(client: Client):
    return {
        "id": client.id,
        "name": client.name
    }

def register_client(
    db: Session,
    username: str,
    password: str,
    email: str,
    name: str
):
    """Register a new client - no JWT or email verification required"""
    try:
        # Create user
        user = _build_user(db, username, password, email, "client")
        
        # Create client
        new_client = Client(
            user_id=user.id,
            name=name,
            is_active=True
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return _client_to_response(new_client)
    except Exception as e:
        db.rollback()
        raise e

def get_client(db: Session, client_id: int, requesting_user_id: int, requesting_user_type: str):
    """
    Get client profile with role-based access control:
    - Client can always view their own profile
    - Barber can view client profile only if there exists at least one confirmed/completed booking between them
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise NotFoundError("Client not found")
    
    # Check authorization
    if requesting_user_type == "client":
        # Client can view their own profile
        requesting_client = db.query(Client).filter(Client.user_id == requesting_user_id).first()
        if requesting_client.id != client_id:
            raise ForbiddenError("You can only view your own profile")
    elif requesting_user_type == "barber":
        # Barber can view client profile only if they have a confirmed/completed booking together
        from app.barbers.models import Barber
        barber = db.query(Barber).filter(Barber.user_id == requesting_user_id).first()
        if not barber:
            raise ForbiddenError("Barber profile not found")
        
        # Check for confirmed or completed booking between this barber and client
        from app.bookings.models import Booking
        has_booking = db.query(Booking).filter(
            and_(
                Booking.barber_id == barber.id,
                Booking.client_id == client_id,
                Booking.status.in_(['confirmed', 'completed'])
            )
        ).first()
        
        if not has_booking:
            raise ForbiddenError("You can only view clients you have a confirmed or completed booking with")
    else:
        raise ForbiddenError("Invalid user type")
    
    return _client_to_response(client)

def update_client(db: Session, client_id: int, user_id: int, client_data: dict):
    """Update client profile - client-only, requires verified email (enforced at route level)"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == user_id
    ).first()
    if not client:
        raise ForbiddenError("You can only update your own profile")
    
    # Update fields (is_active is NOT allowed here - has dedicated delete flow)
    for key, value in client_data.items():
        if key == "is_active":
            continue  # Skip is_active - not allowed via update endpoint
        if value is not None:
            setattr(client, key, value)
    
    db.commit()
    db.refresh(client)
    return _client_to_response(client)

def delete_client(db: Session, client_id: int, user_id: int):
    """
    Deactivate client account - client-only, requires verified email (enforced at route level)
    1. Set client.is_active = False
    2. Cancel all future confirmed bookings using existing cancel_booking function
    3. Past/completed bookings remain as history
    """
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == user_id
    ).first()
    if not client:
        raise ForbiddenError("You can only delete your own profile")
    
    try:
        # Deactivate client
        client.is_active = False
        
        # Find all future confirmed bookings for this client
        from app.bookings.models import Booking
        future_bookings = db.query(Booking).join(Slot).filter(
            and_(
                Booking.client_id == client.id,
                Booking.status == 'confirmed',
                Slot.start_time > datetime.utcnow()
            )
        ).all()
        
        # Cancel each future booking using the existing cancel_booking function
        # This reuses the already-tested atomic cancellation logic
        for booking in future_bookings:
            cancel_booking(db, booking.id, user_id, "client")
        
        db.commit()
        return {"message": "Client account deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise e
