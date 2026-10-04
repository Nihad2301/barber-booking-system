# Barber business logic
from .models import Barber
from app.shops.models import Shop
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.auth.service import _build_user
from app.auth.exceptions import NotFoundError, ForbiddenError
from app.bookings.service import cancel_booking
from app.bookings.models import Booking

def _verify_ownership(barber_owner_id: int, shop_id: int, db: Session):
    barber_owner = db.query(Barber).filter(
        Barber.user_id == barber_owner_id,
        Barber.shop_id == shop_id,
        Barber.is_owner == True
    ).first()

    if not barber_owner:
        raise ForbiddenError("You are not the owner of this shop")
    return barber_owner

def _barber_to_response(barber: Barber):
    return {
        "id": barber.id,
        "shop_id": barber.shop_id,
        "name": barber.name,
        "slot_duration": barber.slot_duration
    }

def register_barber(
    db: Session,
    barber_owner_id: int,
    shop_id: int,
    username: str, 
    password: str, 
    email: str, 
    name: str, 
    slot_duration: int = 30
):
    try:
        barber_owner = _verify_ownership(barber_owner_id, shop_id, db)
        # Create user
        user = _build_user(db, username, password, email, "barber")       
        # Create barber
        new_barber = Barber(
            user_id=user.id, 
            name=name, 
            slot_duration=slot_duration, 
            is_active=True
        )
        new_barber.shop = barber_owner.shop
        db.add(new_barber)
        db.commit()
        db.refresh(new_barber)
        return _barber_to_response(new_barber)
    except Exception as e:
        db.rollback()
        raise e

def show_barbers(db: Session, shop_id: int):
    shop = db.query(Shop).options(joinedload(Shop.barbers)).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    return [_barber_to_response(barber) for barber in shop.barbers if barber.is_active]

def show_barber(db: Session, barber_id: int, shop_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")

    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.shop_id == shop_id,
        Barber.is_active == True
    ).first()
    if not barber:
        raise NotFoundError("Barber not found")

    return _barber_to_response(barber)

def update_self_barber(db: Session, user_id: int, barber_id: int, shop_id: int, self_barber_data: dict):
    try:
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise NotFoundError("Shop not found")

        barber = db.query(Barber).filter(
            Barber.id == barber_id,
            Barber.shop_id == shop_id,
            Barber.user_id == user_id
            ).first()
        if not barber:
            raise ForbiddenError("You can only update your own profile")

        for key, value in self_barber_data.items():
            if value is not None:
                setattr(barber, key, value)

        db.commit()
        db.refresh(barber)
        return _barber_to_response(barber)
    except Exception as e:
        db.rollback()
        raise e

def update_owner_barber(
    db: Session,
    user_id: int,
    barber_id: int,
    shop_id: int,
    barber_data: dict
):
    try:
        # Verify ownership
        _verify_ownership(user_id, shop_id, db)

        # Find barber to update
        barber_to_update = db.query(Barber).filter(
            Barber.id == barber_id,
            Barber.shop_id == shop_id
            ).first()
        if not barber_to_update:
            raise NotFoundError("Barber not found")

        # MVP limitation: Owner cannot deactivate themselves or remove ownership to prevent shop freeze
        if barber_to_update.is_owner and barber_data.get('is_active') == False:
            raise ForbiddenError("Owner cannot deactivate themselves. "
            "This is an MVP limitation to ensure the shop remains manageable.")
        if barber_to_update.is_owner and barber_data.get('is_owner') == False:
            raise ForbiddenError("Owner cannot remove their own ownership status. "
            "This is an MVP limitation to ensure the shop remains manageable.")

        # Update barber fields
        for key, value in barber_data.items():
            if value is not None:
                setattr(barber_to_update, key, value)

        db.commit()
        db.refresh(barber_to_update)
        return _barber_to_response(barber_to_update)
    except Exception as e:
        db.rollback()
        raise e

def delete_self_barber(db: Session, user_id: int, barber_id: int, shop_id: int):
    """
    Deactivate barber account - barber-only self-service
    - If barber is owner: triggers shop closure cascade (all barbers deactivated, slots='shop_closed')
    - If barber is regular: deactivates only this barber, cancels future bookings with 'cancelled_by_barber', slots='barber_left'
    - Past/completed bookings remain as history
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")

    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.shop_id == shop_id,
        Barber.user_id == user_id
    ).first()
    if not barber:
        raise ForbiddenError("You can only delete your own profile")

    # If barber is owner, trigger shop closure cascade
    if barber.is_owner:
        from app.shops.service import delete_shop
        return delete_shop(db, user_id, shop_id)

    # Regular barber deactivation
    try:
        barber.is_active = False

        # Find all confirmed bookings for this barber
        future_bookings = db.query(Booking).filter(
            and_(
                Booking.barber_id == barber.id,
                Booking.status == 'confirmed'
            )
        ).all()

        # Cancel each booking and release slot with 'barber_left' status
        for booking in future_bookings:
            cancel_booking(db, booking.id, user_id, 'barber', target_slot_status='barber_left')

        db.commit()
        return {"message": "Barber account deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise e

def delete_owner_barber(db: Session, user_id: int, barber_id: int, shop_id: int):
    """
    Deactivate barber - owner-only
    - Deactivates the specified barber
    - Cancels future confirmed bookings with 'cancelled_by_barber'
    - Releases slots with 'barber_left' status
    - Does NOT trigger shop closure (use delete_shop for that)
    """
    # Verify ownership
    _verify_ownership(user_id, shop_id, db)

    # Find barber to delete
    barber_to_delete = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.shop_id == shop_id
    ).first()
    if not barber_to_delete:
        raise NotFoundError("Barber not found")

    try:
        barber_to_delete.is_active = False

        # Find all confirmed bookings for this barber
        future_bookings = db.query(Booking).filter(
            and_(
                Booking.barber_id == barber_to_delete.id,
                Booking.status == 'confirmed'
            )
        ).all()

        # Cancel each booking and release slot with 'barber_left' status
        for booking in future_bookings:
            cancel_booking(db, booking.id, user_id, 'barber', target_slot_status='barber_left')

        db.commit()
        return {"message": "Barber deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise e