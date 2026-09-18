# Shop endpoints
from .service import (
    get_available_shops, 
    create_shop, 
    get_shop_by_id, 
    update_shop,
    delete_shop
)
from app.auth.dependencies import get_current_user, require_verified_email
from .schemas import ShopResponse, ShopRequest, ShopUpdateRequest
from app.auth.schemas import MessageResponse, DataResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/shops", tags=["shops"])

@router.get("/", response_model=DataResponse[list[ShopResponse]])
def get_shops(db: Session = Depends(get_db)):
    shops = get_available_shops(db)
    return DataResponse(message="Shops retrieved successfully", data=shops)

@router.post("/", response_model=DataResponse[ShopResponse])
def register_shop(shop: ShopRequest, db: Session = Depends(get_db)):
    shop = create_shop(db, shop.model_dump())
    return DataResponse(message="Shop created successfully", data=shop)

@router.get("/{shop_id}", response_model=DataResponse[ShopResponse])
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = get_shop_by_id(db, shop_id)
    return DataResponse(message="Shop retrieved successfully", data=shop)

@router.put("/{shop_id}", response_model=DataResponse[ShopResponse])
def update_shop(shop_id: int, shop: ShopUpdateRequest, db: Session = Depends(get_db), verified_user: dict = Depends(require_verified_email)):
    user_id = verified_user.get("user_id")
    shop = update_shop(db, shop_id, user_id, shop.model_dump())
    return DataResponse(message="Shop updated successfully", data=shop)

@router.delete("/{shop_id}", response_model=MessageResponse)
def delete_shop(shop_id: int, db: Session = Depends(get_db), verified_user: dict = Depends(require_verified_email)):
    user_id = verified_user.get("user_id")
    result = delete_shop(db, user_id, shop_id)
    return MessageResponse(**result)
    
    