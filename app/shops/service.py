# Shop business logic
from sqlalchemy.orm import joinedload
from .models import Shop
from sqlalchemy.orm import Session

def get_available_shops(db: Session):
    shops = db.query(Shop).options(
        joinedload(Shop.barbers),
        joinedload(Shop.services)
    ).filter(Shop.accepting_new_barbers == True).all()
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