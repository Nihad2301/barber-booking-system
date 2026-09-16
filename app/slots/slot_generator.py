# Slot generation logic - pure functions for generating time slots
from datetime import datetime, time, timedelta
from typing import List, Tuple, Optional

def generate_slots_for_day(
    day_start: datetime,
    day_end: datetime,
    lunch_break_start: Optional[time],
    lunch_break_end: Optional[time],
    slot_duration: int
) -> List[Tuple[datetime, datetime]]:
    """
    Pure function to generate slot time tuples for a single day.
    No database access - easily unit-testable.
    
    Args:
        day_start: Start of the workday (datetime with date component)
        day_end: End of the workday (datetime with date component)
        lunch_break_start: Start of lunch break (time only) or None
        lunch_break_end: End of lunch break (time only) or None
        slot_duration: Duration of each slot in minutes
    
    Returns:
        List of (start_time, end_time) tuples for each slot
    """
    slots = []
    slot_start = day_start
    
    while True:
        # Recalculate slot_end fresh every iteration
        slot_end = slot_start + timedelta(minutes=slot_duration)
        
        # Hard boundary: stop if slot_end exceeds day_end
        if slot_end > day_end:
            break
        
        # Handle lunch break: check for any overlap
        if lunch_break_start and lunch_break_end:
            # Convert lunch break times to datetime for comparison
            lunch_start_dt = datetime.combine(slot_start.date(), lunch_break_start)
            lunch_end_dt = datetime.combine(slot_start.date(), lunch_break_end)
            
            if slot_start <= lunch_end_dt and slot_end >= lunch_start_dt:
                # Slot overlaps with lunch break - skip to after lunch
                slot_start = datetime.combine(slot_start.date(), lunch_break_end)
                continue
        
        slots.append((slot_start, slot_end))
        slot_start = slot_end
    
    return slots
