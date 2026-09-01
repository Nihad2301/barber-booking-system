# User model for authentication
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # "client", "barber"
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_code = Column(String, nullable=True)
    verification_code_expiry = Column(DateTime, nullable=True)

    # Relationships (reverse relationships from Client/Barber)
    client = relationship("Client", back_populates="user", uselist=False)
    barber = relationship("Barber", back_populates="user", uselist=False)
