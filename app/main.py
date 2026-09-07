from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.auth.routes import router as auth_router
from app.barbers.routes import router as barbers_router
from app.shops.routes import router as shops_router
from app.auth.exceptions import AppException
from app.exception_handlers import custom_exception_handler, validation_exception_handler

app = FastAPI(title="Barber Booking System")

# Register exception handlers
app.add_exception_handler(AppException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth_router)
app.include_router(barbers_router)
app.include_router(shops_router)

@app.get("/")
def read_root():
    return {"message": "Barber Booking System API"}
