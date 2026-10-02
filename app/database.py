from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.base import Base

print("[DATABASE] Starting database initialization...")

# Import all models to ensure they are loaded before SQLAlchemy resolves relationships
from app.models import Shop, Barber, BarberService, Client, Service, WorkingHours, Slot, Booking

print("[DATABASE] Models imported, creating engine...")
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
print("[DATABASE] Engine created successfully")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("[DATABASE] SessionLocal configured")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
