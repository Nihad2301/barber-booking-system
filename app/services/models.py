from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.base import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    shop = relationship("Shop", back_populates="services")
    bookings = relationship("Booking", back_populates="service")
    barbers = relationship("Barber", secondary="barber_services", back_populates="services")
