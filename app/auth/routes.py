# Authentication endpoints

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .email import send_verification_email
from app.database import get_db
from .service import (
    login_user, 
    generate_verification_code, 
    verify_email
)
from .schemas import (
    LoginRequest, 
    LoginResponse, 
    MessageResponse, 
    DataResponse, 
    SendEmailRequest,
    VerificationRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=DataResponse[LoginResponse])
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    logged_in_user = login_user(
        db=db, 
        username=login_request.username, 
        password=login_request.password
    )
    return DataResponse(message="Login successful", data=logged_in_user)

@router.post("/send-verification-code", response_model=MessageResponse)
def send_verification_code(email_request: SendEmailRequest, db: Session = Depends(get_db)):
    verification_code = generate_verification_code(db=db, email=email_request.email)
    send_verification_email(email=email_request.email, code=verification_code)
    return MessageResponse(message="Verification code sent successfully")

@router.post("/email-verification", response_model=MessageResponse)
def email_verification(verification_request: VerificationRequest, db: Session = Depends(get_db)):
    verify_email(db=db, email=verification_request.email, code=verification_request.code)
    return MessageResponse(message="Email verified successfully")
