# Barber endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_verified_email
from app.auth.schemas import MessageResponse, DataResponse
from .schemas import BarberRegister, BarberResponse, BarberSelfUpdate, BarberOwnerUpdate
from .service import (
    register_barber, 
    show_barbers, 
    show_barber, 
    update_self_barber, 
    update_owner_barber,
    delete_self_barber,
    delete_owner_barber
)
from app.database import get_db

router = APIRouter(prefix="/barbers", tags=["barbers"])

@router.post("/{shop_id}", response_model=DataResponse[BarberResponse])
def add_barber(
    shop_id: int,
    barber: BarberRegister, 
    db: Session = Depends(get_db), 
    verified_barber_owner: dict = Depends(require_verified_email)
):
    barber_owner_id = verified_barber_owner["user_id"]
    new_barber = register_barber(
        db=db, 
        barber_owner_id=barber_owner_id,
        shop_id=shop_id, 
        username=barber.username, 
        password=barber.password, 
        email=barber.email, 
        name=barber.name, 
        slot_duration=barber.slot_duration
    )
    
    return DataResponse(data=new_barber, message="Barber registered successfully")

@router.get("/{shop_id}", response_model=DataResponse[list[BarberResponse]])
def get_barbers(shop_id: int, db: Session = Depends(get_db)):
    barbers = show_barbers(db, shop_id)
    return DataResponse(data=barbers, message="Barbers retrieved successfully")    

@router.get("/{shop_id}/{barber_id}", response_model=DataResponse[BarberResponse])
def get_barber(shop_id: int, barber_id: int, db: Session = Depends(get_db)):
    barber = show_barber(db, barber_id, shop_id)
    return DataResponse(data=barber, message="Barber retrieved successfully")    

@router.put("/{shop_id}/{barber_id}", response_model=DataResponse[BarberResponse])
def self_update_barber(
    shop_id: int, 
    barber_id: int, 
    barber_data: BarberSelfUpdate, 
    db: Session = Depends(get_db), 
    verified_barber: dict = Depends(require_verified_email)
):
    user_id = verified_barber["user_id"]
    barber = update_self_barber(db, user_id, barber_id, shop_id, barber_data.model_dump())
    return DataResponse(data=barber, message="Barber updated successfully")    

@router.put("/{shop_id}/{barber_id}/owner", response_model=DataResponse[BarberResponse])
def owner_update_barber(
    shop_id: int, 
    barber_id: int, 
    barber_data: BarberOwnerUpdate, 
    db: Session = Depends(get_db), 
    verified_user: dict = Depends(require_verified_email)
):
    user_id = verified_user["user_id"]
    barber = update_owner_barber(db, user_id, barber_id, shop_id, barber_data.model_dump())
    return DataResponse(data=barber, message="Barber updated successfully")    

@router.delete("/{shop_id}/{barber_id}", response_model=MessageResponse)
def self_delete_barber(shop_id: int, barber_id: int, db: Session = Depends(get_db), verified_user: dict = Depends(require_verified_email)):
    user_id = verified_user["user_id"]
    result = delete_self_barber(db, user_id, barber_id, shop_id)
    return MessageResponse(**result)

@router.delete("/{shop_id}/{barber_id}/owner", response_model=MessageResponse)
def owner_delete_barber(shop_id: int, barber_id: int, db: Session = Depends(get_db), verified_user: dict = Depends(require_verified_email)):
    user_id = verified_user["user_id"]
    result = delete_owner_barber(db, user_id, barber_id, shop_id)
    return MessageResponse(**result)
    
