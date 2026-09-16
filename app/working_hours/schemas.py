# Working hours Pydantic schemas
from pydantic import BaseModel, field_validator
from datetime import time
from typing import Optional

class WorkingHoursRequest(BaseModel):
    day_of_week: str  # "Monday", "Tuesday", etc.
    start_time: time
    end_time: time
    lunch_break_start: Optional[time] = None
    lunch_break_end: Optional[time] = None
    
    @field_validator('day_of_week')
    def validate_day(cls, v):
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if v not in valid_days:
            raise ValueError(f"Day must be one of: {', '.join(valid_days)}")
        return v
    
    @field_validator('end_time')
    def validate_times(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("end_time must be after start_time")
        return v

class WorkingHoursResponse(BaseModel):
    id: int
    barber_id: int
    day_of_week: str
    start_time: time
    end_time: time
    lunch_break_start: Optional[time] = None
    lunch_break_end: Optional[time] = None
    
    class Config:
        from_attributes = True
