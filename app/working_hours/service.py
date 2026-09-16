# Working hours business logic
from sqlalchemy.orm import Session
from app.working_hours.models import WorkingHours
from app.barbers.models import Barber
from app.auth.exceptions import NotFoundError, AlreadyExistsError
from app.slots.service import generate_14_day_window

def _working_hours_to_response(working_hours: WorkingHours):
    return {
        "id": working_hours.id,
        "barber_id": working_hours.barber_id,
        "day_of_week": working_hours.day_of_week,
        "start_time": working_hours.start_time,
        "end_time": working_hours.end_time,
        "lunch_break_start": working_hours.lunch_break_start,
        "lunch_break_end": working_hours.lunch_break_end
    }

def add_working_hours(db: Session, barber_id: int, user_id: int, working_hours_data: dict):
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    # Verify barber is updating their own schedule
    if barber.user_id != user_id:
        raise NotFoundError("You can only update your own working hours")
    
    # Check if working hours for this day already exist
    existing = db.query(WorkingHours).filter(
        WorkingHours.barber_id == barber_id,
        WorkingHours.day_of_week == working_hours_data["day_of_week"]
    ).first()
    if existing:
        raise AlreadyExistsError("Working hours for this day already exist")
    
    working_hours = WorkingHours(barber_id=barber_id, **working_hours_data)
    db.add(working_hours)
    db.commit()
    db.refresh(working_hours)
    
    # Trigger slot generation for 14-day window
    generate_14_day_window(db, barber_id)
    
    return _working_hours_to_response(working_hours)

def get_working_hours(db: Session, barber_id: int):
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    working_hours = db.query(WorkingHours).filter(WorkingHours.barber_id == barber_id).all()
    return [_working_hours_to_response(wh) for wh in working_hours]

def update_working_hours(db: Session, barber_id: int, user_id: int, working_hours_id: int, working_hours_data: dict):
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    # Verify barber is updating their own schedule
    if barber.user_id != user_id:
        raise NotFoundError("You can only update your own working hours")
    
    working_hours = db.query(WorkingHours).filter(
        WorkingHours.id == working_hours_id,
        WorkingHours.barber_id == barber_id
    ).first()
    if not working_hours:
        raise NotFoundError("Working hours not found")
    
    for key, value in working_hours_data.items():
        if value is not None:
            setattr(working_hours, key, value)
    
    db.commit()
    db.refresh(working_hours)
    
    # Trigger slot generation for 14-day window
    generate_14_day_window(db, barber_id)
    
    return _working_hours_to_response(working_hours)

def delete_working_hours(db: Session, barber_id: int, user_id: int, working_hours_id: int):
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    # Verify barber is updating their own schedule
    if barber.user_id != user_id:
        raise NotFoundError("You can only delete your own working hours")
    
    working_hours = db.query(WorkingHours).filter(
        WorkingHours.id == working_hours_id,
        WorkingHours.barber_id == barber_id
    ).first()
    if not working_hours:
        raise NotFoundError("Working hours not found")
    
    db.delete(working_hours)
    db.commit()
    
    # Trigger slot generation for 14-day window
    generate_14_day_window(db, barber_id)
    
    return {"message": "Working hours deleted successfully"}
