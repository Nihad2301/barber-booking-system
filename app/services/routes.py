# Service endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.service import (
    _add_service, 
    _get_services, 
    _get_service, 
    _update_service,
    _delete_service
)
from app.auth.dependencies import require_verified_email
from app.auth.schemas import MessageResponse, DataResponse
from .schemas import ServiceRequest, ServiceResponse, ServiceUpdateRequest

router = APIRouter(prefix="/services", tags=["services"])

@router.post("/{shop_id}", response_model=DataResponse[ServiceResponse])
def add_service(
    shop_id: int,
    service_data: ServiceRequest,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    service = _add_service(db, user_id, shop_id, service_data.model_dump())
    return DataResponse(data=service, message="Service created successfully")

@router.get("/{shop_id}", response_model=DataResponse[list[ServiceResponse]])
def get_services(
    shop_id: int,
    db: Session = Depends(get_db)
):
    services = _get_services(db, shop_id)
    return DataResponse(data=services, message="Services retrieved successfully")

@router.get("/{shop_id}/{service_id}", response_model=DataResponse[ServiceResponse])
def get_service(
    shop_id: int,
    service_id: int,
    db: Session = Depends(get_db)
):
    service = _get_service(db, shop_id, service_id)
    return DataResponse(data=service, message="Service retrieved successfully")

@router.put("/{shop_id}/{service_id}", response_model=DataResponse[ServiceResponse])
def update_service(
    shop_id: int,
    service_id: int,
    service_data: ServiceUpdateRequest,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    service = _update_service(db, user_id, shop_id, service_id, service_data.model_dump())
    return DataResponse(data=service, message="Service updated successfully")

@router.delete("/{shop_id}/{service_id}", response_model=MessageResponse)
def delete_service(
    shop_id: int,
    service_id: int,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    result = _delete_service(db, user_id, shop_id, service_id)
    return MessageResponse(**result)
