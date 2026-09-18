# Service business logic
from sqlalchemy.orm import Session
from app.shops.models import Shop
from app.services.models import Service
from app.auth.exceptions import NotFoundError
from app.barbers.service import _verify_ownership

def _service_to_response(service: Service):
    return {
        "id": service.id,
        "name": service.name,
        "price": service.price,
        "is_active": service.is_active
    }

def _add_service(db: Session, user_id: int, shop_id: int, service_data: dict):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    _verify_ownership(user_id, shop_id, db)
    service_data["shop_id"] = shop_id
    service = Service(**service_data)
    db.add(service)
    db.commit()
    db.refresh(service)
    return _service_to_response(service)

def _get_services(db: Session, shop_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    services = db.query(Service).filter(
        Service.shop_id == shop_id,
        Service.is_active == True
    ).all()
    return [_service_to_response(service) for service in services]

def _get_service(db: Session, shop_id: int, service_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.shop_id == shop_id,
        Service.is_active == True
    ).first()
    if not service:
        raise NotFoundError("Service not found")
    
    return _service_to_response(service)      

def _update_service(db: Session, user_id: int, shop_id: int, service_id: int, service_data: dict):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    _verify_ownership(user_id, shop_id, db)
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.shop_id == shop_id,
        Service.is_active == True
    ).first()
    if not service:
        raise NotFoundError("Service not found")
    
    for key, value in service_data.items():
        if value is not None:
            setattr(service, key, value)
    
    db.commit()
    db.refresh(service)
    return _service_to_response(service)

def _delete_service(db: Session, user_id: int, shop_id: int, service_id: int):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise NotFoundError("Shop not found")
    _verify_ownership(user_id, shop_id, db)
    
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.shop_id == shop_id,
        Service.is_active == True
    ).first()
    if not service:
        raise NotFoundError("Service not found")
    
    service.is_active = False
    db.commit()
    return {"message": "Service deleted successfully"}    