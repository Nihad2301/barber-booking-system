from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    status = Column(String, nullable=False)  # "confirmed", "cancelled_by_client", "cancelled_by_barber", "completed"
    
    # Relationships
    slot = relationship("Slot", back_populates="bookings")
    client = relationship("Client", back_populates="bookings")
    barber = relationship("Barber", back_populates="bookings")
    shop = relationship("Shop", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
