# Shop business logic
from sqlalchemy.orm import joinedload
from .models import Shop
from sqlalchemy.orm import Session
from app.auth.exceptions import NotFoundError, AlreadyExistsError

def get_available_shops(db: Session):
    shops = db.query(Shop).options(
        joinedload(Shop.barbers),
        joinedload(Shop.services)
    ).filter(Shop.accepting_new_barbers == True).all()
    if not shops:
        raise NotFoundError("No shops found")

    return [
        {
            "id": shop.id,
            "name": shop.name,
            "location": shop.location,
            "barber_count": len(shop.barbers),
            "services": shop.services
        }
        for shop in shops
    ]

def create_shop(db: Session, shop_data: dict):
    existing_shop = db.query(Shop).filter(
        Shop.name == shop_data["name"], 
        Shop.location == shop_data["location"]
        ).first()
    if existing_shop:
        raise AlreadyExistsError("Shop already exists")

    shop = Shop(**shop_data)
    db.add(shop)
    db.commit()
    db.refresh(shop, options=[joinedload(Shop.barbers), joinedload(Shop.services)])
    return {
        **shop.__dict__, 
        "barber_count": len(shop.barbers), 
        "services": shop.services
    }