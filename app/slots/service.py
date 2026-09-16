# Slot business logic
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Tuple
from app.slots.models import Slot
from app.working_hours.models import WorkingHours
from app.slots.slot_generator import generate_slots_for_day
from app.barbers.models import Barber
from app.auth.exceptions import NotFoundError

def persist_slots(
    db: Session,
    slot_tuples: List[Tuple[datetime, datetime]],
    barber_id: int,
    shop_id: int
):
    """
    Persist generated slots to database.
    Single commit after all slots are added.
    """
    try:
        for slot_start, slot_end in slot_tuples:
            slot = Slot(
                barber_id=barber_id,
                shop_id=shop_id,
                start_time=slot_start,
                end_time=slot_end,
                status="open"  # Python-side default
            )
            db.add(slot)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def generate_slots_for_barber(db: Session, barber_id: int, start_date: datetime, end_date: datetime):
    """
    Generate slots for a barber across a date range.
    For each day in range, look up WorkingHours and generate slots.
    """
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise NotFoundError("Barber not found")
    
    shop_id = barber.shop_id
    slot_duration = barber.slot_duration
    
    current_date = start_date
    while current_date <= end_date:
        # Get weekday name
        weekday = current_date.strftime("%A")
        
        # Look up WorkingHours for this barber and weekday
        working_hours = db.query(WorkingHours).filter(
            WorkingHours.barber_id == barber_id,
            WorkingHours.day_of_week == weekday
        ).first()
        
        if working_hours:
            # Convert time to datetime for this specific date
            day_start = datetime.combine(current_date, working_hours.start_time)
            day_end = datetime.combine(current_date, working_hours.end_time)
            
            # Generate slots
            slot_tuples = generate_slots_for_day(
                day_start=day_start,
                day_end=day_end,
                lunch_break_start=working_hours.lunch_break_start,
                lunch_break_end=working_hours.lunch_break_end,
                slot_duration=slot_duration
            )
            
            # Persist slots
            persist_slots(db, slot_tuples, barber_id, shop_id)
        
        current_date += timedelta(days=1)

def generate_14_day_window(db: Session, barber_id: int):
    """
    Generate slots for the 14-day window starting from today.
    Used when WorkingHours is created/updated.
    """
    today = datetime.now().date()
    start_date = datetime.combine(today, datetime.min.time())
    end_date = start_date + timedelta(days=13)  # 14 days total
    
    generate_slots_for_barber(db, barber_id, start_date, end_date)

def generate_next_day_slots(db: Session):
    """
    Nightly job: generate slots for (today+14) for all barbers.
    Each barber gets their own commit/rollback.
    """
    today = datetime.now().date()
    target_date = today + timedelta(days=14)
    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = start_date  # Only one day
    
    barbers = db.query(Barber).filter(Barber.is_active == True).all()
    
    for barber in barbers:
        try:
            generate_slots_for_barber(db, barber.id, start_date, end_date)
        except Exception as e:
            # One barber's failure shouldn't block others
            print(f"Failed to generate slots for barber {barber.id}: {e}")
            continue
