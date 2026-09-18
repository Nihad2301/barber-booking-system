from sqlalchemy.orm import Session, joinedload
from app.barbers.models import Barber
from app.auth.exceptions import NotFoundError, AlreadyExistsError
from app.services.service import _service_to_response
from app.barbers.service import _verify_ownership
from app.services.schemas import ServiceResponse
from app.services.models import Service

from fastapi import APIRouter, Depends
from app.auth.schemas import MessageResponse, DataResponse
from app.database import get_db
from app.auth.dependencies import require_verified_email

router = APIRouter(prefix="/barber-services", tags=["Barber Services"])

def _add_barber_service(
    db: Session,
    shop_id: int,
    user_id: int,
    barber_id: int,
    service_id: int
):
    # Verify that requester is shop owner
    _verify_ownership(user_id, shop_id, db)
    # Implement adding service to barber
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.shop_id == shop_id,
        Service.is_active == True
    ).first()
    if not service:
        raise NotFoundError("Service not found")

    barber = db.query(Barber).filter(Barber.id == barber_id, Barber.shop_id == shop_id).first()
    if not barber:
        raise NotFoundError("Barber not found")

    if service in barber.services:
        raise AlreadyExistsError("Service already assigned to barber")

    barber.services.append(service)
    db.commit()
    db.refresh(barber)
    return {"message": "Service added to barber successfully"}    

def _get_barber_services(db: Session, shop_id: int, barber_id: int):
    barber = db.query(Barber).options(
        joinedload(Barber.services)
    ).filter(
        Barber.id == barber_id,
        Barber.shop_id == shop_id
    ).first()
    if not barber:
        raise NotFoundError("Barber not found")
    services = [service for service in barber.services if service.is_active]
    return [_service_to_response(service) for service in services]

@router.post("/shops/{shop_id}/barbers/{barber_id}/services/{service_id}", response_model=MessageResponse)
def add_barber_service(
    shop_id: int, 
    barber_id: int, 
    service_id: int, 
    db: Session = Depends(get_db), 
    verified_user: dict = Depends(require_verified_email)
):
    user_id = verified_user.get("user_id")
    result = _add_barber_service(db, shop_id, user_id, barber_id, service_id)
    return MessageResponse(**result)

@router.get("/shops/{shop_id}/barbers/{barber_id}", response_model=DataResponse[list[ServiceResponse]])
def get_barber_services(
    shop_id: int, 
    barber_id: int, 
    db: Session = Depends(get_db)
):
    services = _get_barber_services(db, shop_id, barber_id)
    return DataResponse(data=services, message="Barber services retrieved successfully")
