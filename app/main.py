from fastapi import FastAPI
from app.database import engine
from app.models import Base

app = FastAPI(title="Barber Booking System")

# Create tables (for development - in production use Alembic migrations)
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Barber Booking System API"}
