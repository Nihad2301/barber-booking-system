import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()

# Debug logging
print(f"[CONFIG] DATABASE_URL loaded: {bool(settings.DATABASE_URL)}")
print(f"[CONFIG] SECRET_KEY loaded: {bool(settings.SECRET_KEY)}")
print(f"[CONFIG] PORT from env: {os.getenv('PORT', 'NOT SET')}")
