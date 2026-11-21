from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "nexora-ai-api"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/nexora_ai"
    TEST_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/nexora_ai_test"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    RESUME_UPLOAD_MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB default
    RESUME_UPLOAD_STAGING_DIR: str = "storage/staging/resumes"
    RESUME_STORAGE_DIR: str = "storage/resumes"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 8.0

    @property
    def cors_origins(self) -> List[str]:
        origins = [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), ".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
