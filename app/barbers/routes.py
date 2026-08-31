# Barber endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .schemas import BarberRegister, BarberResponse
from .service import register_barber
from app.database import get_db

router = APIRouter(prefix="/barbers", tags=["barbers"])

@router.post("/", response_model=BarberResponse)
def add_barber(barber: BarberRegister, db: Session = Depends(get_db)):
    return register_barber(
        db=db, 
        shop_id=barber.shop_id, 
        username=barber.username, 
        password=barber.password, 
        email=barber.email, 
        name=barber.name, 
        slot_duration=barber.slot_duration
    )
    
