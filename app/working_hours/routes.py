# Working hours endpoints
from fastapi import APIRouter, Depends
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
from .schemas import WorkingHoursRequest, WorkingHoursResponse

router = APIRouter(prefix="/working-hours", tags=["working-hours"])

@router.post("/{barber_id}", response_model=DataResponse[WorkingHoursResponse])
def create_working_hours(
    barber_id: int,
    working_hours_data: WorkingHoursRequest,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    working_hours = add_working_hours(db, barber_id, user_id, working_hours_data.model_dump())
    return DataResponse(data=working_hours, message="Working hours created successfully")

@router.get("/{barber_id}", response_model=DataResponse[list[WorkingHoursResponse]])
def get_barber_working_hours(barber_id: int, db: Session = Depends(get_db)):
    working_hours = get_working_hours(db, barber_id)
    return DataResponse(data=working_hours, message="Working hours retrieved successfully")

@router.put("/{barber_id}/{working_hours_id}", response_model=DataResponse[WorkingHoursResponse])
def update_barber_working_hours(
    barber_id: int,
    working_hours_id: int,
    working_hours_data: WorkingHoursRequest,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    working_hours = update_working_hours(db, barber_id, user_id, working_hours_id, working_hours_data.model_dump())
    return DataResponse(data=working_hours, message="Working hours updated successfully")

@router.delete("/{barber_id}/{working_hours_id}", response_model=MessageResponse)
def delete_barber_working_hours(
    barber_id: int,
    working_hours_id: int,
    current_user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    result = delete_working_hours(db, barber_id, user_id, working_hours_id)
    return MessageResponse(**result)
