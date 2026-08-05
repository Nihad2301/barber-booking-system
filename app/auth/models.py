# User model for authentication
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # "client", "barber"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=True)

    # Relationships
    client = relationship("Client", back_populates="user")
    barber = relationship("Barber", back_populates="user")
