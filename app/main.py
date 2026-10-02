import sys
import os

sys.stdout.flush()
sys.stderr.flush()

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from apscheduler.schedulers.background import BackgroundScheduler
from app.auth.routes import router as auth_router
from app.barbers.routes import router as barbers_router
from app.shops.routes import router as shops_router
from app.services.routes import router as services_router
from app.barbers.barber_services import router as barber_services_router
from app.working_hours.routes import router as working_hours_router
from app.bookings.routes import router as bookings_router
from app.slots.routes import router as slots_router
from app.clients.routes import router as clients_router
from app.auth.exceptions import AppException
from app.exception_handlers import custom_exception_handler, validation_exception_handler
from app.database import get_db
from app.slots.service import generate_next_day_slots

print("[MAIN] Starting FastAPI app initialization...")
print(f"[MAIN] Python version: {sys.version}")
print(f"[MAIN] Working directory: {os.getcwd()}")
print(f"[MAIN] PORT env var: {os.getenv('PORT', 'NOT SET')}", flush=True)

app = FastAPI(title="Barber Booking System")
print("[MAIN] FastAPI app created")

# Register exception handlers
app.add_exception_handler(AppException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
print("[MAIN] Exception handlers registered")

app.include_router(auth_router)
app.include_router(barbers_router)
app.include_router(shops_router)
app.include_router(services_router)
app.include_router(barber_services_router)
app.include_router(working_hours_router)
app.include_router(bookings_router)
app.include_router(slots_router)
app.include_router(clients_router)
print("[MAIN] All routers registered")

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
    print("[STARTUP] Startup event triggered", flush=True)
    # TEMPORARILY DISABLED: scheduler startup is suspected of making the app
    # unresponsive after startup. Re-enable once the root cause is diagnosed.
    try:
        print("[STARTUP] Starting scheduler...", flush=True)
        scheduler.start()
        print("[STARTUP] Scheduler started successfully", flush=True)
    except Exception as e:
        print(f"[STARTUP] ERROR starting scheduler: {e}", flush=True)
        import traceback
        traceback.print_exc()
    print("[STARTUP] Startup event completed", flush=True)

@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()

print("[MAIN] Defining root route", flush=True)

@app.get("/")
def read_root():
    return {"message": "Barber Booking System API"}

@app.get("/health")
def health():
    print("[HEALTH] Health endpoint called", flush=True)
    return {"status": "ok"}
