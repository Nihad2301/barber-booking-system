# Shop endpoints
from .service import get_available_shops
from .schemas import ShopResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/shops", tags=["shops"])

@router.get("/", response_model=list[ShopResponse])
def get_shops(db: Session = Depends(get_db)):
    return get_available_shops(db)