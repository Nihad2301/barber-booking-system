from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from apscheduler.schedulers.background import BackgroundScheduler
from app.auth.routes import router as auth_router
from app.barbers.routes import router as barbers_router
from app.shops.routes import router as shops_router
from app.services.routes import router as services_router
from app.barbers.barber_services import router as barber_services_router
from app.working_hours.routes import router as working_hours_router
from app.auth.exceptions import AppException
from app.exception_handlers import custom_exception_handler, validation_exception_handler
from app.database import get_db
from app.slots.service import generate_next_day_slots

app = FastAPI(title="Barber Booking System")

# Register exception handlers
app.add_exception_handler(AppException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth_router)
app.include_router(barbers_router)
app.include_router(shops_router)
app.include_router(services_router)
app.include_router(barber_services_router)
app.include_router(working_hours_router)

# Setup APScheduler for nightly slot generation
scheduler = BackgroundScheduler()

def nightly_slot_generation():
    """Nightly job to generate slots for (today+14)"""
    db = next(get_db())
    try:
        generate_next_day_slots(db)
    finally:
        db.close()

scheduler.add_job(
    nightly_slot_generation,
    'cron',
    hour=23,
    minute=59,
    id='nightly_slot_generation'
)

@app.on_event("startup")
def startup_event():
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "Barber Booking System API"}
