# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DJANGO_SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()