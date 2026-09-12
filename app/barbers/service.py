# Barber business logic
from .models import Barber
from app.shops.models import Shop
from sqlalchemy.orm import Session, joinedload
from app.auth.service import _build_user
from app.auth.exceptions import NotFoundError, ForbiddenError

def _verify_ownership(barber_owner_id: int, shop_id: int, db: Session):
    barber_owner = db.query(Barber).options(
        Barber.shop
    ).filter(
        Barber.user_id == barber_owner_id, 
        Barber.shop_id == shop_id, 
        Barber.is_owner == True
    ).first()

    if not barber_owner.shop:
        raise NotFoundError("Shop not found")
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
    shop = db.query(Shop).options(Shop.barbers).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    return [_barber_to_response(barber) for barber in shop.barbers]

def show_barber(db: Session, barber_id: int, shop_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    barber = db.query(Barber).filter(Barber.id == barber_id, Barber.shop_id == shop_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    return _barber_to_response(barber)

def update_self_barber(db: Session, user_id: int, barber_id: int, shop_id: int, self_barber_data: dict):
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

def update_owner_barber(
    db: Session, 
    user_id: int, 
    barber_id: int, 
    shop_id: int, 
    barber_data: dict
):  
    # Verify ownership
    _verify_ownership(user_id, shop_id, db)

    # Find barber to update
    barber_to_update = db.query(Barber).filter(
        Barber.id == barber_id, 
        Barber.shop_id == shop_id
        ).first()
    if not barber_to_update:
        raise NotFoundError("Barber not found")
    
    # Update barber fields
    for key, value in barber_data.items():
        if value is not None:
            setattr(barber_to_update, key, value)

    db.commit()
    db.refresh(barber_to_update)
    return _barber_to_response(barber_to_update)

def delete_self_barber(db: Session, user_id: int, barber_id: int, shop_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    barber = db.query(Barber).options(
        joinedload(Barber.slots),
        joinedload(Barber.bookings)
    ).filter(
        Barber.id == barber_id, 
        Barber.shop_id == shop_id, 
        Barber.user_id == user_id
        ).first()
    if not barber:
        raise ForbiddenError("You can only delete your own profile")
    
    barber.is_active = False
    for slot in barber.slots:
        if slot.status in ["open", "claimed"]:
            slot.status = "barber_left"
    for booking in barber.bookings:
        if booking.status == "confirmed":
            booking.status = "barber_left"
    
    db.commit()
    return {"message": "Barber deleted successfully"}

def delete_owner_barber(db: Session, user_id: int, barber_id: int, shop_id: int):
    # Verify ownership
    _verify_ownership(user_id, shop_id, db)
    
    # Find barber to delete
    barber_to_delete = db.query(Barber).options(
        joinedload(Barber.slots),
        joinedload(Barber.bookings)
    ).filter(
        Barber.id == barber_id, 
        Barber.shop_id == shop_id
        ).first()
    if not barber_to_delete:
        raise NotFoundError("Barber not found")
    
    # Delete barber
    barber_to_delete.is_active = False
    for slot in barber_to_delete.slots:
        if slot.status in ["open", "claimed"]:
            slot.status = "barber_left"
    for booking in barber_to_delete.bookings:
        if booking.status == "confirmed":
            booking.status = "barber_left"
    
    db.commit()
    return {"message": "Barber deleted successfully"}