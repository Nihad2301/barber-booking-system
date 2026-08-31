# Auth business logic
from .models import User
from .schemas import LoginResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .security import hash_password, verify_password, generate_token

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
    db.refresh(user)
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