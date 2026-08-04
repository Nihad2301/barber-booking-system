from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    # Relationships
    shop = relationship("Shop", back_populates="services")
    barbers = relationship("Barber", secondary="barber_services", back_populates="services")
    bookings = relationship("Booking", back_populates="service")
