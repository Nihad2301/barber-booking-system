from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.base import Base

class Barber(Base):
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    is_owner = Column(Boolean, nullable=False, default=False)
    slot_duration = Column(Integer, nullable=False)  # in minutes
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User")
    shop = relationship("Shop", back_populates="barbers")
    bookings = relationship("Booking", back_populates="barber")
    working_hours = relationship("WorkingHours", back_populates="barber")
    services = relationship("Service", secondary="barber_services", back_populates="barbers")
    slots = relationship("Slot", back_populates="barber")

# Join table for Barber-Service many-to-many relationship
class BarberService(Base):
    __tablename__ = "barber_services"

    barber_id = Column(Integer, ForeignKey("barbers.id"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), primary_key=True)
