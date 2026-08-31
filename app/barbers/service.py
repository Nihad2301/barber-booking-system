# Barber business logic
from .models import Barber
from app.shops.models import Shop
from sqlalchemy.orm import Session
from app.auth.service import _build_user

def register_barber(
    db: Session,
    shop_id: int,
    username: str, 
    password: str, 
    email: str, 
    name: str, 
    slot_duration: int = 30
):
    try:
        shop = db.query(Shop).filter(
            Shop.id == shop_id, 
            Shop.accepting_new_barbers == True
        ).first()
        if not shop:
            raise ValueError("Shop not found or not accepting new barbers")

        user = _build_user(db, username, password, email, "barber")       
        barber = Barber(user_id=user.id, name=name, slot_duration=slot_duration)
        barber.shop = shop
        db.add(barber)
        db.commit()
        db.refresh(barber)
        return barber
    except Exception as e:
        db.rollback()
        raise e