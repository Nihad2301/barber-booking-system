# FastAPI dependencies for protected routes
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.security import verify_token
from app.auth.exceptions import EmailNotVerifiedError 

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate JWT token from Authorization header"""
    token = credentials.credentials
    return verify_token(token)

def require_verified_email(user: dict = Depends(get_current_user)):
    """Require that the user's email is verified"""
    if not user.get("is_verified"):
        raise EmailNotVerifiedError("Email not verified")
    return user
