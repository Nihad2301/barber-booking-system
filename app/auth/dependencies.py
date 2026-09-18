# FastAPI dependencies for protected routes
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.security import verify_token
from app.auth.exceptions import EmailNotVerifiedError
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.models import User

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate JWT token from Authorization header"""
    token = credentials.credentials
    return verify_token(token)

def require_verified_email(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Require that the user's email is verified"""
    user_id = user.get("user_id")
    
    # Check database for current verification status
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.is_verified:
        raise EmailNotVerifiedError("Email not verified")
    
    return user
