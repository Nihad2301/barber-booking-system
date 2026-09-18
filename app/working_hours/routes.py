# Working hours endpoints
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.working_hours.service import (
    add_working_hours,
    get_working_hours,
    update_working_hours,
    delete_working_hours
)
from app.auth.dependencies import require_verified_email
from app.auth.schemas import MessageResponse, DataResponse
from .schemas import WorkingHoursRequest, WorkingHoursUpdateRequest, WorkingHoursResponse

def generate_slots_background(barber_id: int):
    """Background task wrapper that creates its own database session"""
    from app.database import SessionLocal
    from app.slots.service import generate_14_day_window

    db = SessionLocal()
    try:
        generate_14_day_window(db, barber_id)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in background slot generation: {e}")
    finally:
        db.close()

router = APIRouter(prefix="/working-hours", tags=["working-hours"])

@router.post("/{barber_id}", response_model=DataResponse[WorkingHoursResponse])
def create_working_hours(
    barber_id: int,
    working_hours_data: WorkingHoursRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    working_hours = add_working_hours(db, barber_id, user_id, working_hours_data.model_dump())
    # Trigger slot generation in background
    background_tasks.add_task(generate_slots_background, barber_id)
    return DataResponse(data=working_hours, message="Working hours created successfully")

@router.get("/{barber_id}", response_model=DataResponse[list[WorkingHoursResponse]])
def get_barber_working_hours(barber_id: int, db: Session = Depends(get_db)):
    working_hours = get_working_hours(db, barber_id)
    return DataResponse(data=working_hours, message="Working hours retrieved successfully")

@router.put("/{barber_id}/{working_hours_id}", response_model=DataResponse[WorkingHoursResponse])
def update_barber_working_hours(
    barber_id: int,
    working_hours_id: int,
    working_hours_data: WorkingHoursUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    working_hours = update_working_hours(db, barber_id, user_id, working_hours_id, working_hours_data.model_dump())
    # Trigger slot generation in background
    background_tasks.add_task(generate_slots_background, barber_id)
    return DataResponse(data=working_hours, message="Working hours updated successfully")

@router.delete("/{barber_id}/{working_hours_id}", response_model=MessageResponse)
def delete_barber_working_hours(
    barber_id: int,
    working_hours_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    result = delete_working_hours(db, barber_id, user_id, working_hours_id)
    # Trigger slot generation in background
    background_tasks.add_task(generate_slots_background, barber_id)
    return MessageResponse(**result)
