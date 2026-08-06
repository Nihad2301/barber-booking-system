from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    barbers = relationship("Barber", back_populates="shop")
    services = relationship("Service", back_populates="shop")
    slots = relationship("Slot", back_populates="shop")
    bookings = relationship("Booking", back_populates="shop")
