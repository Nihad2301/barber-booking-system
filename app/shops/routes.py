# Shop endpoints
from .service import get_available_shops, create_shop
from .schemas import ShopResponse, ShopRequest
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
import sys

router = APIRouter(prefix="/shops", tags=["shops"])

@router.get("/", response_model=list[ShopResponse])
def get_shops(db: Session = Depends(get_db)):
    return get_available_shops(db)

@router.post("/", response_model=ShopResponse)
def register_shop(shop: ShopRequest, db: Session = Depends(get_db)):
    shop = create_shop(db, shop.model_dump())
    return shop    