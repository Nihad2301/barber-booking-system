# Slot endpoints
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.slots.models import Slot
from app.slots.schemas import SlotResponse
from app.auth.schemas import DataResponse
from datetime import datetime, date

router = APIRouter(prefix="/slots", tags=["Slots"])

@router.get("", response_model=DataResponse[list[SlotResponse]])
def list_slots(
    barber_id: int = Query(..., gt=0),
    date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    List available slots for a barber on a specific date.
    """
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    slots = db.query(Slot).filter(
        Slot.barber_id == barber_id,
        Slot.start_time >= start_of_day,
        Slot.start_time <= end_of_day,
        Slot.status == 'open'
    ).order_by(Slot.start_time).all()
    
    return DataResponse(
        data=[SlotResponse.model_validate(slot) for slot in slots],
        message="Slots retrieved successfully"
    )
