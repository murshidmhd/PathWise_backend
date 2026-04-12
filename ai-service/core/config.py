# core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "PathWise AI Service"
    DEBUG: bool = False

    # ── Groq ─────────────────────────────────────────────
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Auth (shared with Django) ─────────────────────────
    DJANGO_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # ── ChromaDB ─────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    GEMINI_API_KEY: str

    # ── CORS ─────────────────────────────────────────────
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
