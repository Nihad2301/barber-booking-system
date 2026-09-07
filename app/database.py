from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.base import Base

# Import all models to ensure they are loaded before SQLAlchemy resolves relationships
from app.models import Shop, Barber, BarberService, Client, Service, WorkingHours, Slot, Booking

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
