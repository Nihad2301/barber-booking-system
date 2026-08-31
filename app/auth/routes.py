# Authentication endpoints

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .service import login_user
from app.database import get_db
from .schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    logged_in_user = login_user(
        db=db, 
        username=login_request.username, 
        password=login_request.password
    )
    return logged_in_user
    
