# Password hashing and JWT utilities
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY

def generate_token(data: dict, expires_in: int = 3600) -> str:
    """Generate a JWT token"""
    payload = data.copy()
    exp = datetime.utcnow() + timedelta(seconds=expires_in)
    payload.update({"exp": exp})
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> dict:
    """Verify a JWT token's signature and expiration"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise Exception("Invalid token")    
