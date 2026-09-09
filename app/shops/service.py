# Shop business logic
from sqlalchemy.orm import joinedload
from .models import Shop
from app.barbers.models import Barber
from sqlalchemy.orm import Session
from app.auth.exceptions import NotFoundError, AlreadyExistsError, ForbiddenError

def _shop_to_response(shop: Shop) -> dict:
    return {
        "id": shop.id,
        "name": shop.name,
        "location": shop.location,
        "accepting_new_barbers": shop.accepting_new_barbers,
        "barber_count": len(shop.barbers),
        "services": shop.services
    }

def _verify_shop_ownership(db: Session, user_id: int, shop_id: int) -> Barber:
    barber = db.query(Barber).filter(Barber.user_id == user_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    if not barber.is_owner or barber.shop_id != shop_id:
        raise ForbiddenError("You are not the owner of this shop")
    return barber
    
def get_available_shops(db: Session):
    shops = db.query(Shop).options(
        joinedload(Shop.barbers),
        joinedload(Shop.services)
    ).filter(Shop.accepting_new_barbers == True).all()
    if not shops:
        raise NotFoundError("No shops found")

    return [
        _shop_to_response(shop)
        for shop in shops
    ]

def get_shop_by_id(db: Session, shop_id: int):
    shop = db.query(Shop).options(
        joinedload(Shop.barbers),
        joinedload(Shop.services)
    ).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    return _shop_to_response(shop)

def create_shop(db: Session, shop_data: dict, user_id: int):
    existing_shop = db.query(Shop).filter(
        Shop.name == shop_data["name"],
        Shop.location == shop_data["location"]
        ).first()
    if existing_shop:
        raise AlreadyExistsError("Shop already exists")

    shop = Shop(**shop_data)
    db.add(shop)
    db.commit()
    db.refresh(shop)

    # Create barber as owner of the new shop
    barber = Barber(
        name=shop_data.get("name", "Shop Owner"),
        shop_id=shop.id,
        is_owner=True,
        slot_duration=30,
        user_id=user_id
    )
    db.add(barber)
    db.commit()

    db.refresh(shop, options=[joinedload(Shop.barbers), joinedload(Shop.services)])
    return _shop_to_response(shop)
    
def update_shop(db: Session, shop_id: int, user_id, shop_data: dict):
    shop = db.query(Shop).options(
        joinedload(Shop.barbers),
        joinedload(Shop.services)
    ).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    _verify_shop_ownership(db, user_id, shop_id)
    
    for key, value in shop_data.items():
        setattr(shop, key, value)
    
    db.commit()
    db.refresh(shop)
    return _shop_to_response(shop)

def delete_shop(db: Session, user_id: int, shop_id: int):
    shop = db.query(Shop).options(
        joinedload(Shop.slots),
        joinedload(Shop.bookings)
    ).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    _verify_shop_ownership(db, user_id, shop_id)
        
    shop.is_active = False
    for slot in shop.slots:
        if slot.status in ["open", "claimed"]:
            slot.status = "shop_closed"
    for booking in shop.bookings:
        if booking.status == "confirmed":
            booking.status = "shop_closed"
    db.commit()
