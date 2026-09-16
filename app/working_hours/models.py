from sqlalchemy import Column, Integer, ForeignKey, Time, String
from sqlalchemy.orm import relationship
from app.base import Base

class WorkingHours(Base):
    __tablename__ = "working_hours"

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    day_of_week = Column(String, nullable=False)  # "Monday", "Tuesday", etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    lunch_break_start = Column(Time, nullable=True)  # Optional lunch break start
    lunch_break_end = Column(Time, nullable=True)  # Optional lunch break end
    
    # Relationships
    barber = relationship("Barber", back_populates="working_hours")
