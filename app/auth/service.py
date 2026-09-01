# Auth business logic
from .models import User
from .schemas import LoginResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .security import hash_password, verify_password, generate_token
from datetime import datetime, timedelta
import secrets
import string

def _build_user(db: Session, username: str, password: str, email: str, user_type: str):
    user = db.query(User).filter(
        or_(User.username == username, User.email == email)
    ).first()
    if user:
        raise ValueError("User already exists")

    hashed_password = hash_password(password)
    
    user = User(
        username=username,
        hashed_password=hashed_password,
        email=email,
        user_type=user_type
    )
    db.add(user)
    db.flush()
    return user
   
def login_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("Invalid credential(s)")
    password_verified = verify_password(password, user.hashed_password)
    if not password_verified:
        raise ValueError("Invalid credential(s)")
    token = generate_token(data={"user_id": user.id})
    return LoginResponse(
        access_token=token, 
        token_type="bearer", 
        user=user
    )

def generate_verification_code(db: Session, email: str, length: int = 6, expiry_hours: int = 24) -> str:
    """Generate a random alphanumeric verification code"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")

    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
    user.verification_code = code
    user.verification_code_expiry = expiry
    db.commit()
    return code

def verify_email(db: Session, email: str, code: str):
    """Verify user email with code"""  
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Could not verify email")
    
    if not user.verification_code or not user.verification_code_expiry:
        raise ValueError("Could not verify email")
    
    if user.verification_code != code:
        raise ValueError("Could not verify email")
    
    if user.verification_code_expiry < datetime.utcnow():
        raise ValueError("Could not verify email")
    
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user